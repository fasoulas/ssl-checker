
import os
import sys
from typing import Any, Dict
from google.adk.agents import Agent

# # Need to load modules from root codebase diorectory higher than the agents folder
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
print(f"Parent directory: {parent_dir}")
sys.path.insert(0, parent_dir)
from domain import ssl_checker

def get_ssl_details(hostname: str, port: int = 443) -> Dict[str, Any]:
    """Returns the details of an SLL certificate.

    Args:
       hostname (str): The hostname of a host whose SSL certificate you want to check.
       port (int): The port number of the host. Default is 443.

    Returns:
        dict: status and result or error msg.
    """
    return ssl_checker.get_ssl_cert_details(hostname, port)

root_agent = Agent(
    name="weather_time_agent",
    model="gemini-2.0-flash",
    description=(
        "Agent to check the validity of SSL certificates."
    ),
    instruction=(
        "You are a helpful agent who can answer user questions about the state and validity of SSL certificates. "
    ),
    tools=[get_ssl_details]
)