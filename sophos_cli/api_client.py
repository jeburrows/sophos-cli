"""Sophos API Client for Partner and Endpoint APIs"""

import os
from datetime import datetime, timezone
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
                computer_protection = protection.get("computer", {}).get("score") if protection.get("computer", {}).get("total", 0) > 0 else None
                server_protection = protection.get("server", {}).get("score") if protection.get("server", {}).get("total", 0) > 0 else None

                # Policy scores
                policy = endpoint.get("policy", {})
                computer_policy_scores = []
                server_policy_scores = []

                for policy_type, policy_data in policy.get("computer", {}).items():
                    if isinstance(policy_data, dict) and "score" in policy_data:
                        computer_policy_scores.append(policy_data["score"])

                for policy_type, policy_data in policy.get("server", {}).items():
                    if isinstance(policy_data, dict) and "score" in policy_data:
                        server_policy_scores.append(policy_data["score"])

                avg_computer_policy = sum(computer_policy_scores) / len(computer_policy_scores) if computer_policy_scores else None
                avg_server_policy = sum(server_policy_scores) / len(server_policy_scores) if server_policy_scores else None

                # Exclusions scores
                exclusions = endpoint.get("exclusions", {})
                computer_exclusions = exclusions.get("policy", {}).get("computer", {}).get("score") if exclusions.get("policy", {}).get("computer", {}).get("total", 0) > 0 else None
                server_exclusions = exclusions.get("policy", {}).get("server", {}).get("score") if exclusions.get("policy", {}).get("server", {}).get("total", 0) > 0 else None
                global_exclusions = exclusions.get("global", {}).get("score") if "score" in exclusions.get("global", {}) else None

                # Tamper protection scores
                tamper = endpoint.get("tamperProtection", {})
                computer_tamper = tamper.get("computer", {}).get("score") if tamper.get("computer", {}).get("total", 0) > 0 else None
                server_tamper = tamper.get("server", {}).get("score") if tamper.get("server", {}).get("total", 0) > 0 else None
                global_tamper = tamper.get("globalDetail", {}).get("score") if "score" in tamper.get("globalDetail", {}) else None

                # Network device scores (firewall)
                network_device = health_data.get("networkDevice", {})
                firewall = network_device.get("firewall", {})
                firewall_scores = []

                for check_type, check_data in firewall.items():
                    if isinstance(check_data, dict) and "score" in check_data:
                        firewall_scores.append(check_data["score"])

                avg_firewall = sum(firewall_scores) / len(firewall_scores) if firewall_scores else None

                # Calculate weighted average scores (only for components that exist)
                protection_scores = [s for s in [computer_protection, server_protection] if s is not None]
                avg_protection = sum(protection_scores) / len(protection_scores) if protection_scores else None

                # If no protection (no endpoints), then policy, exclusions, and tamper are also N/A
                if avg_protection is None:
                    avg_policy = None
                    avg_exclusions = None
                    avg_tamper = None
                else:
                    policy_scores = [s for s in [avg_computer_policy, avg_server_policy] if s is not None]
                    avg_policy = sum(policy_scores) / len(policy_scores) if policy_scores else None

                    exclusions_scores = [s for s in [computer_exclusions, server_exclusions, global_exclusions] if s is not None]
                    avg_exclusions = sum(exclusions_scores) / len(exclusions_scores) if exclusions_scores else None

                    tamper_scores = [s for s in [computer_tamper, server_tamper, global_tamper] if s is not None]
                    avg_tamper = sum(tamper_scores) / len(tamper_scores) if tamper_scores else None

                # Calculate overall score (only include categories that have data)
                all_scores = [s for s in [avg_protection, avg_policy, avg_exclusions, avg_tamper, avg_firewall] if s is not None]
                overall_score = sum(all_scores) / len(all_scores) if all_scores else None

                all_health_data.append({
                    "tenant_name": tenant_name,
                    "tenant_id": tenant_id,
                    "overall_score": round(overall_score, 1) if overall_score is not None else "N/A",
                    "protection_score": round(avg_protection, 1) if avg_protection is not None else "N/A",
                    "policy_score": round(avg_policy, 1) if avg_policy is not None else "N/A",
                    "exclusions_score": round(avg_exclusions, 1) if avg_exclusions is not None else "N/A",
                    "tamper_protection_score": round(avg_tamper, 1) if avg_tamper is not None else "N/A",
                    "firewall_score": round(avg_firewall, 1) if avg_firewall is not None else "N/A"
                })
            except Exception as e:
                # Continue with other tenants if one fails
                print(f"Warning: Failed to get health data for tenant {tenant_name}: {e}")
                continue

        # Sort by tenant name
        all_health_data.sort(key=lambda x: x.get("tenant_name", "").lower())

        return all_health_data

    def get_firewalls_for_tenant(self, tenant_id: str, api_host: str) -> List[Dict]:
        """
        Get all firewalls for a specific tenant

        Args:
            tenant_id: The tenant ID
            api_host: The API host URL for the tenant's region

        Returns:
            list: List of firewall dictionaries
        """
        if not self.access_token:
            self.authenticate()

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-Tenant-ID": tenant_id
        }

        all_firewalls = []
        page_from_key = None

        while True:
            params = {"pageSize": 100}
            if page_from_key:
                params["pageFromKey"] = page_from_key

            response = requests.get(
                f"{api_host}/firewall/v1/firewalls",
                headers=headers,
                params=params
            )
            response.raise_for_status()

            data = response.json()
            firewalls = data.get("items", [])

            if not firewalls:
                break

            all_firewalls.extend(firewalls)

            # Check for next page
            pages = data.get("pages", {})
            page_from_key = pages.get("nextKey")

            if not page_from_key:
                break

        return all_firewalls

    def get_all_firewalls(self) -> List[Dict]:
        """
        Get all firewalls across all tenants

        Returns:
            list: List of dictionaries containing tenant info and firewall details
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
                firewalls = self.get_firewalls_for_tenant(tenant_id, api_host)

                for firewall in firewalls:
                    # Extract cluster/HA status
                    cluster = firewall.get("cluster", {})
                    ha_status = cluster.get("status", "N/A") if cluster else "N/A"

                    all_data.append({
                        "tenant_id": tenant_id,
                        "tenant_name": tenant_name,
                        "firewall_name": firewall.get("name", "N/A"),
                        "firewall_hostname": firewall.get("hostname", "N/A"),
                        "firewall_model": firewall.get("model", "N/A"),
                        "firewall_status": ha_status,
                        "firewall_serial": firewall.get("serialNumber", "N/A"),
                        "firewall_firmware": firewall.get("firmwareVersion", "N/A")
                    })
            except Exception as e:
                # Continue with other tenants if one fails
                print(f"Warning: Failed to get firewalls for tenant {tenant_name}: {e}")
                continue

        # Sort by tenant name, then firewall name
        all_data.sort(key=lambda x: (x.get("tenant_name", "").lower(), x.get("firewall_name", "").lower()))

        return all_data

    def get_licenses_for_tenant(self, tenant_id: str, api_host: str) -> List[Dict]:
        """
        Get all licenses for a specific tenant

        Args:
            tenant_id: The tenant ID
            api_host: The API host URL for the tenant's region (not used for licensing API)

        Returns:
            list: List of license dictionaries
        """
        if not self.access_token:
            self.authenticate()

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-Tenant-ID": tenant_id
        }

        # Licensing API uses the global endpoint, not regional
        licensing_url = f"{self.PARTNER_API_BASE}/licenses/v1/licenses"

        response = requests.get(
            licensing_url,
            headers=headers
        )
        response.raise_for_status()

        data = response.json()

        # The API returns licenses in "licenses" array, not "items"
        return data.get("licenses", [])

    def get_all_licenses(self) -> List[Dict]:
        """
        Get all licenses across all tenants

        Returns:
            list: List of dictionaries containing tenant info and license details
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
                licenses = self.get_licenses_for_tenant(tenant_id, api_host)

                for license in licenses:
                    # Only include usage-based licenses (billable)
                    if license.get("type") != "usage":
                        continue

                    # Only show licenses with actual usage count > 0
                    usage = license.get("usage", {})
                    current = usage.get("current", {})
                    usage_count = current.get("count", 0)

                    if usage_count == 0:
                        continue

                    product = license.get("product", {})
                    product_name = product.get("name", "N/A") if isinstance(product, dict) else "N/A"
                    product_code = product.get("code", "N/A") if isinstance(product, dict) else "N/A"

                    all_data.append({
                        "tenant_id": tenant_id,
                        "tenant_name": tenant_name,
                        "license_id": license.get("id", "N/A"),
                        "license_identifier": license.get("licenseIdentifier", "N/A"),
                        "license_type": license.get("type", "N/A"),
                        "license_product": product_name,
                        "license_product_code": product_code,
                        "license_start": license.get("startDate", "N/A"),
                        "license_usage_count": usage_count,
                        "license_usage_date": current.get("date", "N/A"),
                        "license_perpetual": "Yes" if license.get("perpetual") else "No",
                        "license_unlimited": "Yes" if license.get("unlimited") else "No"
                    })
            except Exception as e:
                # Continue with other tenants if one fails
                print(f"Warning: Failed to get licenses for tenant {tenant_name}: {e}")
                continue

        # Sort by tenant name, then product name
        all_data.sort(key=lambda x: (x.get("tenant_name", "").lower(), x.get("license_product", "").lower()))

        return all_data

    GRAPHQL_URL = "https://api.taegis.sophos.com/graphql"

    def _graphql(self, tenant_id: str, query: str, variables: Dict) -> Dict:
        """Run a read-only GraphQL query for a tenant and return its data"""
        if not self.access_token:
            self.authenticate()

        response = requests.post(
            self.GRAPHQL_URL,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "X-Tenant-ID": tenant_id,
            },
            json={"query": query, "variables": variables},
        )
        response.raise_for_status()

        body = response.json()
        # GraphQL errors come back as HTTP 200 with an "errors" array
        if body.get("errors"):
            raise RuntimeError(body["errors"][0].get("message", "GraphQL error"))
        return body["data"]

    def _for_each_tenant(self, label: str, fetch) -> List[Dict]:
        """Call fetch(tenant) for every tenant, skipping tenants that fail"""
        rows = []
        for tenant in self.get_tenants():
            if not tenant.get("id") or not tenant.get("apiHost"):
                continue
            try:
                rows.extend(fetch(tenant))
            except Exception as e:
                print(f"Warning: Failed to get {label} for tenant {tenant.get('name')}: {e}")
        rows.sort(key=lambda x: x["tenant_name"].lower())
        return rows

    @staticmethod
    def _date(value) -> str:
        """Date portion of an ISO timestamp, or N/A"""
        return value.split("T")[0] if value else "N/A"

    def get_all_detections(self) -> List[Dict]:
        """Get open detections (severity >= 0.3) from the last 7 days across all tenants"""
        query = """
        query ($in: SearchRequestInput) {
          detectionSearch(in: $in) {
            alerts { total_results list { id status metadata { title severity created_at { seconds } } } }
          }
        }"""
        cql = "from alert where status = 'OPEN' and severity >= 0.3 earliest=-7d"

        def fetch(tenant):
            rows, offset = [], 0
            while True:
                data = self._graphql(tenant["id"], query, {"in": {"cql_query": cql, "offset": offset, "limit": 500}})
                alerts = data["detectionSearch"]["alerts"]
                items = alerts.get("list") or []
                for d in items:
                    meta = d.get("metadata") or {}
                    seconds = (meta.get("created_at") or {}).get("seconds")
                    created = datetime.fromtimestamp(int(seconds), timezone.utc).strftime("%Y-%m-%d") if seconds else "N/A"
                    rows.append({
                        "tenant_id": tenant["id"],
                        "tenant_name": tenant["name"],
                        "detection_id": d.get("id", "N/A"),
                        "detection_title": meta.get("title", "N/A"),
                        "detection_severity": meta.get("severity", "N/A"),
                        "detection_status": d.get("status", "N/A"),
                        "detection_created": created,
                    })
                offset += len(items)
                # ponytail: offset paging caps at 10,000; use detectionPoll/search_id if a tenant exceeds it
                if not items or offset >= alerts.get("total_results", 0):
                    return rows

        return self._for_each_tenant("detections", fetch)

    def get_all_cases(self) -> List[Dict]:
        """Get open (not closed) cases across all tenants"""
        query = """
        query ($arguments: CasesArguments!) {
          cases(arguments: $arguments) {
            totalCount
            cases { shortId title severity primaryStatus { name } createdAt closedAt }
          }
        }"""

        def fetch(tenant):
            rows, page = [], 1
            while True:
                args = {"pagination": {"offset": {"page": page, "perPage": 100}}}
                data = self._graphql(tenant["id"], query, {"arguments": args})["cases"]
                cases = data.get("cases") or []
                for c in cases:
                    if c.get("closedAt"):
                        continue
                    rows.append({
                        "tenant_id": tenant["id"],
                        "tenant_name": tenant["name"],
                        "case_id": c.get("shortId", "N/A"),
                        "case_title": c.get("title", "N/A"),
                        "case_severity": c.get("severity", "N/A"),
                        "case_status": (c.get("primaryStatus") or {}).get("name", "N/A"),
                        "case_created": self._date(c.get("createdAt")),
                    })
                if not cases or page * 100 >= data.get("totalCount", 0):
                    return rows
                page += 1

        return self._for_each_tenant("cases", fetch)

    def get_all_dns_locations(self) -> List[Dict]:
        """Get DNS Protection locations with policy names across all tenants (read-only GET)"""
        def fetch(tenant):
            headers = {"Authorization": f"Bearer {self.access_token}", "X-Tenant-ID": tenant["id"]}

            def get_items(path):
                items, page = [], 1
                while True:
                    response = requests.get(
                        f"{tenant['apiHost']}/dns-protection/v2/{path}",
                        headers=headers,
                        params={"page": page, "pageSize": 200, "pageTotal": "true"},
                    )
                    # 403 = tenant has no DNS Protection; skip quietly
                    if response.status_code == 403:
                        return []
                    response.raise_for_status()
                    data = response.json()
                    items.extend(data.get("items", []))
                    if page >= data.get("pages", {}).get("total", 1):
                        return items
                    page += 1

            locations = get_items("locations")
            policies = {p["id"]: p.get("name", "N/A") for p in get_items("policies")} if locations else {}
            return [{
                "tenant_id": tenant["id"],
                "tenant_name": tenant["name"],
                "location_name": loc.get("name", "N/A"),
                "location_policy": policies.get(loc.get("policyId"), "None"),
                "location_default": "Yes" if loc.get("isDefault") else "No",
                "location_doh": "Yes" if loc.get("dohEnabled") else "No",
                "location_ips": ", ".join(loc.get("ipAddresses") or []) or "N/A",
            } for loc in locations]

        if not self.access_token:
            self.authenticate()
        return self._for_each_tenant("DNS locations", fetch)
