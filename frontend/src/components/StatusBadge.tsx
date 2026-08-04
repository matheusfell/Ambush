import { CheckCircle2, AlertTriangle, XCircle, PauseCircle, HelpCircle } from "lucide-react";
import { StatusBadge as UiBadge } from "@/components/ui";

export type StatusKind = "UP" | "DEGRADED" | "DOWN" | "PAUSED" | "UNKNOWN";

export function resolveStatus(
  enabled: boolean,
  result: string | null | undefined,
): StatusKind {
  if (!enabled) return "PAUSED";
  if (result === "UP") return "UP";
  if (result === "DEGRADED") return "DEGRADED";
  if (result === "DOWN") return "DOWN";
  return "UNKNOWN";
}

const meta: Record<
  StatusKind,
  {
    label: string;
    tone: "emerald" | "amber" | "red" | "sky" | "zinc";
    Icon: typeof CheckCircle2;
  }
> = {
  UP: { label: "Online", tone: "emerald", Icon: CheckCircle2 },
  DEGRADED: { label: "Degradado", tone: "amber", Icon: AlertTriangle },
  DOWN: { label: "Fora", tone: "red", Icon: XCircle },
  PAUSED: { label: "Pausado", tone: "zinc", Icon: PauseCircle },
  UNKNOWN: { label: "Sem dado", tone: "sky", Icon: HelpCircle },
};

export function StatusBadge({ kind }: { kind: StatusKind }) {
  const { label, tone, Icon } = meta[kind];
  return (
    <UiBadge tone={tone}>
      <Icon className="size-3.5 shrink-0" aria-hidden />
      {label}
    </UiBadge>
  );
}

export function statusBarColor(result: string): string {
  if (result === "UP") return "bg-emerald-500";
  if (result === "DEGRADED") return "bg-amber-400";
  if (result === "DOWN") return "bg-red-500";
  return "bg-zinc-600";
}
