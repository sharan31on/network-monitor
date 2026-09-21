import time
import sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from rich.console import Console
from rich.table import Table

import ping_engine
import probe
import database
import alerter

console = Console()

TARGETS = ["8.8.8.8", "1.1.1.1", "github.com"]

def check_target(target: str, latency_alert_ms: float = 100.0):
    """Executes ping and port checks for a single host and sends alerts on failure."""
    ping_res = ping_engine.ping_host(target, count=2, timeout_sec=1)
    port_res = probe.probe_single_port(target, 443, "HTTPS", timeout=1.0)

    avg_rtt = ping_res.get("avg_rtt")
    loss = ping_res.get("loss_pct", 100.0)

    health = "HEALTHY"
    if loss > 0:
        health = f"LOSS ({loss:.0f}%)"
    elif avg_rtt and avg_rtt > latency_alert_ms:
        health = f"HIGH LATENCY ({avg_rtt:.1f}ms)"
    elif port_res["status"] != "OPEN":
        health = f"PORT 443 {port_res['status']}"

    # Trigger alert on packet loss or port failure
    if loss > 0 or port_res["status"] != "OPEN":
        alerter.send_alert(
            target=target,
            reason=health,
            details=f"Ping Loss: {loss:.0f}%, Port 443: {port_res['status']}"
        )

    # Log metric directly into SQLite
    database.log_metric(
        target=target,
        rtt=avg_rtt,
        loss=loss,
        port_status=port_res["status"],
        health=health
    )

    return {
        "target": target,
        "rtt": f"{avg_rtt:.1f} ms" if avg_rtt else "-",
        "loss": f"{loss:.0f}%",
        "port_443": port_res["status"],
        "health": health
    }

def run_multi_watch(interval: int = 4):
    database.init_db()
    console.print(f"[bold yellow]Monitoring targets:[/bold yellow] [bold cyan]{', '.join(TARGETS)}[/bold cyan]")
    console.print(f"[dim]Polling every {interval}s. Data logged to metrics.db. Press Ctrl+C to stop.[/dim]\n")

    try:
        while True:
            timestamp = datetime.now().strftime("%H:%M:%S")

            # Check all targets concurrently using threads
            with ThreadPoolExecutor(max_workers=len(TARGETS)) as executor:
                results = list(executor.map(check_target, TARGETS))

            table = Table(title=f"Multi-Target Network Health ({timestamp})")
            table.add_column("Target Host", style="cyan", justify="left")
            table.add_column("Ping Latency", justify="right")
            table.add_column("Packet Loss", justify="center")
            table.add_column("HTTPS (443)", justify="center")
            table.add_column("Health Status", justify="center")

            for res in results:
                health_style = "[green]HEALTHY[/green]" if res["health"] == "HEALTHY" else f"[bold red]{res['health']}[/bold red]"
                port_style = "[green]OPEN[/green]" if res["port_443"] == "OPEN" else "[yellow]" + res["port_443"] + "[/yellow]"
                table.add_row(res["target"], res["rtt"], res["loss"], port_style, health_style)

            console.clear()
            console.print(table)
            time.sleep(interval)

    except KeyboardInterrupt:
        console.print("\n[bold red]Multi-target monitoring stopped.[/bold red]")

if __name__ == "__main__":
    run_multi_watch(interval=4)