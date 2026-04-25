import http from "k6/http";
import { check, group, sleep } from "k6";

const BASE_URL = __ENV.BASE_URL || "http://127.0.0.1:8000";

export const options = {
  scenarios: {
    browse_fleet: {
      executor: "ramping-vus",
      startVUs: 1,
      stages: [
        { duration: "15s", target: 5 },
        { duration: "30s", target: 20 },
        { duration: "15s", target: 0 }
      ],
      gracefulRampDown: "5s"
    }
  },
  thresholds: {
    http_req_failed: ["rate<0.1"],
    http_req_duration: ["p(95)<1200"]
  }
};

export default function () {
  group("public browsing", () => {
    const cars = http.get(
      `${BASE_URL}/cars/?page=1&limit=8&sort_by=price_per_day&sort_order=asc`
    );
    check(cars, {
      "cars returns 200": (r) => r.status === 200,
      "cars payload contains items": (r) => Array.isArray(r.json("items"))
    });

    const electricCars = http.get(`${BASE_URL}/cars/?is_electric=true&page=1&limit=4`);
    check(electricCars, {
      "electric filter returns 200": (r) => r.status === 200
    });
  });

  group("invalid auth protection", () => {
    const payload = "username=invalid@example.com&password=wrong-password";
    const response = http.post(`${BASE_URL}/auth/login`, payload, {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded"
      }
    });
    check(response, {
      "invalid login is rejected": (r) => r.status === 401
    });
  });

  sleep(1);
}
