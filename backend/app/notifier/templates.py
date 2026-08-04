"""Templates HTML de e-mail de alerta."""

from __future__ import annotations

from dataclasses import dataclass


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


def _base_html(*, title: str, badge_color: str, rows: list[tuple[str, str]]) -> str:
    rows_html = "".join(
        f"<tr><td style='padding:6px 12px;color:#94a3b8;width:160px'>{_escape(k)}</td>"
        f"<td style='padding:6px 12px;color:#e2e8f0'>{v}</td></tr>"
        for k, v in rows
    )
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<body style="margin:0;padding:0;background:#0f172a;font-family:Segoe UI,Arial,sans-serif">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0f172a;padding:24px">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0"
             style="background:#1e293b;border-radius:8px;overflow:hidden">
        <tr>
          <td style="padding:20px 24px;border-bottom:1px solid #334155">
            <span style="display:inline-block;padding:4px 10px;border-radius:4px;
                         background:{badge_color};color:#0f172a;font-weight:700;
                         font-size:12px;letter-spacing:0.04em">{_escape(title)}</span>
            <div style="margin-top:12px;color:#f8fafc;font-size:18px;font-weight:600">
              AmbushSystem
            </div>
          </td>
        </tr>
        <tr>
          <td style="padding:16px 12px">
            <table width="100%" cellpadding="0" cellspacing="0">{rows_html}</table>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


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
            rows=[
                ("Monitor", _escape(monitor_name)),
                ("URL", f'<a href="{_escape(url)}" style="color:#38bdf8">{_escape(url)}</a>'),
                ("Início", _escape(started_at_local)),
                ("Erro / status", _escape(error)),
                ("Duração até agora", _escape(duration_so_far)),
                (
                    "Dashboard",
                    f'<a href="{_escape(dashboard_url)}" style="color:#38bdf8">'
                    f"{_escape(dashboard_url)}</a>",
                ),
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
            rows=[
                ("Monitor", _escape(monitor_name)),
                ("URL", f'<a href="{_escape(url)}" style="color:#38bdf8">{_escape(url)}</a>'),
                ("Início da falha", _escape(started_at_local)),
                ("Restabelecido em", _escape(resolved_at_local)),
                ("Duração total", _escape(duration)),
                (
                    "Dashboard",
                    f'<a href="{_escape(dashboard_url)}" style="color:#38bdf8">'
                    f"{_escape(dashboard_url)}</a>",
                ),
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
            rows=[
                ("Monitor", _escape(monitor_name)),
                ("URL", f'<a href="{_escape(url)}" style="color:#38bdf8">{_escape(url)}</a>'),
                ("Horário", _escape(checked_at_local)),
                ("Detalhe", _escape(detail)),
                (
                    "Dashboard",
                    f'<a href="{_escape(dashboard_url)}" style="color:#38bdf8">'
                    f"{_escape(dashboard_url)}</a>",
                ),
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
            rows=[
                ("Monitor", _escape(monitor_name)),
                ("URL", f'<a href="{_escape(url)}" style="color:#38bdf8">{_escape(url)}</a>'),
                ("Início", _escape(started_at_local)),
                ("Erro / status", _escape(error)),
                ("Duração até agora", _escape(duration_so_far)),
                ("Falhas consecutivas", str(failure_count)),
                (
                    "Dashboard",
                    f'<a href="{_escape(dashboard_url)}" style="color:#38bdf8">'
                    f"{_escape(dashboard_url)}</a>",
                ),
            ],
        ),
    )
