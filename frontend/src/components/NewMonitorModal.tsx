import { useState, type FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
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

type Props = {
  open: boolean;
  onClose: () => void;
};

type HttpMethod = "GET" | "HEAD" | "POST" | "PUT" | "PATCH" | "DELETE";

const defaults = {
  name: "",
  url: "https://",
  method: "GET" as HttpMethod,
  interval_seconds: 300,
  timeout_seconds: 10,
  expected_status: "200",
  retries: 2,
  tags: "",
  skip_tls_verify: false,
  follow_redirects: true,
  enabled: true,
};

const methodOptions = ["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE"].map(
  (method) => ({
    value: method as HttpMethod,
    label: method,
  }),
);

export function NewMonitorModal({ open, onClose }: Props) {
  const qc = useQueryClient();
  const [form, setForm] = useState(defaults);
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (payload: MonitorCreatePayload) => api.createMonitor(payload),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["dashboard"] });
      setForm(defaults);
      setError(null);
      onClose();
    },
    onError: (err: unknown) => {
      setError(err instanceof ApiError ? err.message : "Falha ao criar monitor");
    },
  });

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

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
      .map((t) => t.trim())
      .filter(Boolean);

    mutation.mutate({
      name: form.name.trim(),
      url: form.url.trim(),
      method: form.method,
      interval_seconds: form.interval_seconds,
      timeout_seconds: form.timeout_seconds,
      expected_status: statuses.length ? statuses : [200],
      retries: form.retries,
      skip_tls_verify: form.skip_tls_verify,
      follow_redirects: form.follow_redirects,
      enabled: form.enabled,
      tags,
    });
  }

  return (
    <Modal
      open={open}
      title="Novo monitor"
      onClose={onClose}
      footer={
        <>
          <Button onClick={onClose}>Cancelar</Button>
          <Button
            variant="primary"
            form="new-monitor-form"
            type="submit"
            disabled={mutation.isPending}
          >
            {mutation.isPending ? "Salvando…" : "Criar monitor"}
          </Button>
        </>
      }
    >
      <form id="new-monitor-form" className="space-y-3" onSubmit={onSubmit}>
        <div>
          <Label htmlFor="mon-name">Nome</Label>
          <Input
            id="mon-name"
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            placeholder="Reis Jurídico — Produção"
            required
            aria-invalid={Boolean(error && !form.name.trim())}
          />
        </div>

        <div>
          <Label htmlFor="mon-url">URL</Label>
          <Input
            id="mon-url"
            value={form.url}
            onChange={(e) => setForm((f) => ({ ...f, url: e.target.value }))}
            placeholder="https://reisjuridico.reis.adv.br/"
            required
            className="font-mono text-xs"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <Label htmlFor="mon-method">Método</Label>
            <Listbox
              id="mon-method"
              value={form.method}
              options={methodOptions}
              onChange={(method) =>
                setForm((f) => ({
                  ...f,
                  method,
                }))
              }
              aria-label="Método HTTP"
            />
          </div>
          <div>
            <Label htmlFor="mon-status">Status esperados</Label>
            <Input
              id="mon-status"
              value={form.expected_status}
              onChange={(e) =>
                setForm((f) => ({ ...f, expected_status: e.target.value }))
              }
              placeholder="200"
              className="font-mono text-xs"
            />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div>
            <Label htmlFor="mon-interval">Intervalo (s)</Label>
            <Input
              id="mon-interval"
              type="number"
              min={30}
              value={form.interval_seconds}
              onChange={(e) =>
                setForm((f) => ({
                  ...f,
                  interval_seconds: Number(e.target.value),
                }))
              }
              className="font-mono text-xs"
            />
          </div>
          <div>
            <Label htmlFor="mon-timeout">Timeout (s)</Label>
            <Input
              id="mon-timeout"
              type="number"
              min={1}
              max={120}
              value={form.timeout_seconds}
              onChange={(e) =>
                setForm((f) => ({
                  ...f,
                  timeout_seconds: Number(e.target.value),
                }))
              }
              className="font-mono text-xs"
            />
          </div>
          <div>
            <Label htmlFor="mon-retries">Retries</Label>
            <Input
              id="mon-retries"
              type="number"
              min={0}
              max={10}
              value={form.retries}
              onChange={(e) =>
                setForm((f) => ({ ...f, retries: Number(e.target.value) }))
              }
              className="font-mono text-xs"
            />
          </div>
        </div>

        <div>
          <Label htmlFor="mon-tags">Tags (separadas por vírgula)</Label>
          <Input
            id="mon-tags"
            value={form.tags}
            onChange={(e) => setForm((f) => ({ ...f, tags: e.target.value }))}
            placeholder="interno, critico"
          />
        </div>

        <div className="flex flex-col gap-2.5 pt-1">
          <Checkbox
            label="Seguir redirects"
            checked={form.follow_redirects}
            onChange={(e) =>
              setForm((f) => ({ ...f, follow_redirects: e.target.checked }))
            }
          />
          <Checkbox
            label="Ignorar verificação TLS (cert. interno)"
            checked={form.skip_tls_verify}
            onChange={(e) =>
              setForm((f) => ({ ...f, skip_tls_verify: e.target.checked }))
            }
          />
          <Checkbox
            label="Ativar imediatamente"
            checked={form.enabled}
            onChange={(e) =>
              setForm((f) => ({ ...f, enabled: e.target.checked }))
            }
          />
        </div>

        <FieldError>{error}</FieldError>
      </form>
    </Modal>
  );
}
