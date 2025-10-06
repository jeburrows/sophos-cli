"""Sophos API Client for Partner and Endpoint APIs"""

import os
import requests
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class SophosAPIClient:
    """Client for interacting with Sophos Partner and Endpoint APIs"""

    AUTH_URL = "https://id.sophos.com/api/v2/oauth2/token"
    PARTNER_API_BASE = "https://api.central.sophos.com"

    def __init__(self):
        """Initialize the API client with credentials from environment"""
        self.client_id = os.getenv("SOPHOS_CLIENT_ID")
        self.client_secret = os.getenv("SOPHOS_CLIENT_SECRET")

        if not self.client_id or not self.client_secret:
            raise ValueError(
                "Missing API credentials. Please set SOPHOS_CLIENT_ID and "
                "SOPHOS_CLIENT_SECRET in your .env file"
            )

        self.access_token: Optional[str] = None
        self.partner_id: Optional[str] = None

    def authenticate(self) -> str:
        """
        Authenticate with Sophos and get an access token

        Returns:
            str: The access token
        """
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "token"
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        response = requests.post(self.AUTH_URL, data=data, headers=headers)
        response.raise_for_status()

        token_data = response.json()
        self.access_token = token_data["access_token"]

        return self.access_token

    def get_whoami(self) -> Dict:
        """
        Get information about the authenticated principal

        Returns:
            dict: Information including partner ID and API host
        """
        if not self.access_token:
            self.authenticate()

        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        response = requests.get(
            f"{self.PARTNER_API_BASE}/whoami/v1",
            headers=headers
        )
        response.raise_for_status()

        whoami_data = response.json()

        # Store partner ID if this is a partner account
        if whoami_data.get("idType") == "partner":
            self.partner_id = whoami_data.get("id")

        return whoami_data

    def get_tenants(self) -> List[Dict]:
        """
        Get all tenants under the partner account

        Returns:
            list: List of tenant dictionaries
        """
        if not self.access_token:
            self.authenticate()

        if not self.partner_id:
            whoami = self.get_whoami()
            if whoami.get("idType") != "partner":
                raise ValueError("This API client requires a partner account")

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-Partner-ID": self.partner_id
        }

        all_tenants = []
        page = 1

        while True:
            params = {"page": page, "pageSize": 100}

            response = requests.get(
                f"{self.PARTNER_API_BASE}/partner/v1/tenants",
                headers=headers,
                params=params
            )
            response.raise_for_status()

            data = response.json()
            tenants = data.get("items", [])

            if not tenants:
                break

            all_tenants.extend(tenants)

            # Check if there are more pages
            pages = data.get("pages", {})
            if page >= pages.get("total", 1):
                break

            page += 1

        # Sort tenants by name
        all_tenants.sort(key=lambda x: x.get("name", "").lower())

        return all_tenants

    def get_endpoints_for_tenant(self, tenant_id: str, api_host: str) -> List[Dict]:
        """
        Get all endpoints for a specific tenant

        Args:
            tenant_id: The tenant ID
            api_host: The API host URL for the tenant's region

        Returns:
            list: List of endpoint dictionaries
        """
        if not self.access_token:
            self.authenticate()

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-Tenant-ID": tenant_id
        }

        all_endpoints = []
        page_from_key = None

        while True:
            params = {"pageSize": 100}
            if page_from_key:
                params["pageFromKey"] = page_from_key

            response = requests.get(
                f"{api_host}/endpoint/v1/endpoints",
                headers=headers,
                params=params
            )
            response.raise_for_status()

            data = response.json()
            endpoints = data.get("items", [])

            if not endpoints:
                break

            all_endpoints.extend(endpoints)

            # Check for next page
            pages = data.get("pages", {})
            page_from_key = pages.get("nextKey")

            if not page_from_key:
                break

        return all_endpoints

    def get_all_endpoints(self) -> List[Dict]:
        """
        Get all endpoints across all tenants

        Returns:
            list: List of dictionaries containing tenant info and endpoints
        """
        tenants = self.get_tenants()
        all_data = []

        for tenant in tenants:
            tenant_id = tenant.get("id")
            tenant_name = tenant.get("name")
            api_host = tenant.get("apiHost")

            if not tenant_id or not api_host:
                continue

            try:
                endpoints = self.get_endpoints_for_tenant(tenant_id, api_host)

                for endpoint in endpoints:
                    os_info = endpoint.get("os", {})
                    build = os_info.get("build", "N/A")
                    last_seen = endpoint.get("lastSeenAt", "N/A")

                    # Format date only (remove time portion)
                    if last_seen != "N/A":
                        try:
                            # Parse ISO format and extract date only
                            last_seen = last_seen.split("T")[0]
                        except:
                            pass  # Keep original if parsing fails

                    all_data.append({
                        "tenant_id": tenant_id,
                        "tenant_name": tenant_name,
                        "endpoint_hostname": endpoint.get("hostname", "N/A"),
                        "endpoint_os": os_info.get("name", "N/A"),
                        "endpoint_os_version": build,
                        "last_active": last_seen
                    })
            except Exception as e:
                # Continue with other tenants if one fails
                print(f"Warning: Failed to get endpoints for tenant {tenant_name}: {e}")
                continue

        # Sort by tenant name, then hostname
        all_data.sort(key=lambda x: (x.get("tenant_name", "").lower(), x.get("endpoint_hostname", "").lower()))

        return all_data

    def get_tenant_health(self, tenant_id: str, api_host: str) -> Dict:
        """
        Get account health check for a specific tenant

        Args:
            tenant_id: The tenant ID
            api_host: The API host URL for the tenant's region

        Returns:
            dict: Health check data for the tenant
        """
        if not self.access_token:
            self.authenticate()

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-Tenant-ID": tenant_id
        }

        response = requests.get(
            f"{api_host}/account-health-check/v1/health-check",
            headers=headers
        )
        response.raise_for_status()

        return response.json()

    def get_all_tenant_health(self) -> List[Dict]:
        """
        Get account health for all tenants

        Returns:
            list: List of dictionaries containing tenant info and health data
        """
        tenants = self.get_tenants()
        all_health_data = []

        for tenant in tenants:
            tenant_id = tenant.get("id")
            tenant_name = tenant.get("name")
            api_host = tenant.get("apiHost")

            if not tenant_id or not api_host:
                continue

            try:
                health_data = self.get_tenant_health(tenant_id, api_host)

                # Extract endpoint health data
                endpoint = health_data.get("endpoint", {})

                # Protection scores (combine computer and server)
                protection = endpoint.get("protection", {})
                computer_protection = protection.get("computer", {}).get("score", 0)
                server_protection = protection.get("server", {}).get("score", 0)

                # Policy scores (get lowest score from all policies)
                policy = endpoint.get("policy", {})
                computer_policy_scores = []
                server_policy_scores = []

                for policy_type, policy_data in policy.get("computer", {}).items():
                    if isinstance(policy_data, dict) and "score" in policy_data:
                        computer_policy_scores.append(policy_data["score"])

                for policy_type, policy_data in policy.get("server", {}).items():
                    if isinstance(policy_data, dict) and "score" in policy_data:
                        server_policy_scores.append(policy_data["score"])

                avg_computer_policy = sum(computer_policy_scores) / len(computer_policy_scores) if computer_policy_scores else 100
                avg_server_policy = sum(server_policy_scores) / len(server_policy_scores) if server_policy_scores else 100

                # Exclusions scores
                exclusions = endpoint.get("exclusions", {})
                computer_exclusions = exclusions.get("policy", {}).get("computer", {}).get("score", 100)
                server_exclusions = exclusions.get("policy", {}).get("server", {}).get("score", 100)
                global_exclusions = exclusions.get("global", {}).get("score", 100)

                # Tamper protection scores
                tamper = endpoint.get("tamperProtection", {})
                computer_tamper = tamper.get("computer", {}).get("score", 100)
                server_tamper = tamper.get("server", {}).get("score", 100)
                global_tamper = tamper.get("globalDetail", {}).get("score", 100)

                # Network device scores (firewall)
                network_device = health_data.get("networkDevice", {})
                firewall = network_device.get("firewall", {})
                firewall_scores = []

                for check_type, check_data in firewall.items():
                    if isinstance(check_data, dict) and "score" in check_data:
                        firewall_scores.append(check_data["score"])

                avg_firewall = sum(firewall_scores) / len(firewall_scores) if firewall_scores else 100

                # Calculate weighted average scores
                avg_protection = (computer_protection + server_protection) / 2
                avg_policy = (avg_computer_policy + avg_server_policy) / 2
                avg_exclusions = (computer_exclusions + server_exclusions + global_exclusions) / 3
                avg_tamper = (computer_tamper + server_tamper + global_tamper) / 3

                # Calculate overall score (including firewall now)
                overall_score = (avg_protection + avg_policy + avg_exclusions + avg_tamper + avg_firewall) / 5

                all_health_data.append({
                    "tenant_name": tenant_name,
                    "tenant_id": tenant_id,
                    "overall_score": round(overall_score, 1),
                    "protection_score": round(avg_protection, 1),
                    "policy_score": round(avg_policy, 1),
                    "exclusions_score": round(avg_exclusions, 1),
                    "tamper_protection_score": round(avg_tamper, 1),
                    "firewall_score": round(avg_firewall, 1)
                })
            except Exception as e:
                # Continue with other tenants if one fails
                print(f"Warning: Failed to get health data for tenant {tenant_name}: {e}")
                continue

        # Sort by tenant name
        all_health_data.sort(key=lambda x: x.get("tenant_name", "").lower())

        return all_health_data
