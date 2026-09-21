import urllib.request
import json

# Paste your webhook URL between the quotes on this line:
WEBHOOK_URL = "https://discord.com/api/webhooks/your/actual/url/here"

def send_alert(target: str, reason: str, details: str):
    message = {
        "content": f"🚨 **Network Alert Triggered!**",
        "embeds": [{
            "title": f"Host Issue: {target}",
            "color": 15158332, # Red
            "fields": [
                {"name": "Trigger Reason", "value": reason, "inline": True},
                {"name": "Details", "value": details, "inline": True}
            ]
        }]
    }

    if not WEBHOOK_URL:
        print(f"\n[ALERT DISPATCHED LOCALLY] Host: {target} | Issue: {reason} | {details}\n")
        return

    try:
        req = urllib.request.Request(
            WEBHOOK_URL,
            data=json.dumps(message).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "NetMonitor/1.0"}
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            pass
    except Exception as e:
        print(f"[-] Failed to deliver webhook alert: {e}")