"""CLI interface for vkslab-esxi."""

from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table

from vkslab_esxi._logging import setup_logging
from vkslab_esxi.config import LabConfig
from vkslab_esxi.inventory import LabInventory

console = Console()


def load_config(config_path: str | None) -> LabConfig:
    """Load config from path or auto-discover."""
    try:
        return LabConfig.find_and_load(config_path)
    except Exception as e:
        console.print(f"[red]Error loading config:[/red] {e}")
        raise SystemExit(1) from e


@click.group()
@click.option("--config", "config_path", default=None, help="Path to lab.yaml config file")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx: click.Context, config_path: str | None, verbose: bool) -> None:
    """VKS Lab ESXi host preparation tool."""
    setup_logging(verbose=verbose)
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config_path


@cli.command()
@click.option("--host", "host_name", default=None, help="Specific host name")
@click.option("--domain", default=None, help="Domain filter (management/workload/all)")
@click.pass_context
def status(ctx: click.Context, host_name: str | None, domain: str | None) -> None:
    """Show host configuration status."""
    config = load_config(ctx.obj["config_path"])
    inventory = LabInventory(config)

    table = Table(title="ESXi Host Status")
    table.add_column("Host", style="cyan")
    table.add_column("IP", style="green")
    table.add_column("Domain")
    table.add_column("MAC")

    if host_name:
        host = inventory.get_host(host_name)
        if not host:
            console.print(f"[red]Host not found:[/red] {host_name}")
            raise SystemExit(1)
        hosts = [host]
    elif domain:
        hosts = inventory.hosts_by_domain(domain)
    else:
        hosts = inventory.all_hosts()

    for h in hosts:
        table.add_row(h.host.name, h.host.ip, h.host.domain, h.host.mac)

    console.print(table)


@cli.command()
@click.option("--host", "host_name", default=None, help="Specific host name")
@click.option("--domain", default="all", help="Domain filter (management/workload/all)")
@click.pass_context
def prepare(ctx: click.Context, host_name: str | None, domain: str) -> None:
    """Run full host preparation sequence."""
    config = load_config(ctx.obj["config_path"])
    inventory = LabInventory(config)

    try:
        password = config.resolve_password(interactive=True)
    except Exception as e:
        console.print(f"[red]Password error:[/red] {e}")
        raise SystemExit(1) from e

    if host_name:
        host = inventory.get_host(host_name)
        if not host:
            console.print(f"[red]Host not found:[/red] {host_name}")
            raise SystemExit(1)
        console.print(f"Preparing [cyan]{host_name}[/cyan]...")
        try:
            host.prepare_full(password)
            console.print(f"[green]✓[/green] {host_name} prepared successfully")
        except Exception as e:
            console.print(f"[red]✗[/red] {host_name} failed: {e}")
            raise SystemExit(1) from e
    else:
        console.print(f"Preparing [cyan]{domain}[/cyan] domain hosts...")
        results = inventory.prepare_all(password, domain=domain)
        for name, success in results.items():
            icon = "[green]✓[/green]" if success else "[red]✗[/red]"
            console.print(f"  {icon} {name}")
        if not all(results.values()):
            raise SystemExit(1)


@cli.command()
@click.option("--host", "host_name", required=True, help="Host name")
@click.pass_context
def storage(ctx: click.Context, host_name: str) -> None:
    """List storage devices and SSD status."""
    config = load_config(ctx.obj["config_path"])
    inventory = LabInventory(config)
    host = inventory.get_host(host_name)
    if not host:
        console.print(f"[red]Host not found:[/red] {host_name}")
        raise SystemExit(1)

    try:
        password = config.resolve_password(interactive=True)
    except Exception as e:
        console.print(f"[red]Password error:[/red] {e}")
        raise SystemExit(1) from e

    from vkslab_esxi.ssh import SSHConnection

    with SSHConnection(host.host.ip, password=password) as ssh:
        devices = host.list_storage_devices(ssh)

    table = Table(title=f"Storage Devices — {host_name}")
    table.add_column("Device ID", style="cyan")
    table.add_column("Display Name")
    table.add_column("Size (MB)", justify="right")
    table.add_column("SSD", justify="center")
    table.add_column("Boot", justify="center")

    for dev in devices:
        table.add_row(
            dev.device_id,
            dev.display_name,
            str(dev.size_mb),
            "[green]Yes[/green]" if dev.is_ssd else "[red]No[/red]",
            "Yes" if dev.is_boot else "No",
        )

    console.print(table)


