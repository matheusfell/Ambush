import { Link, useParams } from "react-router-dom";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, ExternalLink } from "lucide-react";
import { api, type CheckRecord } from "@/api/client";
import { statusBarColor, StatusBadge, resolveStatus } from "@/components/StatusBadge";
import { Card, Skeleton, StatusBadge as UiStatusBadge } from "@/components/ui";
import { cn, formatLocal, formatMs } from "@/lib/utils";

const TABLE_PAGE_SIZE = 25;
const CHART_POINT_LIMIT = 20;

function percent(value: number, total: number): string {
  if (total === 0) return "0%";
  return `${((value / total) * 100).toFixed(1)}%`;
}

function ResponseChart({ checks }: { checks: CheckRecord[] }) {
  const points = checks
    .slice()
    .reverse()
    .filter((check) => check.response_time_ms != null);
  const width = 100;
  const height = 52;
  const paddingX = 5;
  const paddingY = 7;
  const max = Math.max(...points.map((check) => check.response_time_ms ?? 0), 1);

  if (points.length < 2) {
    return (
      <div className="flex h-56 items-center justify-center rounded-xl border border-dashed border-zinc-800 text-sm text-zinc-500">
        Histórico insuficiente para gráfico.
      </div>
    );
  }

  const polyline = points
    .map((check, index) => {
      const x =
        paddingX + (index / Math.max(points.length - 1, 1)) * (width - paddingX * 2);
      const y =
        height -
        paddingY -
        ((check.response_time_ms ?? 0) / max) * (height - paddingY * 2);
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(" ");

  return (
    <div className="rounded-xl border border-zinc-800 bg-[#111114] p-5">
      <div className="mb-5 flex items-center justify-between text-xs">
        <span className="font-medium text-zinc-300">Picos de resposta</span>
        <span className="font-mono text-zinc-500">máx. {formatMs(max)}</span>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} className="h-56 w-full overflow-visible">
        {[0.25, 0.5, 0.75].map((line) => (
          <line
            key={line}
            x1={paddingX}
            x2={width - paddingX}
            y1={paddingY + line * (height - paddingY * 2)}
            y2={paddingY + line * (height - paddingY * 2)}
            stroke="#27272a"
            strokeWidth="0.5"
            vectorEffect="non-scaling-stroke"
          />
        ))}
        <polyline
          points={polyline}
          fill="none"
          stroke="#10b981"
          strokeWidth="1.6"
          vectorEffect="non-scaling-stroke"
        />
        {points.map((check, index) => {
          const x =
            paddingX + (index / Math.max(points.length - 1, 1)) * (width - paddingX * 2);
          const y =
            height -
            paddingY -
            ((check.response_time_ms ?? 0) / max) * (height - paddingY * 2);
          return (
            <circle
              key={check.id}
              cx={x}
              cy={y}
              r="1.3"
              className={cn(
                check.result === "DOWN"
                  ? "fill-red-500"
                  : check.result === "DEGRADED"
                    ? "fill-amber-400"
                    : "fill-emerald-400",
              )}
            />
          );
        })}
      </svg>
    </div>
  );
}

function StabilityStrip({ checks }: { checks: CheckRecord[] }) {
  const chronological = checks.slice().reverse();
  return (
    <div className="rounded-xl border border-zinc-800 bg-[#111114] p-4">
      <div className="mb-3 flex items-center justify-between text-xs">
        <span className="font-medium text-zinc-300">Histórico de estabilidade</span>
        <span className="font-mono text-zinc-500">{chronological.length} checagens</span>
      </div>
      <div className="flex h-8 items-stretch gap-px overflow-hidden rounded-lg">
        {chronological.map((check) => (
          <div
            key={check.id}
            className={cn("min-w-[3px] flex-1", statusBarColor(check.result))}
            title={`${check.result} · ${formatLocal(check.checked_at)}`}
          />
        ))}
      </div>
    </div>
  );
}

export function MonitorDetailPage() {
  const params = useParams();
  const monitorId = Number(params.id);
  const [page, setPage] = useState(1);
  const monitor = useQuery({
    queryKey: ["monitor", monitorId],
    queryFn: () => api.monitor(monitorId),
    enabled: Number.isFinite(monitorId),
  });
  const chartChecks = useQuery({
    queryKey: ["monitor-checks-chart", monitorId, CHART_POINT_LIMIT],
    queryFn: () => api.monitorChecks(monitorId, CHART_POINT_LIMIT, 1),
    enabled: Number.isFinite(monitorId),
    refetchInterval: 30_000,
  });
  const tableChecks = useQuery({
    queryKey: ["monitor-checks-table", monitorId, page],
    queryFn: () => api.monitorChecks(monitorId, TABLE_PAGE_SIZE, page),
    enabled: Number.isFinite(monitorId),
    refetchInterval: 30_000,
  });

  const chartRows = chartChecks.data?.items ?? [];
  const tableRows = tableChecks.data?.items ?? [];
  const total = chartRows.length;
  const up = chartRows.filter((check) => check.result === "UP").length;
  const degraded = chartRows.filter((check) => check.result === "DEGRADED").length;
  const down = chartRows.filter((check) => check.result === "DOWN").length;
  const avgMs = chartRows.length
    ? Math.round(
        chartRows.reduce((sum, check) => sum + (check.response_time_ms ?? 0), 0) /
          chartRows.length,
      )
    : null;
  const totalTableRows = tableChecks.data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(totalTableRows / TABLE_PAGE_SIZE));
  const currentKind = resolveStatus(monitor.data?.enabled ?? true, monitor.data?.last_result);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Link
          to="/monitors"
          className="inline-flex h-9 items-center gap-2 rounded-lg border border-zinc-700 px-3 text-sm text-zinc-300 hover:bg-zinc-900 hover:text-zinc-100"
        >
          <ArrowLeft className="size-4" />
          Voltar
        </Link>
        {monitor.data && <StatusBadge kind={currentKind} />}
      </div>

      {monitor.isLoading && <Skeleton className="h-40" />}
      {monitor.isError && (
        <Card className="border-red-900 bg-red-950/30 p-3 text-sm text-red-400">
          {(monitor.error as Error).message}
        </Card>
      )}

      {monitor.data && (
        <>
          <Card className="p-4">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
              <div className="min-w-0">
                <h1 className="text-xl font-semibold text-zinc-100">{monitor.data.name}</h1>
                <a
                  href={monitor.data.url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-1 inline-flex max-w-full items-center gap-1 truncate font-mono text-xs text-zinc-500 hover:text-zinc-200"
                >
                  <span className="truncate">{monitor.data.url}</span>
                  <ExternalLink className="size-3" />
                </a>
                <div className="mt-3 flex flex-wrap gap-2">
                  <UiStatusBadge tone="zinc">{monitor.data.method}</UiStatusBadge>
                  <UiStatusBadge tone="sky">a cada {monitor.data.interval_seconds}s</UiStatusBadge>
                  <UiStatusBadge tone={monitor.data.enabled ? "emerald" : "zinc"}>
                    {monitor.data.enabled ? "ativo" : "pausado"}
                  </UiStatusBadge>
                  {monitor.data.tags.map((tag) => (
                    <UiStatusBadge key={tag} tone="zinc">{tag}</UiStatusBadge>
                  ))}
                </div>
              </div>
              <dl className="grid grid-cols-2 gap-4 text-xs lg:min-w-72">
                <div>
                  <dt className="text-zinc-500">Última checagem</dt>
                  <dd className="mt-1 font-mono text-zinc-100">
                    {formatLocal(monitor.data.last_checked_at)}
                  </dd>
                </div>
                <div>
                  <dt className="text-zinc-500">Última resposta</dt>
                  <dd className="mt-1 font-mono text-zinc-100">
                    {formatMs(monitor.data.last_response_time_ms)}
                  </dd>
                </div>
                <div>
                  <dt className="text-zinc-500">Timeout</dt>
                  <dd className="mt-1 font-mono text-zinc-100">{monitor.data.timeout_seconds}s</dd>
                </div>
                <div>
                  <dt className="text-zinc-500">Retries</dt>
                  <dd className="mt-1 font-mono text-zinc-100">{monitor.data.retries}</dd>
                </div>
              </dl>
            </div>
          </Card>

          <section className="grid gap-3 md:grid-cols-4">
            <Card className="p-3"><div className="text-xs text-zinc-500">Estabilidade</div><div className="mt-1 font-mono text-2xl text-emerald-400">{percent(up + degraded, total)}</div></Card>
            <Card className="p-3"><div className="text-xs text-zinc-500">Online</div><div className="mt-1 font-mono text-2xl text-emerald-400">{up}</div></Card>
            <Card className="p-3"><div className="text-xs text-zinc-500">Degradado</div><div className="mt-1 font-mono text-2xl text-amber-400">{degraded}</div></Card>
            <Card className="p-3"><div className="text-xs text-zinc-500">Fora</div><div className="mt-1 font-mono text-2xl text-red-400">{down}</div></Card>
          </section>

          {chartChecks.isLoading ? (
            <Skeleton className="h-72" />
          ) : (
            <section className="grid gap-4 xl:grid-cols-[1fr_360px]">
              <div className="space-y-4">
                <ResponseChart checks={chartRows} />
                <StabilityStrip checks={chartRows} />
              </div>
              <Card className="p-4">
                <h2 className="text-sm font-semibold text-zinc-100">Resumo técnico</h2>
                <dl className="mt-4 space-y-3 text-xs">
                  <div className="flex justify-between gap-3"><dt className="text-zinc-500">Média de resposta</dt><dd className="font-mono text-zinc-100">{formatMs(avgMs)}</dd></div>
                  <div className="flex justify-between gap-3"><dt className="text-zinc-500">Status esperados</dt><dd className="font-mono text-zinc-100">{monitor.data.expected_status.join(", ")}</dd></div>
                  <div className="flex justify-between gap-3"><dt className="text-zinc-500">Segue redirects</dt><dd className="font-mono text-zinc-100">{monitor.data.follow_redirects ? "sim" : "não"}</dd></div>
                  <div className="flex justify-between gap-3"><dt className="text-zinc-500">TLS ignorado</dt><dd className="font-mono text-zinc-100">{monitor.data.skip_tls_verify ? "sim" : "não"}</dd></div>
                </dl>
              </Card>
            </section>
          )}

          <Card className="overflow-hidden p-0">
            <div className="border-b border-zinc-800 px-4 py-3">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-sm font-semibold text-zinc-100">Últimas checagens</h2>
                  <p className="text-xs text-zinc-500">
                    Página {page} de {totalPages} · {totalTableRows} registros
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    className="h-8 rounded-lg border border-zinc-700 px-3 text-xs text-zinc-300 disabled:opacity-50"
                    disabled={page <= 1}
                    onClick={() => setPage((current) => Math.max(1, current - 1))}
                  >
                    Anterior
                  </button>
                  <button
                    type="button"
                    className="h-8 rounded-lg border border-zinc-700 px-3 text-xs text-zinc-300 disabled:opacity-50"
                    disabled={page >= totalPages}
                    onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
                  >
                    Próxima
                  </button>
                </div>
              </div>
            </div>
            <div className="max-h-[420px] overflow-auto">
              <table className="w-full text-left text-xs">
                <thead className="sticky top-0 bg-[#161618] text-zinc-500">
                  <tr>
                    <th className="px-4 py-2 font-medium">Horário</th>
                    <th className="px-4 py-2 font-medium">Resultado</th>
                    <th className="px-4 py-2 font-medium">HTTP</th>
                    <th className="px-4 py-2 font-medium">Tempo</th>
                    <th className="px-4 py-2 font-medium">Erro</th>
                  </tr>
                </thead>
                <tbody>
                  {tableRows.map((check) => (
                    <tr key={check.id} className="border-t border-zinc-900">
                      <td className="px-4 py-2 font-mono text-zinc-400">{formatLocal(check.checked_at)}</td>
                      <td className="px-4 py-2 font-mono text-zinc-100">{check.result}</td>
                      <td className="px-4 py-2 font-mono text-zinc-100">{check.status_code ?? "-"}</td>
                      <td className="px-4 py-2 font-mono text-zinc-100">{formatMs(check.response_time_ms)}</td>
                      <td className="max-w-sm truncate px-4 py-2 text-zinc-500">{check.error_message ?? "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {tableChecks.isLoading && (
              <div className="border-t border-zinc-800 px-4 py-3 text-xs text-zinc-500">
                Carregando checagens...
              </div>
            )}
          </Card>
        </>
      )}
    </div>
  );
}
