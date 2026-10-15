"""Main CLI application for Sophos Partner API"""

import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich import box

from .api_client import SophosAPIClient
from .utils import export_to_csv

console = Console()


def display_menu():
    """Display the main menu"""
    menu_text = """
[bold cyan]Sophos Partner CLI[/bold cyan]

[1] List All Tenants
[2] List All Endpoints
[3] Show Account Health for All Tenants
[4] List All Firewalls
[5] List All Licenses
[6] List Open Detections (High Severity, 7 days)
[7] List Open Cases
[8] List DNS Protection Locations
[9] Exit
"""
    console.print(Panel(menu_text, box=box.ROUNDED, border_style="cyan"))


def list_tenants(client: SophosAPIClient):
    """Display all tenants and export to CSV"""
    console.print("\n[yellow]Fetching tenants...[/yellow]")

    try:
        tenants = client.get_tenants()

        if not tenants:
            console.print("[red]No tenants found.[/red]")
            return

        # Create table for display
        table = Table(title="Sophos Tenants", box=box.ROUNDED)
        table.add_column("Tenant Name", style="cyan", no_wrap=False)
        table.add_column("Tenant ID", style="magenta")
        table.add_column("Data Region", style="green")
        table.add_column("Status", style="yellow")

        # Prepare data for CSV export
        csv_data = []

        for tenant in tenants:
            name = tenant.get("name", "N/A")
            tenant_id = tenant.get("id", "N/A")
            data_region = tenant.get("dataRegion", "N/A")
            status = tenant.get("status", "N/A")

            table.add_row(name, tenant_id, data_region, status)

            csv_data.append({
                "tenant_name": name,
                "tenant_id": tenant_id,
                "data_region": data_region,
                "api_host": tenant.get("apiHost", "N/A"),
                "status": status
            })

        # Display table
        console.print(table)
        console.print(f"\n[green]Total tenants: {len(tenants)}[/green]")

        # Export to CSV
        csv_path = export_to_csv(
            csv_data,
            "sophos_tenants",
            ["tenant_name", "tenant_id", "data_region", "api_host", "status"]
        )
        console.print(f"[green]Data exported to: {csv_path}[/green]\n")

    except Exception as e:
        console.print(f"[red]Error fetching tenants: {e}[/red]")


def list_endpoints(client: SophosAPIClient):
    """Display all endpoints across all tenants and export to CSV"""
    console.print("\n[yellow]Fetching endpoints from all tenants...[/yellow]")
    console.print("[dim]This may take a moment...[/dim]\n")

    try:
        endpoints_data = client.get_all_endpoints()

        if not endpoints_data:
            console.print("[red]No endpoints found.[/red]")
            return

        # Create table for display
        table = Table(title="Sophos Endpoints", box=box.ROUNDED)
        table.add_column("Tenant Name", style="cyan", no_wrap=False)
        table.add_column("Hostname", style="magenta", no_wrap=False)
        table.add_column("OS", style="green")
        table.add_column("OS Version", style="yellow", no_wrap=False)
        table.add_column("Last Active", style="blue", no_wrap=False)

        for endpoint in endpoints_data:
            table.add_row(
                endpoint["tenant_name"],
                endpoint["endpoint_hostname"],
                endpoint["endpoint_os"],
                str(endpoint["endpoint_os_version"]),
                str(endpoint["last_active"])
            )

        # Display table
        console.print(table)
        console.print(f"\n[green]Total endpoints: {len(endpoints_data)}[/green]")

        # Export to CSV
        csv_path = export_to_csv(
            endpoints_data,
            "sophos_endpoints",
            ["tenant_name", "tenant_id", "endpoint_hostname", "endpoint_os", "endpoint_os_version", "last_active"]
        )
        console.print(f"[green]Data exported to: {csv_path}[/green]\n")

    except Exception as e:
        console.print(f"[red]Error fetching endpoints: {e}[/red]")


