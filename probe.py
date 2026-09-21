import socket
import time
from concurrent.futures import ThreadPoolExecutor
from rich.console import Console
from rich.table import Table

console = Console()

COMMON_PORTS = {
    21: "FTP",
    22: "SSH",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    143: "IMAP",
    443: "HTTPS",
    3306: "MySQL",
    5432: "PostgreSQL",
    8080: "HTTP-Proxy"
}

def resolve_hostname(domain: str) -> str:
    try:
        return socket.gethostbyname(domain)
    except socket.gaierror:
        return None

def probe_single_port(ip: str, port: int, service: str, timeout: float = 1.5) -> dict:
    """Probes an individual port and calculates round-trip latency."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    
    start_time = time.perf_counter()
    try:
        sock.connect((ip, port))
        latency = (time.perf_counter() - start_time) * 1000
        sock.close()
        return {"port": port, "service": service, "status": "OPEN", "latency": f"{latency:.2f} ms"}
    except socket.timeout:
        return {"port": port, "service": service, "status": "FILTERED / TIMEOUT", "latency": "-"}
    except ConnectionRefusedError:
        return {"port": port, "service": service, "status": "CLOSED", "latency": "-"}
    except Exception:
        return {"port": port, "service": service, "status": "ERROR", "latency": "-"}

def scan_target(target: str):
    console.print(f"\n[bold cyan]Starting scan for:[/bold cyan] [yellow]{target}[/yellow]")
    
    ip = resolve_hostname(target)
    if not ip:
        console.print(f"[bold red]Failed to resolve {target}[/bold red]")
        return

    console.print(f"[bold green]Resolved IP:[/bold green] {ip}\n")

    # Run checks concurrently using a thread pool
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(probe_single_port, ip, port, service)
            for port, service in COMMON_PORTS.items()
        ]
        for f in futures:
            results.append(f.result())

    # Build the Rich output table
    table = Table(title=f"Port Scan Results: {target} ({ip})")
    table.add_column("Port", justify="right", style="cyan")
    table.add_column("Service", style="magenta")
    table.add_column("Status", justify="center")
    table.add_column("Latency", justify="right", style="green")

    for res in sorted(results, key=lambda x: x["port"]):
        if res["status"] == "OPEN":
            status_style = "[bold green]OPEN[/bold green]"
        elif "TIMEOUT" in res["status"]:
            status_style = "[yellow]FILTERED[/yellow]"
        else:
            status_style = "[red]CLOSED[/red]"

        table.add_row(str(res["port"]), res["service"], status_style, res["latency"])

    console.print(table)

if __name__ == "__main__":
    scan_target("google.com")