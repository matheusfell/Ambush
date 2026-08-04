"""Templates HTML de e-mail de alerta."""
# ruff: noqa: E501

from __future__ import annotations

from dataclasses import dataclass

from app.config import get_settings


@dataclass(frozen=True, slots=True)
class EmailContent:
    subject: str
    html_body: str


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _asset_url(filename: str) -> str:
    base = get_settings().app_base_url.rstrip("/")
    return f"{base}/{filename.lstrip('/')}"


def _link(url: str, label: str | None = None) -> str:
    safe_url = _escape(url)
    safe_label = _escape(label or url)
    return f'<a href="{safe_url}" style="color:#38bdf8;text-decoration:none">{safe_label}</a>'


def _base_html(
    *,
    title: str,
    badge_color: str,
    rows: list[tuple[str, str]],
    body_text: str | None = None,
    cta_url: str | None = None,
) -> str:
    logo_url = _asset_url("ambush.png")
    rows_html = "".join(
        "<tr>"
        "<td style='padding:10px 0;color:#71717a;font-size:12px;"
        "text-transform:uppercase;letter-spacing:.08em;width:165px'>"
        f"{_escape(label)}</td>"
        "<td style='padding:10px 0;color:#e4e4e7;font-size:14px;line-height:1.45'>"
        f"{value}</td>"
        "</tr>"
        for label, value in rows
    )
    body_html = ""
    if body_text:
        body_html = (
            "<div style='margin:18px 0 4px;padding:16px;border:1px solid #27272a;"
            "border-radius:14px;background:#18181b;color:#d4d4d8;font-size:14px;"
            "line-height:1.6;white-space:pre-line'>"
            f"{_escape(body_text)}</div>"
        )

    cta_html = ""
    if cta_url:
        cta_html = (
            "<tr><td style='padding:22px 28px 28px'>"
            f"<a href='{_escape(cta_url)}' "
            "style='display:inline-block;border-radius:10px;background:#10b981;"
            "color:#052e1c;text-decoration:none;font-weight:700;font-size:13px;"
            "padding:11px 16px'>Abrir dashboard</a>"
            "</td></tr>"
        )

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
  <body style="margin:0;padding:0;background:#0c0c0f;font-family:Inter,Segoe UI,Arial,sans-serif">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#0c0c0f;padding:28px 16px">
      <tr>
        <td align="center">
          <table width="640" cellpadding="0" cellspacing="0" style="max-width:640px;width:100%;border:1px solid #27272a;border-radius:22px;overflow:hidden;background:#121216">
            <tr>
              <td style="padding:0;background:linear-gradient(135deg,#18181b 0%,#0c0c0f 58%,#052e2b 100%)">
                <table width="100%" cellpadding="0" cellspacing="0">
                  <tr>
                    <td style="padding:24px 28px">
                      <table width="100%" cellpadding="0" cellspacing="0">
                        <tr>
                          <td style="vertical-align:middle">
                            <img src="{_escape(logo_url)}" alt="AmbushSystem" width="48" height="48" style="display:block;border-radius:14px;background:#0c0c0f;border:1px solid #3f3f46;object-fit:contain" />
                          </td>
                          <td align="right" style="vertical-align:middle">
                            <span style="display:inline-block;border-radius:999px;background:{badge_color};color:#0c0c0f;font-size:12px;font-weight:800;letter-spacing:.08em;padding:7px 11px;text-transform:uppercase">{_escape(title)}</span>
                          </td>
                        </tr>
                      </table>
                      <div style="margin-top:22px;color:#fafafa;font-size:24px;font-weight:800;letter-spacing:-.03em">AmbushSystem</div>
                      <div style="margin-top:6px;color:#a1a1aa;font-size:13px;line-height:1.5">Monitoramento interno de disponibilidade</div>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td style="padding:24px 28px 4px">
                <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse">
                  {rows_html}
                </table>
                {body_html}
              </td>
            </tr>
            {cta_html}
            <tr>
              <td style="border-top:1px solid #27272a;padding:16px 28px;color:#71717a;font-size:12px;line-height:1.5">
                Enviado automaticamente pelo AmbushSystem. Verifique o dashboard antes de acionar times externos.
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>"""


def build_custom_email(
    *,
    subject: str,
    body: str,
    title: str,
    badge_color: str,
    dashboard_url: str | None = None,
) -> EmailContent:
    return EmailContent(
        subject=subject,
        html_body=_base_html(
            title=title,
            badge_color=badge_color,
            rows=[],
            body_text=body,
            cta_url=dashboard_url,
        ),
    )


def build_down_email(
    *,
    monitor_name: str,
    url: str,
    started_at_local: str,
    error: str,
    duration_so_far: str,
    dashboard_url: str,
) -> EmailContent:
    return EmailContent(
        subject=f"[FORA DO AR] {monitor_name}",
        html_body=_base_html(
            title="FORA DO AR",
            badge_color="#f87171",
            cta_url=dashboard_url,
            rows=[
                ("Monitor", _escape(monitor_name)),
                ("URL", _link(url)),
                ("Início", _escape(started_at_local)),
                ("Erro / status", _escape(error)),
                ("Duração até agora", _escape(duration_so_far)),
                ("Dashboard", _link(dashboard_url)),
            ],
        ),
    )


def build_recovery_email(
    *,
    monitor_name: str,
    url: str,
    started_at_local: str,
    resolved_at_local: str,
    duration: str,
    dashboard_url: str,
) -> EmailContent:
    return EmailContent(
        subject=f"[RESTABELECIDO] {monitor_name}",
        html_body=_base_html(
            title="RESTABELECIDO",
            badge_color="#4ade80",
            cta_url=dashboard_url,
            rows=[
                ("Monitor", _escape(monitor_name)),
                ("URL", _link(url)),
                ("Início da falha", _escape(started_at_local)),
                ("Restabelecido em", _escape(resolved_at_local)),
                ("Duração total", _escape(duration)),
                ("Dashboard", _link(dashboard_url)),
            ],
        ),
    )


def build_degraded_email(
    *,
    monitor_name: str,
    url: str,
    checked_at_local: str,
    detail: str,
    dashboard_url: str,
) -> EmailContent:
    return EmailContent(
        subject=f"[DEGRADADO] {monitor_name}",
        html_body=_base_html(
            title="DEGRADADO",
            badge_color="#fbbf24",
            cta_url=dashboard_url,
            rows=[
                ("Monitor", _escape(monitor_name)),
                ("URL", _link(url)),
                ("Horário", _escape(checked_at_local)),
                ("Detalhe", _escape(detail)),
                ("Dashboard", _link(dashboard_url)),
            ],
        ),
    )


def build_reminder_email(
    *,
    monitor_name: str,
    url: str,
    started_at_local: str,
    error: str,
    duration_so_far: str,
    failure_count: int,
    dashboard_url: str,
) -> EmailContent:
    return EmailContent(
        subject=f"[AINDA FORA] {monitor_name}",
        html_body=_base_html(
            title="AINDA FORA DO AR",
            badge_color="#fb923c",
            cta_url=dashboard_url,
            rows=[
                ("Monitor", _escape(monitor_name)),
                ("URL", _link(url)),
                ("Início", _escape(started_at_local)),
                ("Erro / status", _escape(error)),
                ("Duração até agora", _escape(duration_so_far)),
                ("Falhas consecutivas", str(failure_count)),
                ("Dashboard", _link(dashboard_url)),
            ],
        ),
    )
