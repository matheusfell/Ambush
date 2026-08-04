import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { ExternalLink, Play, Pause, Pencil, Trash2 } from "lucide-react";
import type { MonitorCard as MonitorCardType } from "@/api/client";
import { api } from "@/api/client";
import { EditMonitorModal } from "@/components/EditMonitorModal";
import { useAuth } from "@/auth/AuthContext";
import { HistoryBar } from "@/components/HistoryBar";
import { StatusBadge, resolveStatus } from "@/components/StatusBadge";
import { Button, Card, IconButton, Modal } from "@/components/ui";
import { formatLocal, formatMs } from "@/lib/utils";

export function MonitorCardView({ monitor }: { monitor: MonitorCardType }) {
  const { isAdmin } = useAuth();
  const qc = useQueryClient();
  const kind = resolveStatus(monitor.enabled, monitor.current_result);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [selectedCheckId, setSelectedCheckId] = useState<number | null>(null);

  const invalidate = () => qc.invalidateQueries({ queryKey: ["dashboard"] });
  const checkDetails = useQuery({
    queryKey: ["monitor-check", monitor.id, selectedCheckId],
    queryFn: () => api.monitorCheck(monitor.id, selectedCheckId as number),
    enabled: detailsOpen && selectedCheckId !== null,
  });
  const selectedCheck = checkDetails.data ?? null;

  const checkMut = useMutation({
    mutationFn: () => api.checkNow(monitor.id),
    onSuccess: invalidate,
  });
  const toggleMut = useMutation({
    mutationFn: () => api.toggleMonitor(monitor.id),
    onSuccess: invalidate,
  });
  const deleteMut = useMutation({
    mutationFn: () => api.deleteMonitor(monitor.id),
    onSuccess: invalidate,
  });

  return (
    <Card className="flex flex-col gap-3 p-3">
      <header className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <Link
            to={`/monitors/${monitor.id}`}
            className="block truncate text-sm font-medium text-zinc-100 hover:text-emerald-400"
          >
            {monitor.name}
          </Link>
          <a
            href={monitor.url}
            target="_blank"
            rel="noreferrer"
            className="mt-0.5 inline-flex max-w-full items-center gap-1 truncate font-mono text-[11px] text-zinc-500 hover:text-zinc-200"
          >
            <span className="truncate">{monitor.url}</span>
            <ExternalLink className="size-3 shrink-0" />
          </a>
        </div>
        <StatusBadge kind={kind} />
      </header>

      <HistoryBar
        history={monitor.history}
        onSelect={(check) => {
          setSelectedCheckId(check.id);
          setDetailsOpen(true);
        }}
      />

      <dl className="grid grid-cols-2 gap-2 font-mono text-[11px] md:grid-cols-4">
        <div>
          <dt className="text-zinc-500">Resposta</dt>
          <dd className="mt-0.5 text-zinc-200">{formatMs(monitor.last_response_time_ms)}</dd>
        </div>
        <div>
          <dt className="text-zinc-500">Uptime 24h</dt>
          <dd className="mt-0.5 text-zinc-200">
            {monitor.uptime_24h_percent != null
              ? `${monitor.uptime_24h_percent.toFixed(1)}%`
              : "—"}
          </dd>
        </div>
        <div>
          <dt className="text-zinc-500">Última</dt>
          <dd className="mt-0.5 truncate text-zinc-200">
            {formatLocal(monitor.last_checked_at)}
          </dd>
        </div>
        <div>
          <dt className="text-zinc-500">Próxima</dt>
          <dd className="mt-0.5 truncate text-zinc-200">
            {monitor.enabled ? formatLocal(monitor.next_check_at) : "Pausado"}
          </dd>
        </div>
      </dl>

      {monitor.tags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {monitor.tags.map((tag) => (
            <span
              key={tag}
              className="rounded-md border border-zinc-800 bg-zinc-900 px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider text-zinc-500"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {isAdmin && (
        <footer className="flex items-center gap-2 border-t border-zinc-800 pt-3">
          <Button
            disabled={checkMut.isPending}
            onClick={() => checkMut.mutate()}
            aria-label={`Checar ${monitor.name} agora`}
          >
            <Play className="size-3.5" />
            Checar
          </Button>
          <Button
            disabled={toggleMut.isPending}
            onClick={() => toggleMut.mutate()}
            aria-label={monitor.enabled ? "Pausar monitor" : "Retomar monitor"}
          >
            <Pause className="size-3.5" />
            {monitor.enabled ? "Pausar" : "Retomar"}
          </Button>
          <Button onClick={() => setEditOpen(true)} aria-label={`Editar ${monitor.name}`}>
            <Pencil className="size-3.5" />
            Editar
          </Button>
          <IconButton
            className="ml-auto text-red-400 hover:text-red-300"
            aria-label={`Excluir ${monitor.name}`}
            disabled={deleteMut.isPending}
            onClick={() => {
              if (window.confirm(`Excluir o monitor “${monitor.name}”?`)) {
                deleteMut.mutate();
              }
            }}
          >
            <Trash2 className="size-4" />
          </IconButton>
        </footer>
      )}

      <Modal
        open={detailsOpen}
        title={`Resposta da checagem — ${monitor.name}`}
        onClose={() => setDetailsOpen(false)}
        footer={<Button onClick={() => setDetailsOpen(false)}>Fechar</Button>}
      >
        {checkDetails.isLoading ? (
          <p className="text-sm text-zinc-500">Carregando resposta da checagem...</p>
        ) : selectedCheck ? (
          <div className="space-y-4">
            <dl className="grid grid-cols-2 gap-3 text-xs md:grid-cols-4">
              <div>
                <dt className="text-zinc-500">Resultado</dt>
                <dd className="mt-1 font-mono text-zinc-100">{selectedCheck.result}</dd>
              </div>
              <div>
                <dt className="text-zinc-500">HTTP</dt>
                <dd className="mt-1 font-mono text-zinc-100">
                  {selectedCheck.status_code ?? "sem resposta"}
                </dd>
              </div>
              <div>
                <dt className="text-zinc-500">Tempo</dt>
                <dd className="mt-1 font-mono text-zinc-100">
                  {formatMs(selectedCheck.response_time_ms)}
                </dd>
              </div>
              <div>
                <dt className="text-zinc-500">Horário</dt>
                <dd className="mt-1 font-mono text-zinc-100">
                  {formatLocal(selectedCheck.checked_at)}
                </dd>
              </div>
            </dl>

            {selectedCheck.error_message && (
              <div className="rounded-lg border border-red-900 bg-red-950/30 p-3">
                <div className="mb-1 text-xs font-medium uppercase tracking-wider text-red-400">
                  Erro / alerta
                </div>
                <p className="whitespace-pre-wrap font-mono text-xs text-red-200">
                  {selectedCheck.error_message}
                </p>
              </div>
            )}

            <div>
              <div className="mb-2 text-xs font-medium uppercase tracking-wider text-zinc-500">
                Body da resposta
              </div>
              <pre className="max-h-80 overflow-auto rounded-lg border border-zinc-800 bg-[#0c0c0f] p-3 font-mono text-xs leading-relaxed text-zinc-200">
                {selectedCheck.response_body_excerpt ||
                  "Nenhum body capturado para esta checagem."}
              </pre>
            </div>
          </div>
        ) : (
          <p className="text-sm text-zinc-500">Não foi possível carregar esta checagem.</p>
        )}
      </Modal>
      <EditMonitorModal
        open={editOpen}
        monitorId={monitor.id}
        onClose={() => setEditOpen(false)}
      />
    </Card>
  );
}
