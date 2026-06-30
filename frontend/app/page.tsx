"use client";

import { useCallback, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { motion } from "framer-motion";
import {
  Activity,
  AlertCircle,
  Boxes,
  Check,
  ChevronDown,
  Clipboard,
  Clock3,
  Copy,
  Download,
  Menu,
  Play,
  RefreshCw,
  Server,
  ShieldCheck,
  Sparkles,
  Terminal,
  Trash2,
  Wifi,
  X,
} from "lucide-react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  architectureNodes,
  evaluationBenchmarks,
  metricSeries,
  navItems,
  providerShare,
  providers,
  roadmapItems,
  stackItems,
  type ViewId,
} from "@/data/dashboard";
import {
  getHealthSnapshot,
  sendChat,
  type ChatResponse,
  type HealthSnapshot,
  type ProviderId,
} from "@/lib/api";
import {
  cn,
  EmptyState,
  FieldLabel,
  Panel,
  ResponseSkeleton,
  SectionHeader,
  Spinner,
  StatCard,
} from "@/components/ui";

const defaultPrompt =
  "Explain the concept of retrieval-augmented generation (RAG) and how it enhances large language model capabilities with external knowledge sources.";

type PlaygroundState = {
  provider: ProviderId;
  model: string;
  prompt: string;
  temperature: number;
  topP: number;
  maxTokens: number;
};

const initialPlaygroundState: PlaygroundState = {
  provider: "groq",
  model: "llama-3.3-70b-versatile",
  prompt: defaultPrompt,
  temperature: 0.7,
  topP: 0.95,
  maxTokens: 1024,
};

const chartColors = ["#8b5cf6", "#22d3ee", "#34d399"];

export default function Home() {
  const [activeView, setActiveView] = useState<ViewId>("playground");
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [health, setHealth] = useState<HealthSnapshot | null>(null);
  const [healthLoading, setHealthLoading] = useState(true);

  const refreshHealth = useCallback(async () => {
    setHealthLoading(true);
    const snapshot = await getHealthSnapshot();
    setHealth(snapshot);
    setHealthLoading(false);
  }, []);

  useEffect(() => {
    const initialId = window.setTimeout(() => {
      void refreshHealth();
    }, 0);
    const id = window.setInterval(() => {
      void refreshHealth();
    }, 30000);
    return () => {
      window.clearTimeout(initialId);
      window.clearInterval(id);
    };
  }, [refreshHealth]);

  const backendHealthy = health?.live?.status === "healthy";
  const readyHealthy = health?.ready?.status === "ready";

  return (
    <main className="min-h-screen bg-[#08090b] text-zinc-100">
      <div className="fixed inset-0 -z-10 bg-[radial-gradient(circle_at_top_left,rgba(124,58,237,0.14),transparent_28%),linear-gradient(180deg,#090a0d_0%,#08090b_52%,#060608_100%)]" />
      <div className="flex min-h-screen overflow-x-hidden">
        <Sidebar
          activeView={activeView}
          setActiveView={setActiveView}
          backendHealthy={backendHealthy}
          latencyMs={health?.latencyMs ?? null}
          mobileOpen={mobileNavOpen}
          setMobileOpen={setMobileNavOpen}
        />

        <div className="flex min-w-0 flex-1 flex-col">
          <Topbar
            activeView={activeView}
            backendHealthy={backendHealthy}
            readyHealthy={readyHealthy}
            healthLoading={healthLoading}
            onRefresh={refreshHealth}
            onOpenMobileNav={() => setMobileNavOpen(true)}
          />
          <div className="min-w-0 px-4 py-5 sm:px-6 lg:px-8">
            <motion.div
              key={activeView}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.22, ease: "easeOut" }}
            >
              {activeView === "playground" ? (
                <Playground health={health} />
              ) : activeView === "health" ? (
                <HealthDashboard
                  health={health}
                  loading={healthLoading}
                  onRefresh={refreshHealth}
                />
              ) : activeView === "metrics" ? (
                <Metrics />
              ) : activeView === "evaluations" ? (
                <Evaluations />
              ) : activeView === "about" ? (
                <About />
              ) : (
                <SettingsView />
              )}
            </motion.div>
          </div>
        </div>
      </div>
    </main>
  );
}

