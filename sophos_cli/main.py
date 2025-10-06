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
[2] List All Endpoints (Active)
[3] Show Account Health for All Tenants
[4] Exit
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

        for endpoint in endpoints_data:
            table.add_row(
                endpoint["tenant_name"],
                endpoint["endpoint_hostname"],
                endpoint["endpoint_os"],
                str(endpoint["endpoint_os_version"])
            )

        # Display table
        console.print(table)
        console.print(f"\n[green]Total endpoints: {len(endpoints_data)}[/green]")

        # Export to CSV
        csv_path = export_to_csv(
            endpoints_data,
            "sophos_endpoints",
            ["tenant_name", "tenant_id", "endpoint_hostname", "endpoint_os", "endpoint_os_version"]
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
                choices=["1", "2", "3", "4"],
                default="4"
            )

            if choice == "1":
                list_tenants(client)
            elif choice == "2":
                list_endpoints(client)
            elif choice == "3":
                show_tenant_health(client)
            elif choice == "4":
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