def show_tenant_health(client: SophosAPIClient):
    """Display account health for all tenants and export to CSV"""
    console.print("\n[yellow]Fetching account health from all tenants...[/yellow]")
    console.print("[dim]This may take a moment...[/dim]\n")

    try:
        health_data = client.get_all_tenant_health()

        if not health_data:
            console.print("[red]No health data found.[/red]")
            return

        # Create table for display
        table = Table(title="Tenant Account Health", box=box.ROUNDED)
        table.add_column("Tenant Name", style="cyan", no_wrap=False)
        table.add_column("Overall Score", style="magenta", justify="center")
        table.add_column("Protection", style="yellow", justify="center")
        table.add_column("Policy", style="yellow", justify="center")
        table.add_column("Exclusions", style="yellow", justify="center")
        table.add_column("Tamper Protection", style="yellow", justify="center")
        table.add_column("Firewall", style="yellow", justify="center")

        for health in health_data:
            table.add_row(
                health["tenant_name"],
                str(health["overall_score"]),
                str(health["protection_score"]),
                str(health["policy_score"]),
                str(health["exclusions_score"]),
                str(health["tamper_protection_score"]),
                str(health["firewall_score"])
            )

        # Display table
        console.print(table)
        console.print(f"\n[green]Total tenants checked: {len(health_data)}[/green]")

        # Export to CSV
        csv_path = export_to_csv(
            health_data,
            "sophos_tenant_health",
            ["tenant_name", "tenant_id", "overall_score", "protection_score",
             "policy_score", "exclusions_score", "tamper_protection_score", "firewall_score"]
        )
        console.print(f"[green]Data exported to: {csv_path}[/green]\n")

    except Exception as e:
        console.print(f"[red]Error fetching tenant health: {e}[/red]")


def list_firewalls(client: SophosAPIClient):
    """Display all firewalls across all tenants and export to CSV"""
    console.print("\n[yellow]Fetching firewalls from all tenants...[/yellow]")
    console.print("[dim]This may take a moment...[/dim]\n")

    try:
        firewalls_data = client.get_all_firewalls()

        if not firewalls_data:
            console.print("[red]No firewalls found.[/red]")
            return

        # Create table for display
        table = Table(title="Sophos Firewalls", box=box.ROUNDED)
        table.add_column("Tenant Name", style="cyan", no_wrap=False)
        table.add_column("Firewall Name", style="magenta", no_wrap=False)
        table.add_column("Hostname", style="green", no_wrap=False)
        table.add_column("Model", style="yellow", no_wrap=False)
        table.add_column("Status", style="blue")
        table.add_column("Serial Number", style="white", no_wrap=False)
        table.add_column("Firmware", style="white", no_wrap=False)

        for firewall in firewalls_data:
            table.add_row(
                str(firewall["tenant_name"]),
                str(firewall["firewall_name"]),
                str(firewall["firewall_hostname"]),
                str(firewall["firewall_model"]),
                str(firewall["firewall_status"]),
                str(firewall["firewall_serial"]),
                str(firewall["firewall_firmware"])
            )

        # Display table
        console.print(table)
        console.print(f"\n[green]Total firewalls: {len(firewalls_data)}[/green]")

        # Export to CSV
        csv_path = export_to_csv(
            firewalls_data,
            "sophos_firewalls",
            ["tenant_name", "tenant_id", "firewall_name", "firewall_hostname",
             "firewall_model", "firewall_status", "firewall_serial", "firewall_firmware"]
        )
        console.print(f"[green]Data exported to: {csv_path}[/green]\n")

    except Exception as e:
        console.print(f"[red]Error fetching firewalls: {e}[/red]")


def list_licenses(client: SophosAPIClient):
    """Display all licenses across all tenants and export to CSV"""
    console.print("\n[yellow]Fetching licenses from all tenants...[/yellow]")
    console.print("[dim]This may take a moment...[/dim]\n")

    try:
        licenses_data = client.get_all_licenses()

        if not licenses_data:
            console.print("[red]No licenses found.[/red]")
            return

        # Create table for display
        table = Table(title="Sophos Licenses (Usage-Based)", box=box.ROUNDED)
        table.add_column("Tenant Name", style="cyan", no_wrap=False)
        table.add_column("Product", style="green", no_wrap=False)
        table.add_column("Product Code", style="magenta", no_wrap=False)
        table.add_column("Usage Count", style="yellow", justify="right")
        table.add_column("Usage Date", style="white")
        table.add_column("Start Date", style="white")

        for license in licenses_data:
            table.add_row(
                str(license["tenant_name"]),
                str(license["license_product"]),
                str(license["license_product_code"]),
                str(license["license_usage_count"]),
                str(license["license_usage_date"]),
                str(license["license_start"])
            )

        # Display table
        console.print(table)
        console.print(f"\n[green]Total licenses: {len(licenses_data)}[/green]")

        # Export to CSV
        csv_path = export_to_csv(
            licenses_data,
            "sophos_licenses",
            ["tenant_name", "tenant_id", "license_id", "license_identifier",
             "license_type", "license_product", "license_product_code",
             "license_usage_count", "license_usage_date", "license_start",
             "license_perpetual", "license_unlimited"]
        )
        console.print(f"[green]Data exported to: {csv_path}[/green]\n")

    except Exception as e:
        console.print(f"[red]Error fetching licenses: {e}[/red]")


