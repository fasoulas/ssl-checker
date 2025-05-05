import argparse
import json
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP

from pydantic import BaseModel, AnyHttpUrl
import ssl
import socket
from datetime import datetime
from typing import List, Dict, Any
import asyncio

app = FastAPI()
mcp = FastApiMCP(
    app,
    name="MCP Server for SSL certificate checker tool",
    description="Tool to check SSL certificates and return whether they are valid or when they expire",
)
mcp.mount()

class URLList(BaseModel):
    urls: List[AnyHttpUrl]

def parse_cn(cert_part: List) -> str:
    for tup in cert_part:
        for key, value in tup:
            if key == 'commonName':
                return value
    return "N/A"

def get_ssl_cert_details(hostname: str, port: int = 443) -> Dict[str, Any]:
    try:
        context = ssl.create_default_context()
        with socket.create_connection((hostname, port), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                if not cert:
                    raise ValueError("No certificate received")

                not_after = datetime.strptime(cert['notAfter'], "%b %d %H:%M:%S %Y %Z")
                now = datetime.utcnow()
                delta = (not_after - now).days

                issuer_cn = parse_cn(cert.get('issuer', []))
                subject_cn = parse_cn(cert.get('subject', []))

                if delta >= 0:
                    status = "valid"
                    field = {"expires_in": delta}
                else:
                    status = "expired"
                    field = {"expired": -delta}

                return {
                    "status": status,
                    **field,
                    "issuer": issuer_cn,
                    "subject": subject_cn
                }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error: {str(e)}",
            "issuer": None,
            "subject": None
        }

@app.post("/check-ssl",operation_id="check_ssl_certificate")
async def check_ssl_certificates(data: URLList):
    result = {
        "valid": [],
        "expired": [],
        "errors": [],
        "skipped": []
    }

    async def check_one(url_obj: AnyHttpUrl):
        url_str = str(url_obj)

        if url_obj.scheme != "https":
            result["skipped"].append({"url": url_str, "reason": "Non-HTTPS URL"})
            return

        hostname = url_obj.host
        port = url_obj.port or 443
        cert_info = await asyncio.to_thread(get_ssl_cert_details, hostname, port)

        entry = {
            "url": url_str,
            "issuer": cert_info.get("issuer"),
            "subject": cert_info.get("subject")
        }

        if cert_info["status"] == "valid":
            entry["expires_in"] = cert_info["expires_in"]
            result["valid"].append(entry)
        elif cert_info["status"] == "expired":
            entry["expired"] = cert_info["expired"]
            result["expired"].append(entry)
        else:
            entry["message"] = cert_info["message"]
            result["errors"].append(entry)

    tasks = [check_one(url) for url in data.urls]
    await asyncio.gather(*tasks)

    return result


def run_cli_mode():
    parser = argparse.ArgumentParser(description="Check SSL certificates for a list of URLs.")
    parser.add_argument("urls", nargs="+", help="List of HTTPS URLs to check (e.g. https://example.com)")
    args = parser.parse_args()

    import asyncio
    from pydantic import HttpUrl, ValidationError

    class DummyInput(BaseModel):
        urls: List[AnyHttpUrl]

    try:
        # Validate URLs
        input_data = DummyInput(urls=args.urls)
        result = asyncio.run(check_ssl_certificates(input_data))
        print(json.dumps(result, indent=2))
    except ValidationError as ve:
        print("Invalid URL(s) provided:")
        print(ve)

mcp.setup_server()
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        run_cli_mode()
    else:
        import uvicorn
        uvicorn.run("ssl_checker:app", host="0.0.0.0", port=8000, reload=True)