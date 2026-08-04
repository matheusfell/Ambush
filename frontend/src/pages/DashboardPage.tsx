import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, AlertTriangle, XCircle, PauseCircle } from "lucide-react";
import { api, type MonitorCard } from "@/api/client";
import { MonitorCardView } from "@/components/MonitorCard";
import { Card, Panel, Skeleton } from "@/components/ui";
import { cn } from "@/lib/utils";

function groupByTag(monitors: MonitorCard[]): { tag: string; items: MonitorCard[] }[] {
  const map = new Map<string, MonitorCard[]>();
  const untagged: MonitorCard[] = [];

  for (const m of monitors) {
    if (!m.tags.length) {
      untagged.push(m);
      continue;
    }
    for (const tag of m.tags) {
      const list = map.get(tag) ?? [];
      list.push(m);
      map.set(tag, list);
    }
  }

  const groups = [...map.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([tag, items]) => ({ tag, items }));

  if (untagged.length) groups.push({ tag: "sem tag", items: untagged });
  return groups;
}

function Counter({
  label,
  value,
  icon: Icon,
  tone,
}: {
  label: string;
  value: number;
  icon: typeof CheckCircle2;
  tone: string;
}) {
  return (
    <Card className="flex items-center gap-3 p-3">
      <div className={cn("rounded-lg border border-zinc-800 bg-zinc-900 p-2", tone)}>
        <Icon className="size-4" aria-hidden />
      </div>
      <div>
        <div className="text-xs text-zinc-500">{label}</div>
        <div className={cn("font-mono text-2xl font-semibold tabular-nums leading-none", tone)}>
          {value}
        </div>
      </div>
    </Card>
  );
}

function GroupPanel({ group }: { group: { tag: string; items: MonitorCard[] } }) {
  const downCount = group.items.filter((item) => item.current_result === "DOWN").length;
  const degradedCount = group.items.filter((item) => item.current_result === "DEGRADED").length;

  return (
    <Panel className="flex min-h-[260px] flex-col overflow-hidden">
      <header className="flex items-center justify-between gap-3 border-b border-zinc-800 px-3 py-2.5">
        <div className="min-w-0">
          <h2 className="truncate text-xs font-semibold tracking-[0.12em] text-zinc-200 uppercase">
            {group.tag}
          </h2>
          <p className="text-[11px] text-zinc-500">
            {group.items.length} monitor{group.items.length === 1 ? "" : "es"}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-1.5 font-mono text-[10px]">
          {downCount > 0 && (
            <span className="rounded-full border border-red-900 bg-red-950/40 px-2 py-0.5 text-red-400">
              {downCount} fora
            </span>
          )}
          {degradedCount > 0 && (
            <span className="rounded-full border border-amber-900 bg-amber-950/40 px-2 py-0.5 text-amber-400">
              {degradedCount} deg.
            </span>
          )}
        </div>
      </header>

      <div className="grid max-h-[560px] flex-1 gap-3 overflow-y-auto p-3">
        {group.items.map((m) => (
          <MonitorCardView key={`${group.tag}-${m.id}`} monitor={m} />
        ))}
      </div>
    </Panel>
  );
}

export function DashboardPage() {
  const { data, isLoading, isError, error, dataUpdatedAt } = useQuery({
    queryKey: ["dashboard"],
    queryFn: api.dashboard,
    refetchInterval: 30_000,
  });

  const groups = useMemo(() => (data ? groupByTag(data.monitors) : []), [data]);

  const updated = dataUpdatedAt
    ? new Date(dataUpdatedAt).toLocaleTimeString("pt-BR", {
        timeZone: "America/Sao_Paulo",
      })
    : null;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold text-zinc-100">Status operacional</h1>
          <p className="text-xs text-zinc-500">
            Atualização automática a cada 30s
            {updated ? ` · última às ${updated}` : ""}
          </p>
        </div>
        {data && (
          <div className="font-mono text-xs text-zinc-500">
            {data.monitors.length} monitor{data.monitors.length === 1 ? "" : "es"} ·{" "}
            {groups.length} bloco{groups.length === 1 ? "" : "s"}
          </div>
        )}
      </div>

      {isLoading && (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-20" />
          ))}
        </div>
      )}

      {isError && (
        <Card className="border-red-900 bg-red-950/30 p-3 text-sm text-red-400">
          {(error as Error).message}
        </Card>
      )}

      {data && (
        <>
          <section className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <Counter label="Online" value={data.up} icon={CheckCircle2} tone="text-emerald-400" />
            <Counter
              label="Degradado"
              value={data.degraded}
              icon={AlertTriangle}
              tone="text-amber-400"
            />
            <Counter label="Fora" value={data.down} icon={XCircle} tone="text-red-400" />
            <Counter
              label="Pausado"
              value={data.paused}
              icon={PauseCircle}
              tone="text-zinc-400"
            />
          </section>

          {groups.length === 0 ? (
            <Card className="px-4 py-10 text-center text-sm text-zinc-500">
              Nenhum monitor cadastrado. Use <strong className="text-zinc-300">Novo monitor</strong>{" "}
              na barra lateral.
            </Card>
          ) : (
            <section className="grid items-start gap-4 xl:grid-cols-2 2xl:grid-cols-3">
              {groups.map((group) => (
                <GroupPanel key={group.tag} group={group} />
              ))}
            </section>
          )}
        </>
      )}
    </div>
  );
}
