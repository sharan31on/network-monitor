import sqlite3
from datetime import datetime

DB_FILE = "metrics.db"

def init_db():
    """Create the checks table if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monitor_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            target TEXT NOT NULL,
            ping_rtt REAL,
            packet_loss REAL,
            port_443_status TEXT,
            health_status TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_metric(target: str, rtt: float, loss: float, port_status: str, health: str):
    """Insert a single check record into SQLite."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO monitor_logs (timestamp, target, ping_rtt, packet_loss, port_443_status, health_status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        target,
        rtt,
        loss,
        port_status,
        health
    ))
    conn.commit()
    conn.close()

def get_target_summary(target: str):
    """Fetch uptime, average latency, and total checks for a target."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total_checks,
            AVG(ping_rtt) as avg_rtt,
            MIN(ping_rtt) as min_rtt,
            MAX(ping_rtt) as max_rtt,
            SUM(CASE WHEN health_status = 'HEALTHY' THEN 1 ELSE 0 END) as healthy_checks
        FROM monitor_logs
        WHERE target = ?
    """, (target,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row and row[0] > 0:
        total = row[0]
        uptime_pct = (row[4] / total) * 100.0
        return {
            "total_checks": total,
            "avg_rtt": round(row[1], 2) if row[1] else 0.0,
            "min_rtt": round(row[2], 2) if row[2] else 0.0,
            "max_rtt": round(row[3], 2) if row[3] else 0.0,
            "uptime_pct": round(uptime_pct, 2)
        }
    return None

if __name__ == "__main__":
    init_db()
    print("[+] Database initialized successfully.")