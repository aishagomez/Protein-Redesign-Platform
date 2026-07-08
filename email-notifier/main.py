import os
import smtplib
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, EmailStr

app = FastAPI(title="email-notifier")

INTERNAL_TOKEN = os.environ.get("INTERNAL_TOKEN", "internal-secret-change-me")
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "aishaggch13@gmail.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "jtxm kxqi loby ause")
SMTP_FROM = os.environ.get("SMTP_FROM", SMTP_USER or "no-reply@example.com")
SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "true").strip().lower() in {"1", "true", "yes"}


class EmailRequest(BaseModel):
    to_email: EmailStr
    subject: str
    message: str
    pipeline_id: int | None = None
    status: str = "success"   # "success" | "error" | "warning" | "info"


def _verify_internal(x_internal_token: str = Header(...)):
    if x_internal_token != INTERNAL_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid internal token")


STATUS_CONFIG = {
    "success": {
        "color": "#00C896",
        "bg": "#E6FBF5",
        "border": "#00C896",
        "icon": "✓",
        "label": "Completado",
    },
    "error": {
        "color": "#E53E3E",
        "bg": "#FFF5F5",
        "border": "#E53E3E",
        "icon": "✕",
        "label": "Error",
    },
    "warning": {
        "color": "#D97706",
        "bg": "#FFFBEB",
        "border": "#D97706",
        "icon": "⚠",
        "label": "Advertencia",
    },
    "info": {
        "color": "#3B82F6",
        "bg": "#EFF6FF",
        "border": "#3B82F6",
        "icon": "ℹ",
        "label": "Info",
    },
}


def _build_html(payload: EmailRequest) -> str:
    cfg = STATUS_CONFIG.get(payload.status, STATUS_CONFIG["info"])

    timestamp = datetime.now().strftime("%d %b %Y · %H:%M")
    message_html = payload.message.replace("\n", "<br>")

    pipeline_badge = (
        f'<span style="background:#ede8f6;color:#6a5a96;'
        f'font-size:11px;font-family:monospace;padding:2px 8px;'
        f'border-radius:999px;margin-left:8px;">#{payload.pipeline_id}</span>'
        if payload.pipeline_id is not None
        else ""
    )

    return f"""
<html>
<body style="margin:0;padding:0;background:#f4f1f8;
             font-family:'Segoe UI','IBM Plex Sans',sans-serif;
             color:#3d3554;">

<table width="100%" cellpadding="0" cellspacing="0"
       style="padding:40px 16px;">
<tr>
<td align="center">

<table width="560" cellpadding="0" cellspacing="0"
       style="background:#ffffff;border:1px solid #e0d9ed;
              border-radius:16px;box-shadow:0 1px 6px rgba(100,80,140,0.08);
              overflow:hidden;">

<!-- top bar -->
<tr>
<td style="background:{cfg['color']};height:4px;"></td>
</tr>

<!-- header -->
<tr>
<td style="padding:28px 32px 16px;">
  <table width="100%">
    <tr>
      <td style="font-size:11px;letter-spacing:1.5px;
                 color:#8d82a8;text-transform:uppercase;">
        Pipeline Notifier
      </td>
      <td align="right" style="font-size:11px;color:#8d82a8;">
        {timestamp}
      </td>
    </tr>
  </table>
</td>
</tr>

<!-- title -->
<tr>
<td style="padding:0 32px 20px;">
  <div style="margin-bottom:12px;">
    <span style="background:{cfg['bg']};
                 border:1px solid {cfg['border']};
                 color:{cfg['color']};
                 padding:4px 12px;
                 border-radius:999px;
                 font-size:12px;
                 font-weight:600;">
      {cfg['icon']} {cfg['label']}
    </span>
  </div>

  <h1 style="margin:0;font-size:20px;color:#3d3554;">
    {payload.subject}{pipeline_badge}
  </h1>
</td>
</tr>

<!-- divider -->
<tr>
<td style="padding:0 32px;">
  <div style="height:1px;background:#e0d9ed;"></div>
</td>
</tr>

<!-- body -->
<tr>
<td style="padding:24px 32px;">
  <p style="margin:0;font-size:14px;line-height:1.6;color:#5c5278;">
    {message_html}
  </p>
</td>
</tr>

<!-- footer -->
<tr>
<td style="background:#faf8fd;border-top:1px solid #e0d9ed;
           padding:18px 32px;">
  <p style="margin:0;font-size:12px;color:#8d82a8;">
    Generado automáticamente por el sistema de pipelines.
  </p>
</td>
</tr>

</table>

</td>
</tr>
</table>

</body>
</html>
"""


def _build_plaintext(payload: EmailRequest) -> str:
    cfg = STATUS_CONFIG.get(payload.status, STATUS_CONFIG["info"])
    pipeline_info = f" (Pipeline #{payload.pipeline_id})" if payload.pipeline_id is not None else ""
    timestamp = datetime.now().strftime("%d %b %Y %H:%M")
    return (
        f"[{cfg['label'].upper()}]{pipeline_info}\n"
        f"{payload.subject}\n"
        f"{'─' * 40}\n\n"
        f"{payload.message}\n\n"
        f"{'─' * 40}\n"
        f"Generado automáticamente · {timestamp}"
    )


def _send_via_smtp(payload: EmailRequest):
    msg = MIMEMultipart("alternative")
    msg["From"] = SMTP_FROM
    msg["To"] = payload.to_email
    msg["Subject"] = payload.subject

    # Attach plain text first, then HTML (clients prefer the last part)
    msg.attach(MIMEText(_build_plaintext(payload), "plain", "utf-8"))
    msg.attach(MIMEText(_build_html(payload), "html", "utf-8"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
        if SMTP_USE_TLS:
            smtp.starttls()
        if SMTP_USER:
            smtp.login(SMTP_USER, SMTP_PASSWORD)
        smtp.send_message(msg)


@app.get("/health")
def health():
    return {"ok": True, "smtp_configured": bool(SMTP_HOST)}


@app.post("/send", dependencies=[Depends(_verify_internal)])
def send_email(payload: EmailRequest):
    if SMTP_HOST:
        _send_via_smtp(payload)
        return {"ok": True, "mode": "smtp"}

    print("[email-notifier] SMTP not configured; logging simulated email")
    print(f"  to       : {payload.to_email}")
    print(f"  subject  : {payload.subject}")
    print(f"  status   : {payload.status}")
    print(f"  pipeline : {payload.pipeline_id}")
    print(f"  message  : {payload.message}")
    return {"ok": True, "mode": "log"}