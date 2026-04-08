async function updateMetrics() {
    try {
        const metricsResp = await fetch("/monitoring/metrics");
        let metrics = { error: "no data" };
        if (metricsResp.ok) {
            metrics = await metricsResp.json();
        }

        const logResp = await fetch("/api/log");
        const logText = logResp.ok ? await logResp.text() : "log unavailable";

        if (!metrics.error) {
            let dockerStats = "";
            for (const [name, data] of Object.entries(metrics.docker_containers)) {
                dockerStats +=
                    `${name}:\n` +
                    `  CPU: ${data.cpu_percent}%\n` +
                    `  MEM: ${data.memory_usage_mb}MB / ${data.memory_limit_mb}MB\n\n`;
            }

            document.getElementById("statusBox").textContent =
                `Log size: ${metrics.log_size_bytes} bytes\n` +
                `Host CPU: ${metrics.host_cpu_usage_percent}%\n` +
                `Monitor uptime: ${metrics.monitor_uptime_seconds}s\n\n` +
                `API Response Times (ms):\n` +
                `  Min: ${metrics.api_response_times_ms.min}\n` +
                `  Max: ${metrics.api_response_times_ms.max}\n` +
                `  Avg: ${metrics.api_response_times_ms.avg}\n\n` +
                `Docker Container Stats:\n${dockerStats}`;
        }

        document.getElementById("logBox").textContent = logText;

    } catch (err) {
        document.getElementById("statusBox").textContent = "Error contacting monitoring service";
        document.getElementById("logBox").textContent = "";
    }
}

setInterval(updateMetrics, 2000);
updateMetrics();
