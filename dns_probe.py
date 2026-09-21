import time
import sys
import dns.resolver
from rich.console import Console
from rich.table import Table

console = Console()

RECORD_TYPES = ["A", "AAAA", "MX", "NS", "TXT"]

def inspect_dns(domain: str):
    console.print(f"\n[bold cyan]DNS Inspection for:[/bold cyan] [yellow]{domain}[/yellow]\n")
    
    table = Table(title=f"DNS Records: {domain}")
    table.add_column("Type", justify="center", style="cyan", width=8)
    table.add_column("Query Latency", justify="right", style="green", width=14)
    table.add_column("Value / Response Data", style="white")

    resolver = dns.resolver.Resolver()
    resolver.timeout = 2.0
    resolver.lifetime = 2.0

    for rtype in RECORD_TYPES:
        start_time = time.perf_counter()
        try:
            answers = resolver.resolve(domain, rtype)
            latency_ms = (time.perf_counter() - start_time) * 1000

            for rdata in answers:
                # Format MX records cleanly (priority + exchange server)
                if rtype == "MX":
                    entry = f"Priority {rdata.preference} -> {rdata.exchange}"
                else:
                    entry = str(rdata)

                table.add_row(rtype, f"{latency_ms:.2f} ms", entry)

        except dns.resolver.NoAnswer:
            table.add_row(rtype, "-", "[dim]No record found[/dim]")
        except dns.resolver.NXDOMAIN:
            table.add_row(rtype, "-", "[red]Domain does not exist[/red]")
            break
        except dns.resolver.LifetimeTimeout:
            table.add_row(rtype, "-", "[red]Query Timed Out[/red]")
        except Exception as e:
            table.add_row(rtype, "-", f"[red]{type(e).__name__}[/red]")

    console.print(table)

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "google.com"
    inspect_dns(target)