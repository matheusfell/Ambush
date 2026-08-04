import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { MonitorCardView } from "@/components/MonitorCard";
import { Card, Skeleton } from "@/components/ui";

export function MonitorsPage() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["dashboard"],
    queryFn: api.dashboard,
    refetchInterval: 30_000,
  });

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold text-zinc-100">Monitores</h1>
        <p className="text-xs text-zinc-500">Lista completa dos alvos de checagem</p>
      </div>

      {isLoading && (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-40" />
          ))}
        </div>
      )}

      {isError && (
        <Card className="border-red-900 bg-red-950/30 p-3 text-sm text-red-400">
          {(error as Error).message}
        </Card>
      )}

      {data && (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {data.monitors.map((m) => (
            <MonitorCardView key={m.id} monitor={m} />
          ))}
        </div>
      )}
    </div>
  );
}
