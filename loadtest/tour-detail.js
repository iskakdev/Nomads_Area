import http from "k6/http";
import { check, sleep } from "k6";
import { Counter, Rate, Trend } from "k6/metrics";

const target = __ENV.TARGET_URL;
if (!target) {
  throw new Error("TARGET_URL is required");
}

const requests200 = new Counter("http_200");
const requests429 = new Counter("http_429");
const requests3xx = new Counter("http_3xx");
const requests5xx = new Counter("http_5xx");
const unexpected = new Counter("http_unexpected");
const successful = new Rate("successful_responses");
const responseSize = new Trend("response_size");

export const options = {
  discardResponseBodies: true,
  scenarios: {
    public_api: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: __ENV.WARMUP || "15s", target: Number(__ENV.VUS_LOW || 10) },
        { duration: __ENV.LOW_DURATION || "30s", target: Number(__ENV.VUS_LOW || 10) },
        { duration: __ENV.RAMP_DURATION || "15s", target: Number(__ENV.VUS_HIGH || 50) },
        { duration: __ENV.HIGH_DURATION || "60s", target: Number(__ENV.VUS_HIGH || 50) },
        { duration: "10s", target: 0 },
      ],
      gracefulRampDown: "10s",
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.001"],
    http_req_duration: ["p(95)<750", "p(99)<1500"],
    successful_responses: ["rate>0.999"],
    http_429: ["count==0"],
    http_5xx: ["count==0"],
    http_3xx: ["count==0"],
  },
};

export default function () {
  const separator = target.includes("?") ? "&" : "?";
  const requestUrl = __ENV.CACHE_BUST === "yes"
    ? `${target}${separator}load_test_vu=${__VU}&load_test_iteration=${__ITER}`
    : target;

  const response = http.get(requestUrl, {
    redirects: 0,
    headers: {
      Accept: "application/json",
      "User-Agent": "nomads-area-controlled-load-test/1.0",
    },
    tags: { endpoint: "tour-detail" },
  });

  responseSize.add(Number(response.headers["Content-Length"] || 0));
  successful.add(response.status === 200);

  if (response.status === 200) requests200.add(1);
  else if (response.status === 429) requests429.add(1);
  else if (response.status >= 300 && response.status < 400) requests3xx.add(1);
  else if (response.status >= 500) requests5xx.add(1);
  else unexpected.add(1);

  check(response, {
    "status is exactly 200": (r) => r.status === 200,
  });

  if (__ENV.ITERATION_PAUSE) {
    sleep(Number(__ENV.ITERATION_PAUSE));
  }
}
