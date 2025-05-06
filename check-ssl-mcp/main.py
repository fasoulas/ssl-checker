import argparse
import json
import os

from dotenv import load_dotenv
from fastapi import FastAPI,Depends, HTTPException, status
from fastapi_mcp import FastApiMCP, AuthConfig
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from pydantic import BaseModel, AnyHttpUrl
from typing import List
import asyncio
import domain.ssl_checker as ssl_checker


MCP_SERVER_TOKEN=""

security = HTTPBearer()
load_dotenv()

if os.getenv("MCP_SERVER_TOKEN") is None: 
    exit("MCP_SERVER_TOKEN variable is not set. Please set it as environment variable.")
else:
    MCP_SERVER_TOKEN = os.getenv("MCP_SERVER_TOKEN")


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    print(token)
    if token !=  MCP_SERVER_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
        )

app = FastAPI()
mcp = FastApiMCP(
    app,
    name="MCP Server for SSL certificate checker tool",
    description="Tool to check SSL certificates and return whether they are valid or when they expire",
    auth_config=AuthConfig(
        dependencies=[Depends(verify_token)],
    ),
)
mcp.mount()

class URLList(BaseModel):
    urls: List[AnyHttpUrl]

@app.post("/check-ssl",dependencies=[Depends(verify_token)],operation_id="check_ssl_certificate")
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
        cert_info = await asyncio.to_thread(ssl_checker.get_ssl_cert_details, hostname, port)

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