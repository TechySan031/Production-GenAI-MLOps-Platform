import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
    stages: [
        { duration: "20s", target: 5 },
        { duration: "40s", target: 5 },
        { duration: "20s", target: 0 },
    ],

    thresholds: {
        http_req_failed: ["rate<0.01"],
        http_req_duration: ["p(95)<5000"],
    },
};

const url = "http://localhost:8000/chat";

const payload = JSON.stringify({
    model: null,
    stream: false,
    temperature: 0.7,
    messages: [
        {
            role: "user",
            content: "Explain Azure Container Apps in one paragraph.",
        },
    ],
});

const params = {
    headers: {
        "Content-Type": "application/json",
    },
};

export default function () {
    const res = http.post(url, payload, params);

    check(res, {
        "status is 200": (r) => r.status === 200,

        "response has body": (r) => !!r.body,

        "response contains choices": (r) => {
            if (!r.body) return false;

            try {
                const data = JSON.parse(r.body);
                return (
                    data.choices &&
                    Array.isArray(data.choices) &&
                    data.choices.length > 0
                );
            } catch {
                return false;
            }
        },
    });

    sleep(1);
}