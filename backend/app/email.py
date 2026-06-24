"""
JurisAI — Email Service via Resend
Handles transactional emails: invitations, password resets.
"""
import os
import resend

resend.api_key = os.getenv("RESEND_API_KEY", "")

PLATFORM_URL = os.getenv("PLATFORM_URL", "https://jurisai.vercel.app")
FROM_EMAIL = "onboarding@resend.dev"   # sandbox — substituir por domínio verificado em prod


def _invitation_html(name: str, token: str) -> str:
    activate_url = f"{PLATFORM_URL}/invite/{token}"
    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Bem-vindo ao JurisAI</title>
</head>
<body style="margin:0;padding:0;background:#f5f4f0;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f4f0;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 16px rgba(0,0,0,0.08);">

          <!-- Header -->
          <tr>
            <td style="background:#7a2e2e;padding:28px 40px;text-align:center;">
              <span style="font-size:28px;font-weight:900;color:#ffffff;letter-spacing:-0.5px;">
                ⚖️ JurisAI
              </span>
              <p style="color:rgba(255,255,255,0.75);font-size:12px;margin:6px 0 0 0;letter-spacing:0.5px;text-transform:uppercase;">
                Inteligência Artificial Jurídica Privada
              </p>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:36px 40px 24px 40px;">
              <h1 style="font-size:22px;font-weight:700;color:#1a1a1a;margin:0 0 8px 0;">
                Olá, {name}! Bem-vindo(a) 👋
              </h1>
              <p style="font-size:15px;color:#555;line-height:1.6;margin:0 0 24px 0;">
                Você foi convidado(a) para acessar o <strong>JurisAI</strong> — a plataforma de 
                assistência jurídica com IA, com controle total de auditoria, privacidade de dados 
                e conformidade regulatória.
              </p>

              <p style="font-size:14px;color:#555;line-height:1.6;margin:0 0 28px 0;">
                Para ativar sua conta e definir uma senha segura, clique no botão abaixo:
              </p>

              <!-- CTA Button -->
              <table cellpadding="0" cellspacing="0" style="margin:0 auto 32px auto;">
                <tr>
                  <td style="background:#7a2e2e;border-radius:8px;padding:14px 32px;text-align:center;">
                    <a href="{activate_url}"
                       style="color:#ffffff;font-size:15px;font-weight:700;text-decoration:none;display:inline-block;">
                      Ativar minha conta e definir senha →
                    </a>
                  </td>
                </tr>
              </table>

              <!-- Security notice -->
              <div style="background:#faf9f6;border:1px solid #e8e4dc;border-radius:8px;padding:14px 18px;margin-bottom:24px;">
                <p style="font-size:12px;color:#888;margin:0;line-height:1.5;">
                  🔒 <strong>Segurança:</strong> Este link é válido por <strong>72 horas</strong> 
                  e só pode ser utilizado uma vez. Caso expire, peça ao administrador que envie 
                  um novo convite.
                </p>
              </div>

              <p style="font-size:13px;color:#aaa;margin:0;">
                Se você não esperava este email, pode ignorá-lo com segurança.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#f5f4f0;padding:20px 40px;border-top:1px solid #e8e4dc;text-align:center;">
              <p style="font-size:11px;color:#bbb;margin:0;">
                JurisAI · Plataforma Jurídica com IA Privada · 
                <a href="{PLATFORM_URL}" style="color:#7a2e2e;text-decoration:none;">{PLATFORM_URL}</a>
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
""".strip()


def send_invitation_email(to_email: str, name: str, token: str) -> dict:
    """
    Sends a JurisAI invitation email via Resend.
    Returns {"ok": True} on success, {"ok": False, "error": str} on failure.
    """
    if not resend.api_key:
        print("[email] RESEND_API_KEY not set — invitation email skipped.")
        return {"ok": False, "error": "RESEND_API_KEY not configured"}

    try:
        params: resend.Emails.SendParams = {
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": f"Bem-vindo ao JurisAI, {name}! Ative sua conta.",
            "html": _invitation_html(name, token),
        }
        resp = resend.Emails.send(params)
        print(f"[email] Invitation sent to {to_email} — id: {resp.get('id')}")
        return {"ok": True, "email_id": resp.get("id")}
    except Exception as exc:
        print(f"[email] Failed to send invitation to {to_email}: {exc}")
        return {"ok": False, "error": str(exc)}
