import type { ProviderId } from "@/lib/api";
import {
  Activity,
  BarChart3,
  Bot,
  CheckCircle2,
  CircuitBoard,
  Cloud,
  Code2,
  Cpu,
  FlaskConical,
  Gauge,
  GitBranch,
  HeartPulse,
  Home,
  KeyRound,
  Layers3,
  LineChart,
  MessageSquareText,
  Network,
  PackageCheck,
  Server,
  Settings,
  ShieldCheck,
  Terminal,
  Zap,
} from "lucide-react";

export type ViewId =
  | "playground"
  | "health"
  | "metrics"
  | "evaluations"
  | "about"
  | "settings";

export const navItems = [
  { id: "playground", label: "AI Playground", icon: Terminal },
  { id: "health", label: "Health Dashboard", icon: HeartPulse },
  { id: "metrics", label: "Metrics", icon: BarChart3 },
  { id: "evaluations", label: "Evaluations", icon: FlaskConical },
  { id: "about", label: "About", icon: Home },
  { id: "settings", label: "Settings", icon: Settings },
] satisfies Array<{ id: ViewId; label: string; icon: typeof Terminal }>;

export const providers = [
  {
    id: "groq",
    label: "Groq",
    accent: "violet",
    status: "Primary",
    models: ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
  },
  {
    id: "openai",
    label: "OpenAI",
    accent: "cyan",
    status: "Configured",
    models: ["gpt-4o-mini", "gpt-4.1-mini"],
  },
  {
    id: "azure",
    label: "Azure OpenAI",
    accent: "emerald",
    status: "Standby",
    models: ["gpt-4o", "gpt-4.1"],
  },
] satisfies Array<{
  id: ProviderId;
  label: string;
  accent: "violet" | "cyan" | "emerald";
  status: string;
  models: string[];
}>;

export const metricSeries = [
  { time: "09:00", requests: 420, latency: 132, tokens: 11800, cost: 1.18, success: 99.1 },
  { time: "10:00", requests: 680, latency: 126, tokens: 16800, cost: 1.72, success: 99.4 },
  { time: "11:00", requests: 810, latency: 141, tokens: 21400, cost: 2.08, success: 98.9 },
  { time: "12:00", requests: 760, latency: 118, tokens: 19800, cost: 1.94, success: 99.6 },
  { time: "13:00", requests: 940, latency: 124, tokens: 24600, cost: 2.41, success: 99.2 },
  { time: "14:00", requests: 1120, latency: 137, tokens: 30100, cost: 2.96, success: 98.8 },
  { time: "15:00", requests: 1260, latency: 121, tokens: 33400, cost: 3.28, success: 99.5 },
];

export const providerShare = [
  { name: "Groq", value: 67 },
  { name: "OpenAI", value: 22 },
  { name: "Azure", value: 11 },
];

export const evaluationBenchmarks = [
  {
    name: "Accuracy",
    score: "94.8%",
    detail: "Promptfoo golden dataset",
    icon: CheckCircle2,
  },
  {
    name: "Latency",
    score: "124ms",
    detail: "k6 p95 response time",
    icon: Gauge,
  },
  {
    name: "Hallucination",
    score: "1.9%",
    detail: "Grounded answer failures",
    icon: Bot,
  },
  {
    name: "Pass Rate",
    score: "96.4%",
    detail: "All checks combined",
    icon: ShieldCheck,
  },
  {
    name: "Response Time",
    score: "218ms",
    detail: "End-to-end median",
    icon: Activity,
  },
  {
    name: "Throughput",
    score: "82 rps",
    detail: "Sustained chat load",
    icon: Zap,
  },
  {
    name: "Error Rate",
    score: "0.4%",
    detail: "Non-2xx responses",
    icon: PackageCheck,
  },
  {
    name: "Reasoning",
    score: "91.2%",
    detail: "multi-turn QA benchmark",
    icon: Bot,
  },
];

export const architectureNodes = [
  { title: "Next.js Console", text: "Typed App Router frontend for operators.", icon: Code2 },
  { title: "FastAPI Gateway", text: "OpenAI-compatible chat and health APIs.", icon: Server },
  { title: "Provider Layer", text: "Groq, OpenAI, and Azure OpenAI adapters.", icon: Bot },
  { title: "Observability", text: "Metrics, latency, cost, and eval feedback loops.", icon: Activity },
  { title: "Deployment", text: "Docker, CI/CD, and Azure Container Apps.", icon: Cloud },
  { title: "Evaluation", text: "Promptfoo and k6 checks before releases.", icon: FlaskConical },
];

export const stackItems = [
  { label: "FastAPI", icon: Zap },
  { label: "Next.js", icon: Layers3 },
  { label: "Docker", icon: CircuitBoard },
  { label: "Azure", icon: Cloud },
  { label: "GitHub Actions", icon: GitBranch },
  { label: "Promptfoo", icon: MessageSquareText },
  { label: "k6", icon: Gauge },
  { label: "Langfuse", icon: LineChart },
  { label: "Provider Routing", icon: Network },
  { label: "Secrets", icon: KeyRound },
  { label: "Compute", icon: Cpu },
  { label: "Analytics", icon: LineChart },
];

export const roadmapItems = [
  "Streaming chat responses",
  "Live metrics from /metrics",
  "Evaluation history drill-downs",
  "Cost budgets by provider",
  "Langfuse trace deep links",
  "Role-based access controls",
];
