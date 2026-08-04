import { useEffect, useMemo, useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Mail, Send } from "lucide-react";
import {
  api,
  ApiError,
  type EmailNotificationConfigPayload,
  type SmtpSettingsUpdate,
} from "@/api/client";
import {
  Button,
  Card,
  Checkbox,
  FieldError,
  Input,
  Label,
  Listbox,
  StatusBadge,
  Textarea,
} from "@/components/ui";

type DeliveryMethod = "graph" | "smtp";

type TransportForm = {
  delivery_method: DeliveryMethod;
  graph_tenant_id: string;
  graph_client_id: string;
  graph_client_secret: string;
  host: string;
  port: number;
  username: string;
  password: string;
  from_email: string;
  from_name: string;
  use_tls: boolean;
};

type EmailForm = {
  enabled: boolean;
  emails: string;
  failure_threshold: number;
  reminder_minutes: number;
  down_subject: string;
  down_body: string;
  recovery_subject: string;
  recovery_body: string;
};

const transportOptions = [
  { value: "graph", label: "Microsoft 365 Graph (recomendado)" },
  { value: "smtp", label: "SMTP legado / relay interno" },
] satisfies { value: DeliveryMethod; label: string }[];

const defaultEmailForm: EmailForm = {
  enabled: true,
  emails: "",
  failure_threshold: 3,
  reminder_minutes: 30,
  down_subject: "[FORA DO AR] {monitor_name}",
  down_body:
    "O monitor {monitor_name} está fora do ar.\n\nURL: {url}\nErro: {error}\nFalhas consecutivas: {failure_count}\nDashboard: {dashboard_url}",
  recovery_subject: "[RESTABELECIDO] {monitor_name}",
  recovery_body:
    "O monitor {monitor_name} voltou ao ar.\n\nURL: {url}\nDuração: {duration}\nDashboard: {dashboard_url}",
};

function parseEmails(value: string): string[] {
  return value
    .split(/[;,\n]+/)
    .map((email) => email.trim())
    .filter(Boolean);
}

function errorMessage(error: unknown, fallback: string): string {
  return error instanceof ApiError ? error.message : fallback;
}