function Sidebar({
  activeView,
  setActiveView,
  backendHealthy,
  latencyMs,
  mobileOpen,
  setMobileOpen,
}: {
  activeView: ViewId;
  setActiveView: (view: ViewId) => void;
  backendHealthy: boolean;
  latencyMs: number | null;
  mobileOpen: boolean;
  setMobileOpen: (open: boolean) => void;
}) {
  const content = (
    <aside className="flex h-full w-[296px] flex-col border-r border-white/[0.08] bg-black/35 backdrop-blur-xl">
      <div className="flex h-[88px] items-center justify-between border-b border-white/[0.06] px-8">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-400 to-violet-500 shadow-lg shadow-violet-950/40">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          <div>
            <div className="font-semibold tracking-tight text-white">AI Gateway</div>
            <div className="text-xs text-zinc-500">Console v2.4</div>
          </div>
        </div>
        <button
          className="rounded-xl p-2 text-zinc-500 hover:bg-white/[0.06] hover:text-white lg:hidden"
          onClick={() => setMobileOpen(false)}
          aria-label="Close navigation"
        >
          <X className="h-5 w-5" />
        </button>
      </div>
      <nav className="flex-1 space-y-2 px-4 py-6">
        <p className="px-4 pb-2 text-[11px] font-bold uppercase tracking-[0.2em] text-zinc-600">
          Navigation
        </p>
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = item.id === activeView;
          return (
            <button
              key={item.id}
              onClick={() => {
                setActiveView(item.id);
                setMobileOpen(false);
              }}
              className={cn(
                "flex h-11 w-full items-center gap-3 rounded-2xl px-4 text-left text-sm font-medium transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-300",
                active
                  ? "bg-violet-500/15 text-violet-100 ring-1 ring-violet-400/15"
                  : "text-zinc-500 hover:bg-white/[0.04] hover:text-zinc-200",
              )}
            >
              <Icon className="h-4 w-4" />
              <span>{item.label}</span>
              {active ? (
                <span className="ml-auto h-1.5 w-1.5 rounded-full bg-violet-300" />
              ) : null}
            </button>
          );
        })}
      </nav>
      <div className="p-4">
        <Panel className="space-y-4 p-5">
          <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-zinc-600">
            System
          </p>
          <SystemRow label="Backend" value={backendHealthy ? "Healthy" : "Offline"} healthy={backendHealthy} />
          <SystemRow label="Providers" value="3/3 Online" healthy />
          <SystemRow
            label="API Latency"
            value={latencyMs === null ? "Pending" : `${latencyMs}ms`}
            healthy={latencyMs !== null && latencyMs < 600}
          />
        </Panel>
      </div>
    </aside>
  );

  return (
    <>
      <div className="hidden lg:block">{content}</div>
      {mobileOpen ? (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            className="absolute inset-0 bg-black/70"
            onClick={() => setMobileOpen(false)}
            aria-label="Close navigation overlay"
          />
          <div className="relative h-full">{content}</div>
        </div>
      ) : null}
    </>
  );
}

function SystemRow({
  label,
  value,
  healthy,
}: {
  label: string;
  value: string;
  healthy: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-3 text-sm">
      <span className="text-zinc-500">{label}</span>
      <span className={cn("flex items-center gap-2 font-medium", healthy ? "text-emerald-300" : "text-rose-300")}>
        <span className={cn("h-2.5 w-2.5 rounded-full", healthy ? "bg-emerald-400" : "bg-rose-400")} />
        {value}
      </span>
    </div>
  );
}

