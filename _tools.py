"""The agent's HANDS: four READ-ONLY ops tools + their function-calling schemas.

Rule for this whole module: every tool is read-only. It can look, it cannot change anything.
That is the single most important safety decision - the write actions and approval gates come
in the Safety episode. The LLM never runs these; it only *asks* for one, and our code runs it.

The tools read from sample_ops/ so the episode runs offline with a realistic incident baked in
(checkout crashed -> nginx 502s). To point them at real infrastructure, replace the bodies with
real read-only calls (kubectl get, docker ps, your metrics API, requests.get) - the schemas stay
the same.
"""
import os
import json

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "sample_ops")


def _load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


def get_service_status(service):
    """Current status of one service: replicas, image, last event."""
    services = _load("services.json")
    s = services.get(service)
    if not s:
        return {"error": f"unknown service '{service}'", "known_services": list(services)}
    return {"service": service, **s}


def tail_logs(service, lines=20):
    """Last N log lines for a service (read-only, like `tail -n`)."""
    path = os.path.join(DATA, "logs", f"{service}.log")
    if not os.path.exists(path):
        return {"error": f"no log file for '{service}'"}
    with open(path, encoding="utf-8") as f:
        all_lines = f.read().splitlines()
    return {"service": service, "lines": all_lines[-int(lines):]}


def get_metrics(service):
    """Current metrics for a service: cpu, mem, error rate, p95, throughput."""
    metrics = _load("metrics.json")
    if service not in metrics:
        return {"error": f"no metrics for '{service}'", "known_services": list(metrics)}
    return {"service": service, **metrics[service]}


def http_check(url):
    """Read-only HTTP GET health check -> status code. SIMULATED here over sample_ops data.
    For real use, replace this body with: requests.get(url, timeout=5).status_code."""
    routes = _load("routes.json")
    services = _load("services.json")
    match = None
    for path in sorted(routes, key=len, reverse=True):   # longest path prefix wins
        if path in url:
            match = routes[path]
            break
    if match is None:
        return {"url": url, "error": "no route matches this URL in routes.json"}
    up = services.get(match, {}).get("status") == "running"
    if up:
        return {"url": url, "status_code": 200, "via_service": match}
    # nginx proxies to a dead upstream -> 502 Bad Gateway
    return {"url": url, "status_code": 502, "via_service": match,
            "note": f"upstream '{match}' is not running"}


# ---- function-calling schemas (OpenAI/Groq format) -------------------------------------
TOOLS = [
    {"type": "function", "function": {
        "name": "get_service_status",
        "description": "Read the current status of a service (replicas, image, last event). Read-only.",
        "parameters": {"type": "object", "properties": {
            "service": {"type": "string", "description": "service name, e.g. 'checkout'"}},
            "required": ["service"]}}},
    {"type": "function", "function": {
        "name": "tail_logs",
        "description": "Return the last N log lines for a service. Read-only.",
        "parameters": {"type": "object", "properties": {
            "service": {"type": "string"},
            "lines": {"type": "integer", "description": "how many lines (default 20)"}},
            "required": ["service"]}}},
    {"type": "function", "function": {
        "name": "get_metrics",
        "description": "Return current metrics (cpu, mem, error_rate, p95) for a service. Read-only.",
        "parameters": {"type": "object", "properties": {
            "service": {"type": "string"}},
            "required": ["service"]}}},
    {"type": "function", "function": {
        "name": "http_check",
        "description": "Do a read-only HTTP GET health check of a URL and return the status code.",
        "parameters": {"type": "object", "properties": {
            "url": {"type": "string", "description": "full URL, e.g. 'https://shop.example.com/api/checkout'"}},
            "required": ["url"]}}},
]

IMPLS = {
    "get_service_status": get_service_status,
    "tail_logs": tail_logs,
    "get_metrics": get_metrics,
    "http_check": http_check,
}


def dispatch(name, args):
    """Run the tool the model asked for. Only names in IMPLS can ever run."""
    fn = IMPLS.get(name)
    if fn is None:
        return {"error": f"unknown tool '{name}'"}
    try:
        return fn(**args)
    except TypeError as e:
        return {"error": f"bad arguments for '{name}': {e}"}
