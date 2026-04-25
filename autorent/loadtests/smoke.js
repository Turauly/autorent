import http from "k6/http";
import { check, sleep } from "k6";

const BASE_URL = __ENV.BASE_URL || "http://127.0.0.1:8000";

export const options = {
  vus: 10,
  duration: "30s",
  thresholds: {
    http_req_failed: ["rate<0.05"],
    http_req_duration: ["p(95)<800"]
  }
};

export default function () {
  const health = http.get(`${BASE_URL}/healthz`);
  check(health, {
    "health check is 200": (r) => r.status === 200
  });

  const cars = http.get(`${BASE_URL}/cars/?page=1&limit=5`);
  check(cars, {
    "cars listing is 200": (r) => r.status === 200,
    "cars listing contains paging": (r) => r.json("page") === 1
  });

  const metrics = http.get(`${BASE_URL}/metrics`);
  check(metrics, {
    "metrics endpoint is 200": (r) => r.status === 200,
    "metrics contain request counter": (r) => r.body.includes("autorent_http_requests_total")
  });

  sleep(1);
}