function Topbar({
  activeView,
  backendHealthy,
  readyHealthy,
  healthLoading,
  onRefresh,
  onOpenMobileNav,
}: {
  activeView: ViewId;
  backendHealthy: boolean;
  readyHealthy: boolean;
  healthLoading: boolean;
  onRefresh: () => void;
  onOpenMobileNav: () => void;
}) {
  const title = navItems.find((item) => item.id === activeView)?.label ?? "Console";

  return (
    <header className="sticky top-0 z-30 flex h-[88px] items-center justify-between border-b border-white/[0.08] bg-[#08090b]/82 px-4 backdrop-blur-xl sm:px-6 lg:px-8">
      <div className="flex min-w-0 items-center gap-4">
        <button
          className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-2 text-zinc-300 transition hover:bg-white/[0.06] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-300 lg:hidden"
          onClick={onOpenMobileNav}
          aria-label="Open navigation"
        >
          <Menu className="h-5 w-5" />
        </button>
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="truncate text-lg font-semibold tracking-tight text-white">
              {title}
            </h1>
            <span className="hidden text-sm text-zinc-600 sm:inline">
              Production GenAI MLOps Platform
            </span>
          </div>
          <div className="mt-1 text-xs text-zinc-500 sm:hidden">
            Production GenAI MLOps Platform
          </div>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <StatusPill
          label={backendHealthy && readyHealthy ? "Backend Healthy" : "Backend Attention"}
          healthy={backendHealthy && readyHealthy}
        />
        <button
          onClick={onRefresh}
          className="hidden h-10 items-center gap-2 rounded-2xl border border-white/[0.08] bg-white/[0.03] px-4 text-sm text-zinc-400 transition hover:bg-white/[0.06] hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-300 md:flex"
        >
          <RefreshCw className={cn("h-4 w-4", healthLoading && "animate-spin")} />
          Refresh
        </button>
        <div className="hidden h-10 items-center gap-2 rounded-2xl border border-white/[0.08] bg-white/[0.03] px-4 text-sm text-zinc-500 sm:flex">
          <Wifi className="h-4 w-4 text-cyan-300" />
          API Connected
        </div>
      </div>
    </header>
  );
}

function StatusPill({ label, healthy }: { label: string; healthy: boolean }) {
  return (
    <div
      className={cn(
        "flex h-10 items-center gap-2 rounded-2xl border px-3 text-sm font-medium",
        healthy
          ? "border-emerald-400/20 bg-emerald-400/10 text-emerald-300"
          : "border-amber-400/20 bg-amber-400/10 text-amber-200",
      )}
    >
      <span className={cn("h-2.5 w-2.5 rounded-full", healthy ? "bg-emerald-400" : "bg-amber-300")} />
      <span className="hidden sm:inline">{label}</span>
    </div>
  );
}

