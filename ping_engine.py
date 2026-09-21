import subprocess
import re
import platform
from rich.console import Console
from rich.table import Table

console = Console()

def ping_host(target: str, count: int = 4, timeout_sec: int = 2) -> dict:
    """
    Executes ICMP echo requests and computes min/avg/max RTT, packet loss, and jitter.
    """
    is_windows = platform.system().lower() == "windows"
    
    # Flags: Windows uses -n for count and -w for timeout (in ms)
    # Unix/Linux/macOS uses -c for count and -W for timeout (in sec)
    if is_windows:
        cmd = ["ping", "-n", str(count), "-w", str(timeout_sec * 1000), target]
    else:
        cmd = ["ping", "-c", str(count), "-W", str(timeout_sec), target]

    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        output = proc.stdout
    except Exception as e:
        return {"error": str(e)}

    # Extract individual packet latencies
    if is_windows:
        # Matches patterns like "time=42ms" or "time<1ms"
        times = re.findall(r"time[=<](\d+)ms", output)
        times = [float(t) for t in times]
    else:
        # Matches patterns like "time=42.1 ms"
        times = re.findall(r"time=([\d\.]+)\s*ms", output)
        times = [float(t) for t in times]

    sent = count
    received = len(times)
    lost = sent - received
    loss_pct = (lost / sent) * 100.0

    if received > 0:
        min_rtt = min(times)
        max_rtt = max(times)
        avg_rtt = sum(times) / received

        # Jitter: average difference between consecutive latency measurements
        if received > 1:
            jitter = sum(abs(times[i] - times[i - 1]) for i in range(1, len(times))) / (received - 1)
        else:
            jitter = 0.0
    else:
        min_rtt = max_rtt = avg_rtt = jitter = None

    return {
        "target": target,
        "sent": sent,
        "received": received,
        "loss_pct": loss_pct,
        "min_rtt": min_rtt,
        "avg_rtt": avg_rtt,
        "max_rtt": max_rtt,
        "jitter": jitter,
        "samples": times
    }

def display_ping(target: str, count: int = 4):
    console.print(f"\n[bold cyan]Sending {count} ICMP Echo Requests to:[/bold cyan] [yellow]{target}[/yellow]...\n")
    data = ping_host(target, count=count)

    if "error" in data:
        console.print(f"[bold red]Ping failed: {data['error']}[/bold red]")
        return

    table = Table(title=f"ICMP Ping Diagnostics: {target}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="white")

    loss_style = "[green]0%[/green]" if data["loss_pct"] == 0 else f"[bold red]{data['loss_pct']:.1f}%[/bold red]"

    table.add_row("Packets Sent", str(data["sent"]))
    table.add_row("Packets Received", str(data["received"]))
    table.add_row("Packet Loss", loss_style)

    if data["avg_rtt"] is not None:
        table.add_row("Min RTT", f"{data['min_rtt']:.1f} ms")
        table.add_row("Avg RTT", f"[bold green]{data['avg_rtt']:.1f} ms[/bold green]")
        table.add_row("Max RTT", f"{data['max_rtt']:.1f} ms")
        table.add_row("Jitter (Latency Variance)", f"{data['jitter']:.2f} ms")
        table.add_row("Individual Samples", ", ".join([f"{t:.0f}ms" for t in data["samples"]]))
    else:
        table.add_row("Status", "[bold red]Host Unreachable (100% loss)[/bold red]")

    console.print(table)

if __name__ == "__main__":
    display_ping("8.8.8.8", count=4)