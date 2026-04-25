from collections import defaultdict
from threading import Lock
from time import time

STARTED_AT = time()
_LOCK = Lock()
_REQUEST_COUNTER = defaultdict(int)
_REQUEST_DURATION_SUM_MS = defaultdict(float)
_REQUEST_DURATION_MAX_MS = defaultdict(float)


def _escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def record_request(method: str, path: str, status_code: int, duration_ms: float) -> None:
    key = (method.upper(), path, str(status_code))
    with _LOCK:
        _REQUEST_COUNTER[key] += 1
        _REQUEST_DURATION_SUM_MS[key] += duration_ms
        _REQUEST_DURATION_MAX_MS[key] = max(_REQUEST_DURATION_MAX_MS[key], duration_ms)


def render_metrics() -> str:
    lines = [
        "# HELP autorent_process_uptime_seconds Process uptime in seconds.",
        "# TYPE autorent_process_uptime_seconds gauge",
        f"autorent_process_uptime_seconds {time() - STARTED_AT:.2f}",
        "# HELP autorent_http_requests_total Total HTTP requests processed.",
        "# TYPE autorent_http_requests_total counter",
        "# HELP autorent_http_request_duration_ms_sum Total HTTP request duration in milliseconds.",
        "# TYPE autorent_http_request_duration_ms_sum counter",
        "# HELP autorent_http_request_duration_ms_max Maximum HTTP request duration in milliseconds.",
        "# TYPE autorent_http_request_duration_ms_max gauge",
    ]

    with _LOCK:
        keys = sorted(_REQUEST_COUNTER.keys())
        for method, path, status_code in keys:
            labels = (
                f'method="{_escape_label(method)}",'
                f'path="{_escape_label(path)}",'
                f'status_code="{_escape_label(status_code)}"'
            )
            lines.append(f"autorent_http_requests_total{{{labels}}} {_REQUEST_COUNTER[(method, path, status_code)]}")
            lines.append(
                "autorent_http_request_duration_ms_sum"
                f"{{{labels}}} {_REQUEST_DURATION_SUM_MS[(method, path, status_code)]:.2f}"
            )
            lines.append(
                "autorent_http_request_duration_ms_max"
                f"{{{labels}}} {_REQUEST_DURATION_MAX_MS[(method, path, status_code)]:.2f}"
            )

    lines.append("")
    return "\n".join(lines)
