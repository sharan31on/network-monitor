import time
import psutil
from rich.console import Console
from rich.table import Table
from rich.live import Live

console = Console()

def get_net_io():
    """Retrieve cumulative network byte counters per interface."""
    return psutil.net_io_counters(pernic=True)

def generate_table(old_stats, new_stats, interval: float) -> Table:
    table = Table(title=f"Network Interface Throughput (Interval: {interval:.1f}s)")
    table.add_column("Interface", style="cyan", no_wrap=True)
    table.add_column("Download (RX)", justify="right", style="green")
    table.add_column("Upload (TX)", justify="right", style="magenta")
    table.add_column("Packets Recv", justify="right", style="white")
    table.add_column("Packets Sent", justify="right", style="white")
    table.add_column("Drop In/Out", justify="center", style="yellow")

    for iface, initial in old_stats.items():
        if iface not in new_stats:
            continue
        current = new_stats[iface]

        # Calculate speed in Kilobytes per second (KB/s)
        rx_speed = (current.bytes_recv - initial.bytes_recv) / 1024 / interval
        tx_speed = (current.bytes_sent - initial.bytes_sent) / 1024 / interval

        # Filter out inactive virtual adapters with 0 total traffic
        if current.bytes_recv == 0 and current.bytes_sent == 0:
            continue

        drop_str = f"{current.dropin} / {current.dropout}"

        table.add_row(
            iface,
            f"{rx_speed:.2f} KB/s",
            f"{tx_speed:.2f} KB/s",
            str(current.packets_recv),
            str(current.packets_sent),
            drop_str
        )

    return table

def run_live_monitor(interval: float = 1.0):
    console.print("[bold yellow]Press Ctrl+C to stop monitoring...[/bold yellow]\n")
    try:
        with Live(console=console, refresh_per_second=2) as live:
            while True:
                old_stats = get_net_io()
                time.sleep(interval)
                new_stats = get_net_io()
                live.update(generate_table(old_stats, new_stats, interval))
    except KeyboardInterrupt:
        console.print("\n[bold red]Monitoring stopped.[/bold red]")

if __name__ == "__main__":
    run_live_monitor(interval=1.0)