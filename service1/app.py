from flask import Flask, Response
import datetime, shutil, requests, os

app = Flask(__name__)

API_VERSION = os.getenv("API_VERSION", "v1")

STORAGE_URL = "http://storage:8200/log"
RESET_URL = "http://storage:8200/reset"
SERVICE2_URL = "http://service2:8300/status"


def iso_now_utc():
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def uptime_hours():
    try:
        with open("/proc/uptime") as f:
            return float(f.readline().split()[0]) / 3600.0
    except:
        return 0.0

def free_mb_root():
    total, used, free = shutil.disk_usage("/")
    return free // (1024 * 1024)

def make_record():
    return f"{iso_now_utc()}: version {API_VERSION}, uptime {uptime_hours():.2f} hours, free disk in root: {int(free_mb_root())} MBytes"

@app.route("/status", methods=["GET"])
def status():
    rec1 = make_record()

    try:
        requests.post(STORAGE_URL, data=rec1, headers={"Content-Type": "text/plain"}, timeout=2)
    except Exception as e:
        return Response(f"Storage POST error: {e}", status=500, mimetype="text/plain")

    try:
        r2 = requests.get(SERVICE2_URL, timeout=4)
        rec2 = r2.text
    except Exception as e:
        rec2 = f"{iso_now_utc()}: error contacting service2: {e}"

    combined = rec1 + "\n" + rec2
    return Response(combined, mimetype="text/plain")

@app.route("/log", methods=["GET"])
def log():
    try:
        r = requests.get("http://storage:8200/log", timeout=2)
        return Response(r.text, mimetype="text/plain")
    except Exception as e:
        return Response(f"Log error: {e}", status=500, mimetype="text/plain")

@app.route("/uptime", methods=["GET"])
def uptime():
    try:
        with open("/proc/uptime") as f:
            return f.readline().split()[0]
    except:
        return "0"

@app.route("/reset", methods=["POST"])
def reset():
    try:
        requests.post(RESET_URL, timeout=2)
        return "ok", 200
    except Exception as e:
        return f"reset error: {e}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8199)