def _list_generic(title, fetch, columns, csv_name, noun):
    """Fetch rows across tenants, show a table, and export to CSV"""
    console.print(f"\n[yellow]Fetching {noun} from all tenants...[/yellow]")
    console.print("[dim]This may take a moment...[/dim]\n")
    try:
        rows = fetch()
        if not rows:
            console.print(f"[red]No {noun} found.[/red]")
            return
        table = Table(title=title, box=box.ROUNDED)
        for header, key in columns:
            table.add_column(header, no_wrap=False)
        for r in rows:
            table.add_row(*(str(r[key]) for _, key in columns))
        console.print(table)
        console.print(f"\n[green]Total {noun}: {len(rows)}[/green]")
        csv_path = export_to_csv(rows, csv_name, ["tenant_name", "tenant_id"] + [k for _, k in columns if k != "tenant_name"])
        console.print(f"[green]Data exported to: {csv_path}[/green]\n")
    except Exception as e:
        console.print(f"[red]Error fetching {noun}: {e}[/red]")


def list_detections(client: SophosAPIClient):
    _list_generic("Open Detections (Severity >= 0.3, Last 7 Days)", client.get_all_detections,
                  [("Tenant Name", "tenant_name"), ("Title", "detection_title"), ("Severity", "detection_severity"),
                   ("Status", "detection_status"), ("Created", "detection_created"), ("ID", "detection_id")],
                  "sophos_detections", "detections")


def list_cases(client: SophosAPIClient):
    _list_generic("Open Cases", client.get_all_cases,
                  [("Tenant Name", "tenant_name"), ("Case ID", "case_id"), ("Title", "case_title"),
                   ("Severity", "case_severity"), ("Status", "case_status"), ("Created", "case_created")],
                  "sophos_cases", "cases")


def list_dns_locations(client: SophosAPIClient):
    _list_generic("DNS Protection Locations", client.get_all_dns_locations,
                  [("Tenant Name", "tenant_name"), ("Location", "location_name"), ("Policy", "location_policy"),
                   ("Default", "location_default"), ("DoH", "location_doh"), ("IP Addresses", "location_ips")],
                  "sophos_dns_locations", "DNS locations")


def main():
    """Main entry point for the CLI application"""
    console.print("\n[bold cyan]Welcome to Sophos Partner CLI[/bold cyan]\n")

    try:
        # Initialize API client
        client = SophosAPIClient()

        # Authenticate
        console.print("[yellow]Authenticating...[/yellow]")
        client.authenticate()

        # Get partner info
        whoami = client.get_whoami()

        if whoami.get("idType") != "partner":
            console.print("[red]Error: This tool requires a partner account.[/red]")
            sys.exit(1)

        console.print(f"[green]Authenticated as: {whoami.get('id')}[/green]\n")

        # Main menu loop
        while True:
            display_menu()
            choice = Prompt.ask(
                "[bold]Select an option[/bold]",
                choices=[str(i) for i in range(1, 10)],
                default="9"
            )

            if choice == "1":
                list_tenants(client)
            elif choice == "2":
                list_endpoints(client)
            elif choice == "3":
                show_tenant_health(client)
            elif choice == "4":
                list_firewalls(client)
            elif choice == "5":
                list_licenses(client)
            elif choice == "6":
                list_detections(client)
            elif choice == "7":
                list_cases(client)
            elif choice == "8":
                list_dns_locations(client)
            elif choice == "9":
                console.print("\n[cyan]Goodbye![/cyan]\n")
                break

    except ValueError as e:
        console.print(f"[red]Configuration Error: {e}[/red]")
        console.print("\n[yellow]Please ensure you have:")
        console.print("1. Created a .env file (copy from .env.example)")
        console.print("2. Added your Sophos API credentials[/yellow]\n")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n\n[cyan]Interrupted. Goodbye![/cyan]\n")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
