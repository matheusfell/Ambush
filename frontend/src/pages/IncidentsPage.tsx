import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { Card, Skeleton, StatusBadge } from "@/components/ui";
import { formatLocal } from "@/lib/utils";

function formatDuration(seconds: number | null): string {
  if (seconds == null) return "—";
  if (seconds < 60) return `${seconds}s`;
  const m = Math.floor(seconds / 60);
  if (m < 60) return `${m} min`;
  const h = Math.floor(m / 60);
  return `${h}h ${m % 60}min`;
}

export function IncidentsPage() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["incidents"],
    queryFn: () => api.incidents(),
    refetchInterval: 30_000,
  });

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold text-zinc-100">Incidentes</h1>
        <p className="text-xs text-zinc-500">Histórico de indisponibilidade</p>
      </div>

      {isLoading && <Skeleton className="h-40" />}
      {isError && (
        <Card className="border-red-900 bg-red-950/30 p-3 text-sm text-red-400">
          {(error as Error).message}
        </Card>
      )}

      {data && data.length === 0 && (
        <Card className="px-4 py-10 text-center text-sm text-zinc-500">
          Nenhum incidente registrado.
        </Card>
      )}

      {data && data.length > 0 && (
        <Card className="overflow-hidden p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-zinc-800 text-xs text-zinc-500">
                <tr>
                  <th className="px-4 py-3 font-medium">Monitor</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Início</th>
                  <th className="px-4 py-3 font-medium">Duração</th>
                  <th className="px-4 py-3 font-medium">Falhas</th>
                  <th className="px-4 py-3 font-medium">Erro</th>
                </tr>
              </thead>
              <tbody>
                {data.map((inc) => (
                  <tr key={inc.id} className="border-b border-zinc-800/80 last:border-0">
                    <td className="px-4 py-3 text-zinc-200">
                      {inc.monitor_name ?? `#${inc.monitor_id}`}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge tone={inc.status === "open" ? "red" : "emerald"}>
                        {inc.status === "open" ? "Aberto" : "Fechado"}
                      </StatusBadge>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-zinc-400">
                      {formatLocal(inc.started_at)}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-zinc-400">
                      {formatDuration(inc.duration_seconds)}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-zinc-400">
                      {inc.failure_count}
                    </td>
                    <td className="max-w-[240px] truncate px-4 py-3 text-xs text-zinc-500">
                      {inc.last_error ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
