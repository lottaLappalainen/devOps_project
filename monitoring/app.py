from flask import Flask, jsonify
import requests, time, os, docker

app = Flask(__name__)

URLS = {
    "api_v1": "http://api_v1:8199/status"
}

client = docker.from_env()
start_time = time.time()

# ---------------- BASIC METRICS ----------------

def uptime_seconds():
    return int(time.time() - start_time)

def host_cpu_usage():
    try:
        with open("/proc/stat") as f:
            cpu1 = list(map(int, f.readline().split()[1:]))
        time.sleep(0.5)
        with open("/proc/stat") as f:
            cpu2 = list(map(int, f.readline().split()[1:]))

        idle_delta = cpu2[3] - cpu1[3]
        total_delta = sum(cpu2) - sum(cpu1)
        return round(100.0 * (total_delta - idle_delta) / total_delta, 2)
    except:
        return 0.0

def log_size_bytes():
    try:
        r = requests.get("http://storage:8200/log", timeout=2)
        return len(r.text.encode("utf-8"))
    except:
        return 0

# ---------------- ADVANCED METRICS ----------------

response_times = []
last_seen = {}

def measure_api_response():
    try:
        start = time.time()
        requests.get(URLS["api_v1"], timeout=2)
        elapsed = round((time.time() - start) * 1000, 2)
        response_times.append(elapsed)
        if len(response_times) > 50:
            response_times.pop(0)
        last_seen["api_v1"] = int(time.time())
    except:
        pass

def docker_container_stats():
    stats = {}
    for c in client.containers.list():
        s = c.stats(stream=False)
        cpu_delta = s["cpu_stats"]["cpu_usage"]["total_usage"] - \
                    s["precpu_stats"]["cpu_usage"]["total_usage"]
        system_delta = s["cpu_stats"]["system_cpu_usage"] - \
                       s["precpu_stats"]["system_cpu_usage"]

        cpu_percent = 0
        if system_delta > 0:
            cpu_percent = round((cpu_delta / system_delta) * 100, 2)

        mem_usage = round(s["memory_stats"]["usage"] / (1024 * 1024), 2)
        mem_limit = round(s["memory_stats"]["limit"] / (1024 * 1024), 2)

        stats[c.name] = {
            "cpu_percent": cpu_percent,
            "memory_usage_mb": mem_usage,
            "memory_limit_mb": mem_limit
        }

        last_seen[c.name] = int(time.time())

    return stats

def response_time_stats():
    if not response_times:
        return {"min": 0, "max": 0, "avg": 0}

    return {
        "min": min(response_times),
        "max": max(response_times),
        "avg": round(sum(response_times) / len(response_times), 2)
    }

# ---------------- ROUTES ----------------

@app.route("/metrics")
def metrics():
    measure_api_response()

    return jsonify({
        "log_size_bytes": log_size_bytes(),
        "host_cpu_usage_percent": host_cpu_usage(),
        "monitor_uptime_seconds": uptime_seconds(),

        "docker_containers": docker_container_stats(),
        "api_response_times_ms": response_time_stats(),
        "last_seen_seconds": last_seen
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8400)