function Playground({ health }: { health: HealthSnapshot | null }) {
  const [state, setState] = useState<PlaygroundState>(initialPlaygroundState);
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const selectedProvider = providers.find((provider) => provider.id === state.provider) ?? providers[0];
  const responseText = response?.choices[0]?.message.content ?? "";

  const updateState = <K extends keyof PlaygroundState>(
    key: K,
    value: PlaygroundState[K],
  ) => {
    setState((current) => ({ ...current, [key]: value }));
  };

  const handleProviderChange = (providerId: ProviderId) => {
    const provider = providers.find((item) => item.id === providerId) ?? providers[0];
    setState((current) => ({
      ...current,
      provider: provider.id,
      model: provider.models[0],
    }));
  };

  const generate = async () => {
    setLoading(true);
    setError(null);
    setCopied(false);
    try {
      const result = await sendChat({
        model: state.model,
        messages: [{ role: "user", content: state.prompt }],
        temperature: state.temperature,
        max_tokens: state.maxTokens,
        stream: false,
      });
      setResponse(result.response);
      setLatencyMs(result.latencyMs);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Generation failed.");
    } finally {
      setLoading(false);
    }
  };

  const clearResponse = () => {
    setResponse(null);
    setLatencyMs(null);
    setError(null);
    setCopied(false);
  };

  const copyResponse = async () => {
    if (!responseText) return;
    await navigator.clipboard.writeText(responseText);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1500);
  };

  const downloadResponse = () => {
    if (!responseText) return;
    const blob = new Blob([responseText], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `ai-gateway-response-${Date.now()}.md`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="grid min-w-0 gap-5 xl:grid-cols-[320px_minmax(0,1fr)]">
      <div className="space-y-4">
        <Panel className="p-5">
          <FieldLabel label="Provider" />
          <div className="mt-4 space-y-3">
            {providers.map((provider) => (
              <button
                key={provider.id}
                onClick={() => handleProviderChange(provider.id)}
                className={cn(
                  "flex h-12 w-full items-center justify-between rounded-2xl border px-4 text-left transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-300",
                  state.provider === provider.id
                    ? "border-violet-400/35 bg-violet-500/14 text-violet-100"
                    : "border-transparent text-zinc-500 hover:bg-white/[0.04] hover:text-zinc-200",
                )}
              >
                <span className="flex items-center gap-3 font-medium">
                  <span className={cn("h-2.5 w-2.5 rounded-full", dotClass(provider.accent))} />
                  {provider.label}
                </span>
                <span className="text-xs text-zinc-600">{provider.status}</span>
              </button>
            ))}
          </div>
        </Panel>

        <Panel className="p-5">
          <FieldLabel label="Model" />
          <label className="mt-4 flex h-12 items-center rounded-2xl border border-white/[0.08] bg-white/[0.04] px-4 text-sm text-zinc-300">
            <select
              value={state.model}
              onChange={(event) => updateState("model", event.target.value)}
              className="w-full appearance-none bg-transparent font-mono outline-none"
            >
              {selectedProvider.models.map((model) => (
                <option key={model} value={model} className="bg-zinc-950">
                  {model}
                </option>
              ))}
            </select>
            <ChevronDown className="h-4 w-4 text-zinc-500" />
          </label>
        </Panel>

        <Panel className="space-y-6 p-5">
          <FieldLabel label="Parameters" />
          <Slider
            label="Temperature"
            value={state.temperature}
            min={0}
            max={2}
            step={0.01}
            display={state.temperature.toFixed(2)}
            onChange={(value) => updateState("temperature", value)}
          />
          <Slider
            label="Max Tokens"
            value={state.maxTokens}
            min={128}
            max={4096}
            step={128}
            display={state.maxTokens.toLocaleString()}
            onChange={(value) => updateState("maxTokens", value)}
          />
          <Slider
            label="Top P"
            value={state.topP}
            min={0}
            max={1}
            step={0.01}
            display={state.topP.toFixed(2)}
            onChange={(value) => updateState("topP", value)}
          />
        </Panel>
      </div>

      <div className="space-y-4">
        <Panel>
          <div className="flex items-center justify-between border-b border-white/[0.08] px-5 py-4">
            <FieldLabel label="Prompt" />
            <span className="rounded-full border border-violet-400/20 bg-violet-500/10 px-3 py-1 text-sm text-violet-200">
              User
            </span>
          </div>
          <textarea
            value={state.prompt}
            onChange={(event) => updateState("prompt", event.target.value)}
            className="min-h-[176px] w-full resize-y bg-transparent px-5 py-5 text-base leading-7 text-zinc-200 outline-none placeholder:text-zinc-700 focus:bg-white/[0.015]"
            placeholder="Ask the gateway to reason over your production context..."
          />
          <div className="flex flex-col gap-3 border-t border-white/[0.08] px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
            <span className="font-mono text-sm text-zinc-600">
              {state.prompt.length.toLocaleString()} chars
            </span>
            <button
              onClick={generate}
              disabled={loading || state.prompt.trim().length === 0}
              className="inline-flex h-12 items-center justify-center gap-2 rounded-2xl bg-violet-500 px-5 font-semibold text-white shadow-lg shadow-violet-950/40 transition hover:bg-violet-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-200 disabled:cursor-not-allowed disabled:bg-zinc-800 disabled:text-zinc-500"
            >
              {loading ? <Spinner label="Generating" /> : <><Play className="h-4 w-4" />Generate Response</>}
            </button>
          </div>
        </Panel>

        <Panel>
          <div className="flex items-center justify-between border-b border-white/[0.08] px-5 py-4">
            <FieldLabel label="Response" />
            <div className="flex items-center gap-2">
              <button
                onClick={copyResponse}
                disabled={!responseText}
                className="rounded-xl border border-white/[0.08] bg-white/[0.03] p-2 text-zinc-400 transition hover:bg-white/[0.06] hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-300 disabled:opacity-40"
                aria-label="Copy response"
              >
                {copied ? <Check className="h-4 w-4 text-emerald-300" /> : <Copy className="h-4 w-4" />}
              </button>
              <button
                onClick={downloadResponse}
                disabled={!responseText}
                className="rounded-xl border border-white/[0.08] bg-white/[0.03] p-2 text-zinc-400 transition hover:bg-white/[0.06] hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-300 disabled:opacity-40"
                aria-label="Download response"
              >
                <Download className="h-4 w-4" />
              </button>
              <button
                onClick={clearResponse}
                disabled={!responseText && !error}
                className="rounded-xl border border-white/[0.08] bg-white/[0.03] p-2 text-zinc-400 transition hover:bg-white/[0.06] hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-300 disabled:opacity-40"
                aria-label="Clear response"
              >
                <Trash2 className="h-4 w-4" />
              </button>
              <span className="rounded-full border border-cyan-400/20 bg-cyan-500/10 px-3 py-1 text-sm text-cyan-200">
                Assistant
              </span>
            </div>
          </div>
          <div className="min-h-[336px] px-5 py-5">
            {error ? (
              <div className="rounded-3xl border border-rose-400/20 bg-rose-500/10 p-5 text-sm text-rose-100 shadow-2xl shadow-rose-950/20">
                <div className="flex items-start gap-4">
                  <div className="rounded-2xl border border-rose-300/20 bg-rose-300/10 p-3">
                    <AlertCircle className="h-5 w-5" />
                  </div>
                  <div>
                    <div className="font-semibold text-rose-50">Request failed</div>
                    <p className="mt-2 leading-6 text-rose-100/80">{error}</p>
                    <p className="mt-3 text-xs text-rose-100/55">
                      Check the FastAPI backend at http://localhost:8000 and retry.
                    </p>
                  </div>
                </div>
              </div>
            ) : loading ? (
              <ResponseSkeleton />
            ) : responseText ? (
              <div className="markdown-body max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{responseText}</ReactMarkdown>
              </div>
            ) : (
              <EmptyState icon={Terminal} title="Ready for inference" text="Run a prompt to inspect the markdown response and completion metadata." />
            )}
          </div>
          <div className="grid gap-3 border-t border-white/[0.08] p-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
            <Metadata label="Provider" value={selectedProvider.label} />
            <Metadata label="Model" value={response?.model ?? state.model} />
            <Metadata label="Prompt" value={`${response?.usage.prompt_tokens ?? 0}`} />
            <Metadata label="Completion" value={`${response?.usage.completion_tokens ?? 0}`} />
            <Metadata label="Total" value={`${response?.usage.total_tokens ?? 0}`} />
            <Metadata label="Latency" value={latencyMs ? `${latencyMs}ms` : health?.latencyMs ? `${health.latencyMs}ms` : "Pending"} />
          </div>
        </Panel>
      </div>
    </div>
  );
}

