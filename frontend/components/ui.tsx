import type { ComponentType, ReactNode } from "react";
import { Loader2 } from "lucide-react";

export function cn(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(" ");
}

export function SectionHeader({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description?: string;
}) {
  return (
    <div className="space-y-2">
      <div className="text-[11px] font-bold uppercase tracking-[0.22em] text-zinc-500">
        {eyebrow}
      </div>
      <h2 className="text-2xl font-semibold tracking-tight text-zinc-50 md:text-3xl">
        {title}
      </h2>
      {description ? (
        <p className="max-w-2xl text-sm leading-6 text-zinc-400">{description}</p>
      ) : null}
    </div>
  );
}

export function Panel({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={cn(
        "rounded-[22px] border border-white/[0.08] bg-zinc-950/70 shadow-2xl shadow-black/20 transition-shadow duration-300 hover:shadow-black/30",
        className,
      )}
    >
      {children}
    </section>
  );
}

export function StatCard({
  label,
  value,
  helper,
  icon: Icon,
  tone = "violet",
}: {
  label: string;
  value: string;
  helper: string;
  icon: ComponentType<{ className?: string }>;
  tone?: "violet" | "cyan" | "emerald" | "amber";
}) {
  const tones = {
    violet: "text-violet-300 bg-violet-500/10 border-violet-500/20",
    cyan: "text-cyan-300 bg-cyan-500/10 border-cyan-500/20",
    emerald: "text-emerald-300 bg-emerald-500/10 border-emerald-500/20",
    amber: "text-amber-300 bg-amber-500/10 border-amber-500/20",
  };

  return (
    <Panel className="p-5 transition-transform duration-200 hover:-translate-y-0.5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">
            {label}
          </p>
          <p className="mt-3 text-2xl font-semibold text-zinc-50">{value}</p>
          <p className="mt-2 text-sm text-zinc-500">{helper}</p>
        </div>
        <div className={cn("rounded-2xl border p-3", tones[tone])}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </Panel>
  );
}

export function Spinner({ label = "Loading" }: { label?: string }) {
  return (
    <span className="inline-flex items-center gap-2">
      <Loader2 className="h-4 w-4 animate-spin" />
      {label}
    </span>
  );
}

export function FieldLabel({
  label,
  value,
}: {
  label: string;
  value?: string;
}) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-zinc-500">
        {label}
      </span>
      {value ? (
        <span className="font-mono text-sm text-violet-200">{value}</span>
      ) : null}
    </div>
  );
}

export function EmptyState({
  icon: Icon,
  title,
  text,
}: {
  icon: ComponentType<{ className?: string }>;
  title: string;
  text: string;
}) {
  return (
    <div className="flex min-h-[260px] flex-col items-center justify-center text-center">
      <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4 text-zinc-500">
        <Icon className="h-6 w-6" />
      </div>
      <p className="mt-4 font-medium text-zinc-300">{title}</p>
      <p className="mt-1 max-w-sm text-sm text-zinc-500">{text}</p>
    </div>
  );
}

export function ResponseSkeleton() {
  return (
    <div className="space-y-4 py-2" aria-label="Response loading">
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 animate-pulse rounded-2xl bg-violet-400/15" />
        <div className="space-y-2">
          <div className="h-3 w-36 animate-pulse rounded-full bg-white/[0.08]" />
          <div className="h-3 w-24 animate-pulse rounded-full bg-white/[0.05]" />
        </div>
      </div>
      <div className="space-y-3">
        <div className="h-4 w-full animate-pulse rounded-full bg-white/[0.07]" />
        <div className="h-4 w-[92%] animate-pulse rounded-full bg-white/[0.07]" />
        <div className="h-4 w-[78%] animate-pulse rounded-full bg-white/[0.06]" />
        <div className="mt-5 h-24 animate-pulse rounded-2xl border border-white/[0.06] bg-white/[0.04]" />
        <div className="h-4 w-[86%] animate-pulse rounded-full bg-white/[0.06]" />
      </div>
    </div>
  );
}
