def test_healthcheck_and_metrics_endpoints(client):
    health = client.get("/healthz")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "autorent_http_requests_total" in metrics.text
    assert "autorent_process_uptime_seconds" in metrics.text
