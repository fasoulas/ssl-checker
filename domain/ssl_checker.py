import ssl
import socket
from datetime import datetime
from typing import Any, Dict, List

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
    