export function EmailSettingsPage() {
  const qc = useQueryClient();
  const [transportForm, setTransportForm] = useState<TransportForm>({
    delivery_method: "graph",
    graph_tenant_id: "",
    graph_client_id: "",
    graph_client_secret: "",
    host: "smtp.office365.com",
    port: 587,
    username: "",
    password: "",
    from_email: "",
    from_name: "AmbushSystem",
    use_tls: true,
  });
  const [testEmail, setTestEmail] = useState("");
  const [transportError, setTransportError] = useState<string | null>(null);
  const [transportOk, setTransportOk] = useState<string | null>(null);

  const [selectedMonitorId, setSelectedMonitorId] = useState<string>("");
  const [emailForm, setEmailForm] = useState<EmailForm>(defaultEmailForm);
  const [configError, setConfigError] = useState<string | null>(null);
  const [configOk, setConfigOk] = useState<string | null>(null);

  const dashboard = useQuery({ queryKey: ["dashboard"], queryFn: api.dashboard });
  const smtp = useQuery({ queryKey: ["smtp"], queryFn: api.smtp });
  const configs = useQuery({ queryKey: ["email-configs"], queryFn: api.emailConfigs });

  const monitorOptions = useMemo(
    () =>
      (dashboard.data?.monitors ?? []).map((monitor) => ({
        value: String(monitor.id),
        label: monitor.name,
      })),
    [dashboard.data],
  );
  const monitorNameById = useMemo(() => {
    return new Map(
      (dashboard.data?.monitors ?? []).map((monitor) => [monitor.id, monitor.name]),
    );
  }, [dashboard.data]);

  useEffect(() => {
    if (!selectedMonitorId && monitorOptions.length > 0) {
      setSelectedMonitorId(monitorOptions[0].value);
    }
  }, [monitorOptions, selectedMonitorId]);

  useEffect(() => {
    if (!smtp.data) return;
    setTransportForm({
      delivery_method: smtp.data.delivery_method === "smtp" ? "smtp" : "graph",
      graph_tenant_id: smtp.data.graph_tenant_id ?? "",
      graph_client_id: smtp.data.graph_client_id ?? "",
      graph_client_secret: "",
      host: smtp.data.host || "smtp.office365.com",
      port: smtp.data.port,
      username: smtp.data.username ?? "",
      password: "",
      from_email: smtp.data.from_email,
      from_name: smtp.data.from_name,
      use_tls: smtp.data.use_tls,
    });
  }, [smtp.data]);

  useEffect(() => {
    const monitorId = Number(selectedMonitorId);
    if (!monitorId) return;
    const existing = configs.data?.find((config) => config.monitor_id === monitorId);
    if (!existing) {
      setEmailForm(defaultEmailForm);
      return;
    }
    setEmailForm({
      enabled: existing.enabled,
      emails: existing.emails.join("\n"),
      failure_threshold: existing.failure_threshold,
      reminder_minutes: existing.reminder_minutes,
      down_subject: existing.down_subject,
      down_body: existing.down_body,
      recovery_subject: existing.recovery_subject,
      recovery_body: existing.recovery_body,
    });
  }, [configs.data, selectedMonitorId]);

  const saveTransport = useMutation({
    mutationFn: (payload: SmtpSettingsUpdate) => api.updateSmtp(payload),
    onSuccess: async () => {
      setTransportError(null);
      setTransportOk("Configuração de envio salva.");
      await qc.invalidateQueries({ queryKey: ["smtp"] });
    },
    onError: (error) => {
      setTransportOk(null);
      setTransportError(errorMessage(error, "Falha ao salvar configuração de envio"));
    },
  });

  const sendTest = useMutation({
    mutationFn: () => api.testSmtp(testEmail),
    onSuccess: (result) => {
      setTransportError(null);
      setTransportOk(result.detail);
    },
    onError: (error) => {
      setTransportOk(null);
      setTransportError(errorMessage(error, "Falha ao enviar e-mail de teste"));
    },
  });

  const saveConfig = useMutation({
    mutationFn: ({
      monitorId,
      payload,
    }: {
      monitorId: number;
      payload: EmailNotificationConfigPayload;
    }) => api.upsertEmailConfig(monitorId, payload),
    onSuccess: async () => {
      setConfigError(null);
      setConfigOk("Configuração de e-mail do monitor salva.");
      await qc.invalidateQueries({ queryKey: ["email-configs"] });
    },
    onError: (error) => {
      setConfigOk(null);
      setConfigError(errorMessage(error, "Falha ao salvar configuração"));
    },
  });

  const deleteConfig = useMutation({
    mutationFn: (monitorId: number) => api.deleteEmailConfig(monitorId),
    onSuccess: async (_, monitorId) => {
      setConfigError(null);
      setConfigOk("Configuração de correspondência excluída.");
      if (String(monitorId) === selectedMonitorId) {
        setEmailForm(defaultEmailForm);
      }
      await qc.invalidateQueries({ queryKey: ["email-configs"] });
    },
    onError: (error) => {
      setConfigOk(null);
      setConfigError(errorMessage(error, "Falha ao excluir configuração"));
    },
  });

  function editConfig(monitorId: number) {
    setSelectedMonitorId(String(monitorId));
    setConfigOk("Configuração carregada para edição.");
    setConfigError(null);
  }

  function submitTransport(event: FormEvent) {
    event.preventDefault();
    setTransportError(null);
    setTransportOk(null);

    if (!transportForm.from_email) {
      setTransportError("Informe o remetente padrão.");
      return;
    }

    if (transportForm.delivery_method === "graph") {
      if (!transportForm.graph_tenant_id || !transportForm.graph_client_id) {
        setTransportError("Informe Tenant ID e Client ID do App Registration.");
        return;
      }
      if (!smtp.data?.has_graph_client_secret && !transportForm.graph_client_secret) {
        setTransportError("Informe o Client Secret do Microsoft 365.");
        return;
      }
    }

    if (transportForm.delivery_method === "smtp" && !transportForm.host) {
      setTransportError("Informe o host SMTP.");
      return;
    }

    saveTransport.mutate({
      delivery_method: transportForm.delivery_method,
      graph_tenant_id: transportForm.graph_tenant_id || null,
      graph_client_id: transportForm.graph_client_id || null,
      graph_client_secret: transportForm.graph_client_secret || null,
      host: transportForm.host,
      port: transportForm.port,
      username: transportForm.username || null,
      password: transportForm.password || null,
      from_email: transportForm.from_email,
      from_name: transportForm.from_name,
      use_tls: transportForm.use_tls,
    });
  }

  function submitConfig(event: FormEvent) {
    event.preventDefault();
    const monitorId = Number(selectedMonitorId);
    const emails = parseEmails(emailForm.emails);
    setConfigError(null);
    setConfigOk(null);

    if (!monitorId) {
      setConfigError("Selecione um monitor.");
      return;
    }
    if (emails.length === 0) {
      setConfigError("Informe pelo menos um destinatário.");
      return;
    }
    if (emailForm.failure_threshold < 1) {
      setConfigError("O limite mínimo é 1 checagem.");
      return;
    }
    if (emailForm.reminder_minutes < 0) {
      setConfigError("O reenvio mínimo é 0 minutos.");
      return;
    }

    saveConfig.mutate({
      monitorId,
      payload: {
        monitor_id: monitorId,
        enabled: emailForm.enabled,
        emails,
        failure_threshold: emailForm.failure_threshold,
        reminder_minutes: emailForm.reminder_minutes,
        down_subject: emailForm.down_subject,
        down_body: emailForm.down_body,
        recovery_subject: emailForm.recovery_subject,
        recovery_body: emailForm.recovery_body,
      },
    });
  }

  const usingGraph = transportForm.delivery_method === "graph";

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold text-zinc-100">E-mail</h1>
        <p className="text-xs text-zinc-500">
          Microsoft 365 Graph é o método recomendado internamente; SMTP fica como fallback.
        </p>
      </div>

      <div className="grid items-start gap-4 xl:grid-cols-[460px_1fr]">
        <Card>
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-semibold text-zinc-100">Conexão de envio</h2>
              <p className="text-xs text-zinc-500">
                App-only Graph com Mail.Send ou SMTP legado.
              </p>
            </div>
            <StatusBadge tone={usingGraph ? "emerald" : "amber"}>
              {usingGraph ? "Graph" : "SMTP"}
            </StatusBadge>
          </div>

          <form className="space-y-3" onSubmit={submitTransport}>
            <div>
              <Label htmlFor="delivery-method">Método</Label>
              <Listbox
                id="delivery-method"
                value={transportForm.delivery_method}
                options={transportOptions}
                onChange={(value) =>
                  setTransportForm((form) => ({ ...form, delivery_method: value }))
                }
                aria-label="Método de envio"
              />
            </div>

            <div>
              <Label htmlFor="from-email">Remetente padrão</Label>
              <Input
                id="from-email"
                value={transportForm.from_email}
                onChange={(event) =>
                  setTransportForm((form) => ({ ...form, from_email: event.target.value }))
                }
                placeholder="no-reply@dominio.com"
              />
              <p className="mt-1 text-xs text-zinc-500">
                No Graph, este endereço precisa existir no tenant e ter permissão de envio.
              </p>
            </div>
            <div>
              <Label htmlFor="from-name">Nome do remetente</Label>
              <Input
                id="from-name"
                value={transportForm.from_name}
                onChange={(event) =>
                  setTransportForm((form) => ({ ...form, from_name: event.target.value }))
                }
              />
            </div>

            {usingGraph ? (
              <div className="space-y-3 rounded-xl border border-emerald-900/50 bg-emerald-950/10 p-3">
                <div>
                  <Label htmlFor="tenant-id">O365 Tenant ID</Label>
                  <Input
                    id="tenant-id"
                    value={transportForm.graph_tenant_id}
                    onChange={(event) =>
                      setTransportForm((form) => ({
                        ...form,
                        graph_tenant_id: event.target.value,
                      }))
                    }
                    placeholder="ID do diretório no Azure AD"
                  />
                </div>
                <div>
                  <Label htmlFor="client-id">O365 Client ID</Label>
                  <Input
                    id="client-id"
                    value={transportForm.graph_client_id}
                    onChange={(event) =>
                      setTransportForm((form) => ({
                        ...form,
                        graph_client_id: event.target.value,
                      }))
                    }
                    placeholder="App registration client id"
                  />
                </div>
                <div>
                  <Label htmlFor="client-secret">O365 Client Secret</Label>
                  <Input
                    id="client-secret"
                    type="password"
                    value={transportForm.graph_client_secret}
                    onChange={(event) =>
                      setTransportForm((form) => ({
                        ...form,
                        graph_client_secret: event.target.value,
                      }))
                    }
                    placeholder={
                      smtp.data?.has_graph_client_secret
                        ? "Secret já salvo (preencha para trocar)"
                        : "Client secret"
                    }
                  />
                </div>
                <p className="text-xs text-zinc-500">
                  Requer permissão Application <span className="font-mono">Mail.Send</span> e
                  consentimento administrativo no Azure.
                </p>
              </div>
            ) : (
              <div className="space-y-3 rounded-xl border border-amber-900/50 bg-amber-950/10 p-3">
                <div>
                  <Label htmlFor="smtp-host">SMTP Host</Label>
                  <Input
                    id="smtp-host"
                    value={transportForm.host}
                    onChange={(event) =>
                      setTransportForm((form) => ({ ...form, host: event.target.value }))
                    }
                    placeholder="smtp.office365.com"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label htmlFor="smtp-port">Porta</Label>
                    <Input
                      id="smtp-port"
                      type="number"
                      value={transportForm.port}
                      onChange={(event) =>
                        setTransportForm((form) => ({
                          ...form,
                          port: Number(event.target.value),
                        }))
                      }
                    />
                  </div>
                  <div className="pt-6">
                    <Checkbox
                      label="STARTTLS/TLS"
                      checked={transportForm.use_tls}
                      onChange={(event) =>
                        setTransportForm((form) => ({
                          ...form,
                          use_tls: event.target.checked,
                        }))
                      }
                    />
                  </div>
                </div>
                <div>
                  <Label htmlFor="smtp-user">SMTP User</Label>
                  <Input
                    id="smtp-user"
                    value={transportForm.username}
                    onChange={(event) =>
                      setTransportForm((form) => ({ ...form, username: event.target.value }))
                    }
                    placeholder="usuario@dominio.com"
                  />
                </div>
                <div>
                  <Label htmlFor="smtp-password">SMTP Pass</Label>
                  <Input
                    id="smtp-password"
                    type="password"
                    value={transportForm.password}
                    onChange={(event) =>
                      setTransportForm((form) => ({ ...form, password: event.target.value }))
                    }
                    placeholder={
                      smtp.data?.has_password
                        ? "Senha já salva (preencha para trocar)"
                        : "Senha ou app password"
                    }
                  />
                </div>
              </div>
            )}

            <Button type="submit" variant="primary" disabled={saveTransport.isPending}>
              Salvar conexão
            </Button>
          </form>

          <div className="mt-4 border-t border-zinc-800 pt-4">
            <Label htmlFor="email-test">E-mail de teste</Label>
            <div className="flex gap-2">
              <Input
                id="email-test"
                value={testEmail}
                onChange={(event) => setTestEmail(event.target.value)}
                placeholder="voce@dominio.com"
              />
              <Button disabled={!testEmail || sendTest.isPending} onClick={() => sendTest.mutate()}>
                <Send className="size-4" />
                Testar
              </Button>
            </div>
          </div>

          <FieldError>{transportError}</FieldError>
          {transportOk && <p className="mt-2 text-xs text-emerald-400">{transportOk}</p>}
        </Card>

        <Card>
          <div className="mb-4 flex items-center gap-3">
            <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-2 text-zinc-300">
              <Mail className="size-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-zinc-100">Alerta por monitor</h2>
              <p className="text-xs text-zinc-500">
                Destinatários, limite de falhas e texto do e-mail.
              </p>
            </div>
          </div>

          <div className="mb-4 rounded-xl border border-zinc-800 bg-zinc-950/30 p-3">
            <div className="mb-3 flex items-center justify-between gap-3">
              <div>
                <h3 className="text-sm font-semibold text-zinc-100">
                  Lista de correspondência
                </h3>
                <p className="text-xs text-zinc-500">
                  Monitores que já possuem destinatários configurados.
                </p>
              </div>
              <StatusBadge tone="zinc">{configs.data?.length ?? 0}</StatusBadge>
            </div>

            {configs.data?.length ? (
              <div className="space-y-2">
                {configs.data.map((config) => (
                  <div
                    key={config.id}
                    className="rounded-lg border border-zinc-800 bg-[#151518] p-3"
                  >
                    <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-medium text-zinc-100">
                            {monitorNameById.get(config.monitor_id) ??
                              `Monitor #${config.monitor_id}`}
                          </span>
                          <StatusBadge tone={config.enabled ? "emerald" : "zinc"}>
                            {config.enabled ? "Ativo" : "Inativo"}
                          </StatusBadge>
                          <span className="text-xs text-zinc-500">
                            após {config.failure_threshold} falhas · reenvio{" "}
                            {config.reminder_minutes > 0
                              ? `${config.reminder_minutes} min`
                              : "desativado"}
                          </span>
                        </div>
                        <div className="mt-2 flex flex-wrap gap-1.5">
                          {config.emails.map((email) => (
                            <span
                              key={email}
                              className="rounded-md border border-zinc-800 bg-zinc-900 px-2 py-1 font-mono text-xs text-zinc-300"
                            >
                              {email}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div className="flex shrink-0 gap-2">
                        <Button onClick={() => editConfig(config.monitor_id)}>
                          Editar
                        </Button>
                        <Button
                          variant="danger"
                          disabled={deleteConfig.isPending}
                          onClick={() => {
                            if (
                              window.confirm(
                                "Excluir a correspondência deste monitor?",
                              )
                            ) {
                              deleteConfig.mutate(config.monitor_id);
                            }
                          }}
                        >
                          Excluir
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="rounded-lg border border-dashed border-zinc-800 p-3 text-sm text-zinc-500">
                Nenhuma correspondência configurada ainda. Salve um monitor abaixo para
                ele aparecer nesta lista.
              </p>
            )}
          </div>

          <form className="space-y-3" onSubmit={submitConfig}>
            <div>
              <Label htmlFor="email-monitor">Monitor</Label>
              {monitorOptions.length > 0 ? (
                <Listbox
                  id="email-monitor"
                  value={selectedMonitorId}
                  options={monitorOptions}
                  onChange={setSelectedMonitorId}
                  aria-label="Monitor"
                />
              ) : (
                <p className="text-sm text-zinc-500">Nenhum monitor cadastrado.</p>
              )}
            </div>

            <Checkbox
              label="Ativar alertas de e-mail para este monitor"
              checked={emailForm.enabled}
              onChange={(event) =>
                setEmailForm((form) => ({ ...form, enabled: event.target.checked }))
              }
            />

            <div className="grid gap-3 md:grid-cols-[160px_180px_1fr]">
              <div>
                <Label htmlFor="failure-threshold">Enviar após</Label>
                <Input
                  id="failure-threshold"
                  type="number"
                  min={1}
                  max={20}
                  value={emailForm.failure_threshold}
                  onChange={(event) =>
                    setEmailForm((form) => ({
                      ...form,
                      failure_threshold: Number(event.target.value),
                    }))
                  }
                />
                <p className="mt-1 text-xs text-zinc-500">checagens DOWN seguidas</p>
              </div>
              <div>
                <Label htmlFor="reminder-minutes">Reenviar a cada</Label>
                <Input
                  id="reminder-minutes"
                  type="number"
                  min={0}
                  max={1440}
                  value={emailForm.reminder_minutes}
                  onChange={(event) =>
                    setEmailForm((form) => ({
                      ...form,
                      reminder_minutes: Number(event.target.value),
                    }))
                  }
                />
                <p className="mt-1 text-xs text-zinc-500">minutos (0 desativa)</p>
              </div>
              <div>
                <Label htmlFor="emails">Destinatários</Label>
                <Textarea
                  id="emails"
                  value={emailForm.emails}
                  onChange={(event) =>
                    setEmailForm((form) => ({ ...form, emails: event.target.value }))
                  }
                  placeholder={"ti@dominio.com\njuridico@dominio.com"}
                  className="min-h-20 font-mono text-xs"
                />
              </div>
            </div>

            <div className="grid gap-3 lg:grid-cols-2">
              <div className="space-y-3">
                <div>
                  <Label htmlFor="down-subject">Assunto quando cair</Label>
                  <Input
                    id="down-subject"
                    value={emailForm.down_subject}
                    onChange={(event) =>
                      setEmailForm((form) => ({ ...form, down_subject: event.target.value }))
                    }
                  />
                </div>
                <div>
                  <Label htmlFor="down-body">Corpo quando cair</Label>
                  <Textarea
                    id="down-body"
                    value={emailForm.down_body}
                    onChange={(event) =>
                      setEmailForm((form) => ({ ...form, down_body: event.target.value }))
                    }
                    className="min-h-44 font-mono text-xs"
                  />
                </div>
              </div>
              <div className="space-y-3">
                <div>
                  <Label htmlFor="recovery-subject">Assunto de recuperação</Label>
                  <Input
                    id="recovery-subject"
                    value={emailForm.recovery_subject}
                    onChange={(event) =>
                      setEmailForm((form) => ({
                        ...form,
                        recovery_subject: event.target.value,
                      }))
                    }
                  />
                </div>
                <div>
                  <Label htmlFor="recovery-body">Corpo de recuperação</Label>
                  <Textarea
                    id="recovery-body"
                    value={emailForm.recovery_body}
                    onChange={(event) =>
                      setEmailForm((form) => ({ ...form, recovery_body: event.target.value }))
                    }
                    className="min-h-44 font-mono text-xs"
                  />
                </div>
              </div>
            </div>

            <p className="text-xs text-zinc-500">
              Variáveis disponíveis: {"{monitor_name}"}, {"{url}"}, {"{error}"},{" "}
              {"{status_code}"}, {"{failure_count}"}, {"{duration}"},{" "}
              {"{dashboard_url}"}.
            </p>

            <FieldError>{configError}</FieldError>
            {configOk && <p className="text-xs text-emerald-400">{configOk}</p>}

            <Button
              type="submit"
              variant="primary"
              disabled={saveConfig.isPending || !selectedMonitorId}
            >
              Salvar alerta do monitor
            </Button>
          </form>
        </Card>
      </div>
    </div>
  );
}
