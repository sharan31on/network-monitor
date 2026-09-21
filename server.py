import sqlite3
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

app = FastAPI(title="Network Monitor Dashboard")
DB_FILE = "metrics.db"

def get_targets():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT target FROM monitor_logs ORDER BY target")
    targets = [r[0] for r in cursor.fetchall()]
    conn.close()
    return targets or ["8.8.8.8"]

def get_stats(target: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Latency logs for selected target
    cursor.execute("""
        SELECT timestamp, target, ping_rtt, packet_loss, health_status
        FROM monitor_logs
        WHERE target = ?
        ORDER BY id DESC
        LIMIT 30
    """, (target,))
    rows = cursor.fetchall()

    # Total statistics for selected target
    cursor.execute("""
        SELECT 
            COUNT(*), 
            AVG(ping_rtt), 
            SUM(CASE WHEN health_status = 'HEALTHY' THEN 1 ELSE 0 END)
        FROM monitor_logs
        WHERE target = ?
    """, (target,))
    total_stats = cursor.fetchone()
    conn.close()

    total_checks = total_stats[0] or 1
    avg_rtt = total_stats[1] or 0.0
    healthy_checks = total_stats[2] or 0
    uptime_pct = (healthy_checks / total_checks) * 100.0

    rows.reverse()
    metrics = [
        {
            "time": r[0].split(" ")[1],
            "target": r[1],
            "rtt": r[2] if r[2] is not None else 0,
            "loss": r[3],
            "health": r[4]
        }
        for r in rows
    ]

    return {
        "metrics": metrics,
        "latest_rtt": metrics[-1]["rtt"] if metrics else 0,
        "latest_target": target,
        "avg_rtt": round(avg_rtt, 1),
        "uptime_pct": round(uptime_pct, 1)
    }

@app.get("/api/targets")
def list_targets():
    return get_targets()

@app.get("/api/metrics")
def metrics_api(target: str = Query("8.8.8.8")):
    return get_stats(target)

@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Network Monitor Live Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: 'Segoe UI', Tahoma, sans-serif; background: #0b1120; color: #f8fafc; padding: 24px; margin: 0; }
            .container { max-width: 1000px; margin: 0 auto; }
            .header-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
            h1 { color: #38bdf8; margin: 0 0 6px 0; font-size: 28px; }
            p.sub { color: #94a3b8; margin: 0; }
            select { background: #1e293b; color: #f8fafc; border: 1px solid #475569; padding: 8px 16px; border-radius: 8px; font-size: 15px; cursor: pointer; outline: none; }
            .grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
            .card { background: #1e293b; padding: 18px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3); border: 1px solid #334155; }
            .card .title { font-size: 13px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; }
            .card .val { font-size: 26px; font-weight: bold; margin-top: 8px; color: #f8fafc; }
            .val.green { color: #4ade80; }
            .val.cyan { color: #38bdf8; }
            .chart-card { background: #1e293b; padding: 24px; border-radius: 12px; border: 1px solid #334155; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header-bar">
                <div>
                    <h1>Network Latency & Health Dashboard</h1>
                    <p class="sub">Multi-target continuous diagnostic stream</p>
                </div>
                <div>
                    <label for="targetSelect" style="color: #94a3b8; margin-right: 8px;">Target:</label>
                    <select id="targetSelect" onchange="switchTarget()"></select>
                </div>
            </div>
            
            <div class="grid">
                <div class="card">
                    <div class="title">Active Target</div>
                    <div class="val cyan" id="targetVal">-</div>
                </div>
                <div class="card">
                    <div class="title">Current Latency</div>
                    <div class="val" id="currentRtt">-</div>
                </div>
                <div class="card">
                    <div class="title">Average Latency</div>
                    <div class="val" id="avgRtt">-</div>
                </div>
                <div class="card">
                    <div class="title">System Uptime</div>
                    <div class="val green" id="uptimeVal">-%</div>
                </div>
            </div>

            <div class="chart-card">
                <canvas id="latencyChart" height="100"></canvas>
            </div>
        </div>

        <script>
            let currentTarget = "8.8.8.8";
            const ctx = document.getElementById('latencyChart').getContext('2d');
            const chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Ping Latency (ms)',
                        data: [],
                        borderColor: '#38bdf8',
                        backgroundColor: 'rgba(56, 189, 248, 0.12)',
                        borderWidth: 2,
                        pointRadius: 4,
                        pointBackgroundColor: '#38bdf8',
                        fill: true,
                        tension: 0.3
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: { beginAtZero: true, grid: { color: '#334155' }, ticks: { color: '#94a3b8' } },
                        x: { grid: { color: '#334155' }, ticks: { color: '#94a3b8' } }
                    },
                    plugins: {
                        legend: { labels: { color: '#f8fafc' } }
                    }
                }
            });

            async function loadTargets() {
                try {
                    const res = await fetch('/api/targets');
                    const targets = await res.json();
                    const select = document.getElementById('targetSelect');
                    select.innerHTML = "";
                    targets.forEach(t => {
                        const opt = document.createElement('option');
                        opt.value = t;
                        opt.innerText = t;
                        if (t === currentTarget) opt.selected = true;
                        select.appendChild(opt);
                    });
                } catch(e) {
                    console.error("Failed to load targets", e);
                }
            }

            function switchTarget() {
                currentTarget = document.getElementById('targetSelect').value;
                refresh();
            }

            async function refresh() {
                try {
                    const res = await fetch(`/api/metrics?target=${encodeURIComponent(currentTarget)}`);
                    const data = await res.json();

                    document.getElementById('targetVal').innerText = data.latest_target;
                    document.getElementById('currentRtt').innerText = data.latest_rtt + ' ms';
                    document.getElementById('avgRtt').innerText = data.avg_rtt + ' ms';
                    document.getElementById('uptimeVal').innerText = data.uptime_pct + '%';

                    chart.data.labels = data.metrics.map(d => d.time);
                    chart.data.datasets[0].data = data.metrics.map(d => d.rtt);
                    chart.update();
                } catch (e) {
                    console.error("Dashboard sync error", e);
                }
            }

            loadTargets();
            setInterval(refresh, 2000);
            refresh();
        </script>
    </body>
    </html>
    """