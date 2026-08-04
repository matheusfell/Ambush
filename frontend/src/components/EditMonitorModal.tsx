import { useEffect, useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ApiError, type MonitorCreatePayload } from "@/api/client";
import {
  Button,
  Checkbox,
  FieldError,
  Input,
  Label,
  Listbox,
  Modal,
} from "@/components/ui";

type HttpMethod = "GET" | "HEAD" | "POST" | "PUT" | "PATCH" | "DELETE";

type Props = {
  monitorId: number | null;
  open: boolean;
  onClose: () => void;
};

const defaults = {
  name: "",
  url: "https://",
  method: "GET" as HttpMethod,
  interval_seconds: 300,
  timeout_seconds: 10,
  expected_status: "200",
  retries: 2,
  slow_threshold_ms: 3000,
  tags: "",
  skip_tls_verify: false,
  follow_redirects: true,
  enabled: true,
};

const methodOptions = ["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE"].map(
  (method) => ({ value: method as HttpMethod, label: method }),
);

export function EditMonitorModal({ monitorId, open, onClose }: Props) {
  const qc = useQueryClient();
  const [form, setForm] = useState(defaults);
  const [error, setError] = useState<string | null>(null);

  const monitor = useQuery({
    queryKey: ["monitor", monitorId],
    queryFn: () => api.monitor(monitorId as number),
    enabled: open && monitorId !== null,
  });

  useEffect(() => {
    if (!monitor.data) return;
    setForm({
      name: monitor.data.name,
      url: monitor.data.url,
      method: monitor.data.method as HttpMethod,
      interval_seconds: monitor.data.interval_seconds,
      timeout_seconds: monitor.data.timeout_seconds,
      expected_status: monitor.data.expected_status.join(","),
      retries: monitor.data.retries,
      slow_threshold_ms: monitor.data.slow_threshold_ms,
      tags: monitor.data.tags.join(", "),
      skip_tls_verify: monitor.data.skip_tls_verify,
      follow_redirects: monitor.data.follow_redirects,
      enabled: monitor.data.enabled,
    });
    setError(null);
  }, [monitor.data]);

  const mutation = useMutation({
    mutationFn: (payload: MonitorCreatePayload) =>
      api.updateMonitor(monitorId as number, payload),
    onSuccess: async () => {
      await Promise.all([
        qc.invalidateQueries({ queryKey: ["dashboard"] }),
        qc.invalidateQueries({ queryKey: ["monitor", monitorId] }),
      ]);
      setError(null);
      onClose();
    },
    onError: (err: unknown) => {
      setError(err instanceof ApiError ? err.message : "Falha ao editar monitor");
    },
  });

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (monitorId === null) return;

    const statuses = form.expected_status
      .split(/[,\s]+/)
      .map((s) => s.trim())
      .filter(Boolean)
      .map((s) => Number(s));

    if (!form.name.trim()) {
      setError("Informe o nome");
      return;
    }
    if (!form.url.trim() || form.url === "https://") {
      setError("Informe a URL");
      return;
    }
    if (statuses.some((n) => Number.isNaN(n) || n < 100 || n > 599)) {
      setError("Status esperados inválidos (ex.: 200 ou 200,301,302)");
      return;
    }
    if (form.interval_seconds < 30) {
      setError("Intervalo mínimo: 30 segundos");
      return;
    }

    const tags = form.tags
      .split(/[,]+/)
      .map((tag) => tag.trim())
      .filter(Boolean);

    mutation.mutate({
      name: form.name.trim(),
      url: form.url.trim(),
      method: form.method,
      interval_seconds: form.interval_seconds,
      timeout_seconds: form.timeout_seconds,
      expected_status: statuses.length ? statuses : [200],
      retries: form.retries,
      slow_threshold_ms: form.slow_threshold_ms,
      skip_tls_verify: form.skip_tls_verify,
      follow_redirects: form.follow_redirects,
      enabled: form.enabled,
      tags,
    });
  }

  return (
    <Modal
      open={open}
      title="Editar monitor"
      onClose={onClose}
      footer={
        <>
          <Button onClick={onClose}>Cancelar</Button>
          <Button
            variant="primary"
            form="edit-monitor-form"
            type="submit"
            disabled={mutation.isPending || monitor.isLoading}
          >
            {mutation.isPending ? "Salvando…" : "Salvar alterações"}
          </Button>
        </>
      }
    >
      {monitor.isLoading ? (
        <p className="text-sm text-zinc-500">Carregando monitor...</p>
      ) : (
        <form id="edit-monitor-form" className="space-y-3" onSubmit={onSubmit}>
          <div>
            <Label htmlFor="edit-mon-name">Nome</Label>
            <Input
              id="edit-mon-name"
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              required
            />
          </div>

          <div>
            <Label htmlFor="edit-mon-url">URL</Label>
            <Input
              id="edit-mon-url"
              value={form.url}
              onChange={(e) => setForm((f) => ({ ...f, url: e.target.value }))}
              required
              className="font-mono text-xs"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label htmlFor="edit-mon-method">Método</Label>
              <Listbox
                id="edit-mon-method"
                value={form.method}
                options={methodOptions}
                onChange={(method) => setForm((f) => ({ ...f, method }))}
                aria-label="Método HTTP"
              />
            </div>
            <div>
              <Label htmlFor="edit-mon-status">Status esperados</Label>
              <Input
                id="edit-mon-status"
                value={form.expected_status}
                onChange={(e) =>
                  setForm((f) => ({ ...f, expected_status: e.target.value }))
                }
                className="font-mono text-xs"
              />
            </div>
          </div>

          <div className="grid grid-cols-4 gap-3">
            <div>
              <Label htmlFor="edit-mon-interval">Intervalo (s)</Label>
              <Input
                id="edit-mon-interval"
                type="number"
                min={30}
                value={form.interval_seconds}
                onChange={(e) =>
                  setForm((f) => ({ ...f, interval_seconds: Number(e.target.value) }))
                }
                className="font-mono text-xs"
              />
            </div>
            <div>
              <Label htmlFor="edit-mon-timeout">Timeout (s)</Label>
              <Input
                id="edit-mon-timeout"
                type="number"
                min={1}
                max={120}
                value={form.timeout_seconds}
                onChange={(e) =>
                  setForm((f) => ({ ...f, timeout_seconds: Number(e.target.value) }))
                }
                className="font-mono text-xs"
              />
            </div>
            <div>
              <Label htmlFor="edit-mon-retries">Retries</Label>
              <Input
                id="edit-mon-retries"
                type="number"
                min={0}
                max={10}
                value={form.retries}
                onChange={(e) => setForm((f) => ({ ...f, retries: Number(e.target.value) }))}
                className="font-mono text-xs"
              />
            </div>
            <div>
              <Label htmlFor="edit-mon-slow">Lento (ms)</Label>
              <Input
                id="edit-mon-slow"
                type="number"
                min={1}
                value={form.slow_threshold_ms}
                onChange={(e) =>
                  setForm((f) => ({ ...f, slow_threshold_ms: Number(e.target.value) }))
                }
                className="font-mono text-xs"
              />
            </div>
          </div>

          <div>
            <Label htmlFor="edit-mon-tags">Tags (separadas por vírgula)</Label>
            <Input
              id="edit-mon-tags"
              value={form.tags}
              onChange={(e) => setForm((f) => ({ ...f, tags: e.target.value }))}
            />
          </div>

          <div className="flex flex-col gap-2.5 pt-1">
            <Checkbox
              label="Seguir redirects"
              checked={form.follow_redirects}
              onChange={(e) => setForm((f) => ({ ...f, follow_redirects: e.target.checked }))}
            />
            <Checkbox
              label="Ignorar verificação TLS (cert. interno)"
              checked={form.skip_tls_verify}
              onChange={(e) => setForm((f) => ({ ...f, skip_tls_verify: e.target.checked }))}
            />
            <Checkbox
              label="Monitor ativo"
              checked={form.enabled}
              onChange={(e) => setForm((f) => ({ ...f, enabled: e.target.checked }))}
            />
          </div>

          <FieldError>{error}</FieldError>
        </form>
      )}
    </Modal>
  );
}
