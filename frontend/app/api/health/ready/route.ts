import { NextResponse } from "next/server";

const backendUrl = process.env.BACKEND_API_URL ?? "http://localhost:8000";

export async function GET() {
  const response = await fetch(`${backendUrl}/health/ready`, {
    cache: "no-store",
  });
  const payload = (await response.json()) as unknown;

  return NextResponse.json(payload, { status: response.status });
}
