import argparse
import sys
from rich.console import Console

# Import the diagnostic modules
import probe
import dns_probe
import net_stats
import ping_engine

console = Console()

def show_banner():
    console.print(r"""[bold cyan]
  _   _      _     __  __             _ _             
 | \ | | ___| |_  |  \/  | ___  _ __ (_) |_ ___  _ __ 
 |  \| |/ _ \ __| | |\/| |/ _ \| '_ \| | __/ _ \| '__|
 | |\  |  __/ |_  | |  | | (_) | | | | | || (_) | |   
 |_| \_|\___|\__| |_|  |_|\___/|_| |_|_|\__\___/|_|   
    [/bold cyan]""", justify="left")
    console.print("[dim]Network Diagnostic & Monitoring CLI Tool[/dim]\n")

def main():
    parser = argparse.ArgumentParser(
        description="Network Monitoring & Diagnostics Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python monitor.py --target google.com --all
  python monitor.py --target 1.1.1.1 --ping
  python monitor.py --target github.com --dns
  python monitor.py --target cloudflare.com --ports
  python monitor.py --live
        """
    )

    parser.add_argument("-t", "--target", type=str, help="Target domain or IP to inspect")
    parser.add_argument("--ping", action="store_true", help="Run ICMP Ping, packet loss & jitter diagnostic")
    parser.add_argument("--dns", action="store_true", help="Run DNS records resolution")
    parser.add_argument("--ports", action="store_true", help="Run concurrent port latency scan")
    parser.add_argument("--all", action="store_true", help="Run all diagnostic scans (Ping, DNS, Ports) on the target")
    parser.add_argument("--live", action="store_true", help="Launch live network interface throughput monitor")

    # If no arguments provided, print help banner
    if len(sys.argv) == 1:
        show_banner()
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()
    show_banner()

    # Route 1: Live traffic throughput monitor
    if args.live:
        net_stats.run_live_monitor(interval=1.0)
        return

    # Route 2: Target-based checks
    if not args.target:
        console.print("[bold red]Error:[/bold red] You must specify a target host with -t / --target (or use --live).")
        sys.exit(1)

    # Determine what to run
    run_ping = args.ping or args.all
    run_dns = args.dns or args.all
    run_ports = args.ports or args.all

    # If target is given without any specific flags, run everything
    if not args.ping and not args.dns and not args.ports and not args.all:
        run_ping = True
        run_dns = True
        run_ports = True

    if run_ping:
        ping_engine.display_ping(args.target, count=4)

    if run_dns:
        dns_probe.inspect_dns(args.target)

    if run_ports:
        probe.scan_target(args.target)

if __name__ == "__main__":
    main()