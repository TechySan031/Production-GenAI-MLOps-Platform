import axios, { AxiosError } from "axios";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "/api",
  timeout: 60000,
  headers: {
    "Content-Type": "application/json",
  },
});

export type ProviderId = "groq" | "openai" | "azure";

export type ChatMessage = {
  role: "system" | "user" | "assistant";
  content: string;
};

export type ChatRequest = {
  model: string;
  messages: ChatMessage[];
  temperature: number;
  max_tokens: number;
  stream: false;
};

export type UsageInfo = {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
};

export type ChatResponse = {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: Array<{
    index: number;
    message: ChatMessage;
    finish_reason: string;
  }>;
  usage: UsageInfo;
};

export type HealthResponse = {
  status: string;
  version: string;
  environment: string;
};

export type ReadinessResponse = {
  status: string;
  checks: Record<string, boolean>;
};

export type HealthSnapshot = {
  live: HealthResponse | null;
  ready: ReadinessResponse | null;
  latencyMs: number | null;
  checkedAt: string;
  error: string | null;
};

function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ detail?: string; error?: string }>;
    return (
      axiosError.response?.data?.detail ??
      axiosError.response?.data?.error ??
      axiosError.message
    );
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Unexpected request failure.";
}

export async function sendChat(request: ChatRequest): Promise<{
  response: ChatResponse;
  latencyMs: number;
}> {
  const startedAt = performance.now();
  try {
    const { data } = await api.post<ChatResponse>("/chat", request);
    return {
      response: data,
      latencyMs: Math.round(performance.now() - startedAt),
    };
  } catch (error) {
    throw new Error(getErrorMessage(error));
  }
}

export async function getHealthSnapshot(): Promise<HealthSnapshot> {
  const startedAt = performance.now();
  const checkedAt = new Date().toISOString();

  try {
    const [liveResult, readyResult] = await Promise.allSettled([
      api.get<HealthResponse>("/health"),
      api.get<ReadinessResponse>("/health/ready"),
    ]);

    const live = liveResult.status === "fulfilled" ? liveResult.value.data : null;
    const ready =
      readyResult.status === "fulfilled" ? readyResult.value.data : null;
    const error =
      liveResult.status === "rejected"
        ? getErrorMessage(liveResult.reason)
        : readyResult.status === "rejected"
          ? getErrorMessage(readyResult.reason)
          : null;

    return {
      live,
      ready,
      latencyMs: Math.round(performance.now() - startedAt),
      checkedAt,
      error,
    };
  } catch (error) {
    return {
      live: null,
      ready: null,
      latencyMs: Math.round(performance.now() - startedAt),
      checkedAt,
      error: getErrorMessage(error),
    };
  }
}