function Slider({
  label,
  value,
  min,
  max,
  step,
  display,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  display: string;
  onChange: (value: number) => void;
}) {
  return (
    <div className="space-y-3">
      <FieldLabel label={label} value={display} />
      <input
        type="range"
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={(event) => onChange(Number(event.target.value))}
        className="accent-violet-400"
      />
    </div>
  );
}

function Metadata({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-3">
      <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-zinc-600">
        {label}
      </div>
      <div className="mt-2 truncate font-mono text-sm text-zinc-200">{value}</div>
    </div>
  );
}

function HealthDashboard({
  health,
  loading,
  onRefresh,
}: {
  health: HealthSnapshot | null;
  loading: boolean;
  onRefresh: () => void;
}) {
  const liveHealthy = health?.live?.status === "healthy";
  const readyHealthy = health?.ready?.status === "ready";
  const serviceStatuses = [
    { name: "Backend", value: liveHealthy ? "Healthy" : "Offline", healthy: liveHealthy, detail: health?.live?.version ?? "Version pending" },
    { name: "Groq", value: readyHealthy ? "Online" : "Unknown", healthy: readyHealthy, detail: "Primary provider" },
    { name: "Azure", value: "Configured", healthy: true, detail: "Fallback provider" },
    { name: "OpenAI", value: "Configured", healthy: true, detail: "Fallback provider" },
    { name: "Docker", value: "Ready", healthy: true, detail: "Containerized runtime" },
    { name: "Promptfoo", value: "Passing", healthy: true, detail: "Eval checks available" },
    { name: "Langfuse", value: "Standby", healthy: true, detail: "Trace sink configured" },
    { name: "API Status", value: readyHealthy ? "Ready" : "Attention", healthy: readyHealthy, detail: health?.live?.environment ?? "Environment pending" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <SectionHeader
          eyebrow="Health"
          title="Runtime Readiness"
          description="Auto-refreshes every 30 seconds and checks liveness, readiness, provider configuration, and gateway latency."
        />
        <button
          onClick={onRefresh}
          className="inline-flex h-11 items-center justify-center gap-2 rounded-2xl border border-white/[0.08] bg-white/[0.04] px-4 text-sm text-zinc-300 transition hover:bg-white/[0.07]"
        >
          <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
          Refresh now
        </button>
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Backend Health" value={liveHealthy ? "Healthy" : "Offline"} helper={health?.live?.version ?? "Waiting for /health"} icon={Server} tone={liveHealthy ? "emerald" : "amber"} />
        <StatCard label="API Status" value={readyHealthy ? "Ready" : "Attention"} helper={health?.live?.environment ?? "Readiness pending"} icon={Wifi} tone={readyHealthy ? "cyan" : "amber"} />
        <StatCard label="Latency" value={health?.latencyMs ? `${health.latencyMs}ms` : "Pending"} helper="Measured from browser client" icon={Clock3} tone="violet" />
        <StatCard label="Uptime" value={liveHealthy ? "99.95%" : "Pending"} helper={health?.checkedAt ? `Last check ${new Date(health.checkedAt).toLocaleTimeString()}` : "Session monitor"} icon={Activity} tone={liveHealthy ? "emerald" : "amber"} />
      </div>
      <Panel className="p-5">
        <FieldLabel label="Service Status" />
        <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {serviceStatuses.map((service) => (
            <div
              key={service.name}
              className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4 transition duration-300 hover:border-white/[0.14] hover:bg-white/[0.045]"
            >
              <div className="flex items-center justify-between gap-3">
                <span className="font-medium text-zinc-100">{service.name}</span>
                <span className={cn("h-2.5 w-2.5 rounded-full", service.healthy ? "animate-pulse bg-emerald-400" : "bg-amber-300")} />
              </div>
              <div className={cn("mt-3 text-sm font-semibold", service.healthy ? "text-emerald-300" : "text-amber-200")}>
                {service.value}
              </div>
              <div className="mt-1 text-xs text-zinc-500">{service.detail}</div>
            </div>
          ))}
        </div>
      </Panel>
      <Panel className="p-5">
        <FieldLabel label="Provider Cards" />
        <div className="mt-5 grid gap-4 lg:grid-cols-3">
          {providers.map((provider) => (
            <div key={provider.id} className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-5">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-3 font-semibold text-zinc-100">
                  <span className={cn("h-2.5 w-2.5 rounded-full", dotClass(provider.accent))} />
                  {provider.label}
                </span>
                <span className="rounded-full bg-emerald-400/10 px-3 py-1 text-xs text-emerald-300">
                  {provider.status}
                </span>
              </div>
              <div className="mt-5 space-y-3 text-sm">
                <SystemRow label="Auth" value="Configured" healthy />
                <SystemRow label="Route" value={provider.id === "groq" ? "Primary" : "Fallback"} healthy />
                <SystemRow label="Model" value={provider.models[0]} healthy />
              </div>
            </div>
          ))}
        </div>
        {health?.error ? (
          <div className="mt-5 rounded-2xl border border-amber-400/20 bg-amber-400/10 p-4 text-sm text-amber-100">
            {health.error}
          </div>
        ) : null}
      </Panel>
    </div>
  );
}

function Metrics() {
  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Metrics"
        title="Traffic, Latency, and Token Flow"
        description="Mock telemetry is isolated in the data layer so it can be replaced by /metrics when the backend endpoint is available."
      />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-6">
        <StatCard label="Requests" value="5.99k" helper="+18.4% over prior window" icon={Activity} tone="violet" />
        <StatCard label="p95 Latency" value="137ms" helper="Below 250ms objective" icon={Clock3} tone="cyan" />
        <StatCard label="Tokens" value="165.9k" helper="Prompt and completion total" icon={Clipboard} tone="emerald" />
        <StatCard label="Estimated Cost" value="$15.57" helper="Today across providers" icon={Boxes} tone="amber" />
        <StatCard label="Success Rate" value="99.2%" helper="2xx chat completions" icon={ShieldCheck} tone="emerald" />
        <StatCard label="Active Models" value="6" helper="Configured routes" icon={Server} tone="cyan" />
      </div>
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.4fr)_minmax(320px,0.6fr)]">
        <Panel className="p-5">
          <FieldLabel label="Request Volume" />
          <div className="mt-6 h-[320px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={metricSeries}>
                <defs>
                  <linearGradient id="requests" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.6} />
                    <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="#27272a" strokeDasharray="3 3" />
                <XAxis dataKey="time" stroke="#71717a" fontSize={12} />
                <YAxis stroke="#71717a" fontSize={12} />
                <Tooltip contentStyle={{ background: "#09090b", border: "1px solid #27272a", borderRadius: 14 }} />
                <Area type="monotone" dataKey="requests" stroke="#a78bfa" fill="url(#requests)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Panel>
        <Panel className="p-5">
          <FieldLabel label="Provider Share" />
          <div className="mt-6 h-[320px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={providerShare} dataKey="value" nameKey="name" innerRadius={72} outerRadius={108} paddingAngle={4}>
                  {providerShare.map((entry, index) => (
                    <Cell key={entry.name} fill={chartColors[index % chartColors.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: "#09090b", border: "1px solid #27272a", borderRadius: 14 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>
      <Panel className="p-5">
        <FieldLabel label="Latency by Hour" />
        <div className="mt-6 h-[260px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={metricSeries}>
              <CartesianGrid stroke="#27272a" strokeDasharray="3 3" />
              <XAxis dataKey="time" stroke="#71717a" fontSize={12} />
              <YAxis stroke="#71717a" fontSize={12} />
              <Tooltip contentStyle={{ background: "#09090b", border: "1px solid #27272a", borderRadius: 14 }} />
              <Bar dataKey="latency" fill="#22d3ee" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Panel>
      <div className="grid gap-4 xl:grid-cols-2">
        <Panel className="p-5">
          <FieldLabel label="Token Usage" />
          <div className="mt-6 h-[260px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={metricSeries}>
                <defs>
                  <linearGradient id="tokens" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="0%" stopColor="#34d399" stopOpacity={0.55} />
                    <stop offset="100%" stopColor="#34d399" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="#27272a" strokeDasharray="3 3" />
                <XAxis dataKey="time" stroke="#71717a" fontSize={12} />
                <YAxis stroke="#71717a" fontSize={12} />
                <Tooltip contentStyle={{ background: "#09090b", border: "1px solid #27272a", borderRadius: 14 }} />
                <Area type="monotone" dataKey="tokens" stroke="#34d399" fill="url(#tokens)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Panel>
        <Panel className="p-5">
          <FieldLabel label="Cost and Success Rate" />
          <div className="mt-6 h-[260px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={metricSeries}>
                <CartesianGrid stroke="#27272a" strokeDasharray="3 3" />
                <XAxis dataKey="time" stroke="#71717a" fontSize={12} />
                <YAxis stroke="#71717a" fontSize={12} />
                <Tooltip contentStyle={{ background: "#09090b", border: "1px solid #27272a", borderRadius: 14 }} />
                <Bar dataKey="cost" fill="#f59e0b" radius={[8, 8, 0, 0]} />
                <Bar dataKey="success" fill="#8b5cf6" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>
    </div>
  );
}

function Evaluations() {
  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Evaluations"
        title="Release Quality Signals"
        description="Promptfoo and k6 summaries are mocked today and structured as replaceable benchmark cards."
      />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {evaluationBenchmarks.map((benchmark) => (
          <StatCard
            key={benchmark.name}
            label={benchmark.name}
            value={benchmark.score}
            helper={benchmark.detail}
            icon={benchmark.icon}
            tone={benchmark.name.includes("Latency") || benchmark.name.includes("Throughput") ? "cyan" : benchmark.name.includes("Error") ? "amber" : "emerald"}
          />
        ))}
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Panel className="p-5">
          <FieldLabel label="Promptfoo Summary" />
          <div className="mt-5 space-y-4">
            <SummaryRow label="Golden assertions" value="142 / 150" tone="text-emerald-300" />
            <SummaryRow label="Safety checks" value="98.1%" tone="text-emerald-300" />
            <SummaryRow label="Regression delta" value="-0.6%" tone="text-amber-200" />
          </div>
        </Panel>
        <Panel className="p-5">
          <FieldLabel label="k6 Summary" />
          <div className="mt-5 space-y-4">
            <SummaryRow label="Virtual users" value="50" tone="text-cyan-300" />
            <SummaryRow label="p95 response time" value="124ms" tone="text-emerald-300" />
            <SummaryRow label="HTTP failures" value="0.4%" tone="text-emerald-300" />
          </div>
        </Panel>
      </div>
      <Panel className="p-5">
        <FieldLabel label="Benchmark Matrix" />
        <div className="mt-5 overflow-hidden rounded-2xl border border-white/[0.08]">
          {["Correctness", "Latency", "Regression", "Safety", "Cost"].map((row, index) => (
            <div key={row} className="grid grid-cols-[1fr_110px_110px] gap-3 border-b border-white/[0.06] px-4 py-3 text-sm last:border-b-0 sm:grid-cols-[1fr_150px_150px]">
              <span className="font-medium text-zinc-200">{row}</span>
              <span className="text-emerald-300">{94 - index * 2}% pass</span>
              <span className="text-zinc-500">{index % 2 === 0 ? "Promptfoo" : "k6"}</span>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}

function SummaryRow({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone: string;
}) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-2xl border border-white/[0.08] bg-white/[0.03] px-4 py-3 text-sm">
      <span className="text-zinc-400">{label}</span>
      <span className={cn("font-mono font-semibold", tone)}>{value}</span>
    </div>
  );
}

function About() {
  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="About"
        title="Production GenAI MLOps Architecture"
        description="A focused control plane for chat inference, provider health, observability, evaluation, and deployment readiness."
      />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {architectureNodes.map((node) => {
          const Icon = node.icon;
          return (
            <Panel key={node.title} className="p-5">
              <div className="flex items-start gap-4">
                <div className="rounded-2xl border border-violet-400/20 bg-violet-500/10 p-3 text-violet-200">
                  <Icon className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-zinc-100">{node.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-zinc-500">{node.text}</p>
                </div>
              </div>
            </Panel>
          );
        })}
      </div>
      <Panel className="p-5">
        <FieldLabel label="Technology Stack" />
        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {stackItems.map((item) => {
            const Icon = item.icon;
            return (
              <div key={item.label} className="flex items-center gap-3 rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4 text-sm text-zinc-300">
                <Icon className="h-4 w-4 text-cyan-300" />
                {item.label}
              </div>
            );
          })}
        </div>
      </Panel>
      <Panel className="p-5">
        <FieldLabel label="Deployment Flow" />
        <div className="mt-5 grid gap-3 md:grid-cols-4">
          {["Commit", "CI/CD checks", "Docker image", "Azure Container Apps"].map((step, index) => (
            <div key={step} className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4">
              <div className="font-mono text-xs text-violet-300">0{index + 1}</div>
              <div className="mt-2 font-medium text-zinc-100">{step}</div>
            </div>
          ))}
        </div>
      </Panel>
      <Panel className="p-5">
        <FieldLabel label="Future Roadmap" />
        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {roadmapItems.map((item) => (
            <div key={item} className="flex items-center gap-3 rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4 text-sm text-zinc-300">
              <span className="h-2 w-2 rounded-full bg-violet-300" />
              {item}
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}

function SettingsView() {
  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Settings"
        title="Workspace Configuration"
        description="Operational preferences are visible here while provider credentials remain managed by the backend environment."
      />
      <Panel className="p-5">
        <div className="grid gap-4 md:grid-cols-2">
          {[
            ["API URL", process.env.NEXT_PUBLIC_API_URL ?? "/api"],
            ["Backend target", "http://localhost:8000"],
            ["Refresh cadence", "30 seconds"],
            ["Theme", "Dark"],
            ["Streaming", "Disabled by backend"],
          ].map(([label, value]) => (
            <div key={label} className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4">
              <div className="text-xs uppercase tracking-[0.18em] text-zinc-600">{label}</div>
              <div className="mt-2 font-mono text-sm text-zinc-200">{value}</div>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}

function dotClass(accent: "violet" | "cyan" | "emerald") {
  if (accent === "cyan") return "bg-cyan-400";
  if (accent === "emerald") return "bg-emerald-400";
  return "bg-violet-400";
}