@cli.command()
@click.option("--host", "host_name", default=None, help="Specific host name")
@click.option("--domain", default="all", help="Domain filter (management/workload/all)")
@click.pass_context
def verify(ctx: click.Context, host_name: str | None, domain: str) -> None:
    """Verify network connectivity from hosts."""
    config = load_config(ctx.obj["config_path"])
    inventory = LabInventory(config)

    try:
        password = config.resolve_password(interactive=True)
    except Exception as e:
        console.print(f"[red]Password error:[/red] {e}")
        raise SystemExit(1) from e

    if host_name:
        hosts = [inventory.get_host(host_name)]
        if hosts[0] is None:
            console.print(f"[red]Host not found:[/red] {host_name}")
            raise SystemExit(1)
    else:
        hosts = inventory.hosts_by_domain(domain)

    from vkslab_esxi.ssh import SSHConnection

    table = Table(title="Network Connectivity")
    table.add_column("Host", style="cyan")
    table.add_column("Gateway", justify="center")
    table.add_column("DNS", justify="center")

    for h in hosts:
        try:
            with SSHConnection(h.host.ip, password=password) as ssh:
                result = h.verify_network_connectivity(ssh)
            gw = "[green]OK[/green]" if result["gateway"] else "[red]FAIL[/red]"
            dns = "[green]OK[/green]" if result["dns"] else "[red]FAIL[/red]"
        except Exception:
            gw = "[red]UNREACHABLE[/red]"
            dns = "[red]UNREACHABLE[/red]"
        table.add_row(h.host.name, gw, dns)

    console.print(table)


@cli.command("mark-ssd")
@click.option("--host", "host_name", required=True, help="Host name")
@click.option("--device", default=None, help="Specific device ID (default: all NVMe)")
@click.pass_context
def mark_ssd(ctx: click.Context, host_name: str, device: str | None) -> None:
    """Mark storage devices as SSD."""
    config = load_config(ctx.obj["config_path"])
    inventory = LabInventory(config)
    host = inventory.get_host(host_name)
    if not host:
        console.print(f"[red]Host not found:[/red] {host_name}")
        raise SystemExit(1)

    try:
        password = config.resolve_password(interactive=True)
    except Exception as e:
        console.print(f"[red]Password error:[/red] {e}")
        raise SystemExit(1) from e

    from vkslab_esxi.ssh import SSHConnection

    with SSHConnection(host.host.ip, password=password) as ssh:
        if device:
            host.mark_device_as_ssd(ssh, device)
            console.print(f"[green]Marked {device} as SSD[/green]")
        else:
            marked = host.mark_all_devices_as_ssd(ssh)
            for dev_id in marked:
                console.print(f"[green]Marked {dev_id} as SSD[/green]")
            if not marked:
                console.print("No devices to mark")


@cli.command("install-vib")
@click.option("--host", "host_name", default=None, help="Specific host name")
@click.option("--domain", default="all", help="Domain filter")
@click.option("--vib-path", required=True, help="Path to VIB file on jumpbox")
@click.pass_context
def install_vib(
    ctx: click.Context, host_name: str | None, domain: str, vib_path: str
) -> None:
    """Install mock HCL VIB for vSAN ESA."""
    config = load_config(ctx.obj["config_path"])
    inventory = LabInventory(config)

    try:
        password = config.resolve_password(interactive=True)
    except Exception as e:
        console.print(f"[red]Password error:[/red] {e}")
        raise SystemExit(1) from e

    if host_name:
        hosts = [inventory.get_host(host_name)]
        if hosts[0] is None:
            console.print(f"[red]Host not found:[/red] {host_name}")
            raise SystemExit(1)
    else:
        hosts = inventory.hosts_by_domain(domain)

    from vkslab_esxi.ssh import SSHConnection

    for h in hosts:
        console.print(f"Installing VIB on [cyan]{h.host.name}[/cyan]...")
        try:
            with SSHConnection(h.host.ip, password=password) as ssh:
                ssh.upload_file(vib_path, "/tmp/mock-hcl.vib")
                h.install_vsan_esa_mock_vib(ssh, "/tmp/mock-hcl.vib")
            console.print(f"  [green]✓[/green] {h.host.name}")
        except Exception as e:
            console.print(f"  [red]✗[/red] {h.host.name}: {e}")
