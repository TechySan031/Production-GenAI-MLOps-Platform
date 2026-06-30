import { NextResponse } from "next/server";

const backendUrl = process.env.BACKEND_API_URL ?? "http://localhost:8000";

export async function POST(request: Request) {
  const body = (await request.json()) as unknown;
  const response = await fetch(`${backendUrl}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
    cache: "no-store",
  });

  const payload = (await response.json()) as unknown;
  return NextResponse.json(payload, { status: response.status });
}
