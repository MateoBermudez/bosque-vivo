from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo

from bosquevivo.accounts.mailer import OutgoingEmail

BOGOTA = ZoneInfo("America/Bogota")
FOOTER = (
    "Bosque Vivo · Politécnico Colombiano Jaime Isaza Cadavid. Este es un mensaje automático; "
    "no lo responda."
)


def local_time(moment: datetime) -> str:
    return moment.astimezone(BOGOTA).strftime("%d/%m/%Y %H:%M (hora de Colombia)")


def _html(
    title: str, paragraphs: list[str], button: tuple[str, str] | None, code: str | None
) -> str:
    blocks = [f'<p style="margin:0 0 16px">{escape(text)}</p>' for text in paragraphs]
    if code:
        blocks.insert(
            1,
            '<p style="margin:0 0 16px;font-size:32px;font-weight:700;letter-spacing:8px;'
            f'font-family:monospace">{escape(code)}</p>',
        )
    if button:
        label, url = button
        blocks.insert(
            1,
            f'<p style="margin:0 0 24px"><a href="{escape(url)}" style="background:#1f3a2a;'
            "color:#f4f6ec;padding:12px 20px;border-radius:999px;text-decoration:none;"
            f'font-weight:600">{escape(label)}</a></p>'
            f'<p style="margin:0 0 16px;font-size:12px;color:#5b6b5f">Si el botón no funciona, '
            f"copie este enlace: {escape(url)}</p>",
        )
    return (
        '<!doctype html><html lang="es"><body style="margin:0;background:#f5f4ee;'
        'font-family:Arial,Helvetica,sans-serif;color:#1c2a20">'
        '<div style="max-width:520px;margin:0 auto;padding:32px 20px">'
        '<p style="margin:0 0 24px;font-weight:700;font-size:18px">Bosque Vivo</p>'
        f'<h1 style="margin:0 0 16px;font-size:22px">{escape(title)}</h1>'
        + "".join(blocks)
        + f'<p style="margin:32px 0 0;font-size:12px;color:#5b6b5f">{escape(FOOTER)}</p>'
        "</div></body></html>"
    )


def _email(
    to: str,
    subject: str,
    title: str,
    paragraphs: list[str],
    *,
    button: tuple[str, str] | None = None,
    code: str | None = None,
) -> OutgoingEmail:
    lines = [paragraphs[0]]
    if code:
        lines.append(f"Código: {code}")
    if button:
        lines.append(f"{button[0]}: {button[1]}")
    lines.extend(paragraphs[1:])
    lines.append(FOOTER)
    body = "\n\n".join(lines) + "\n"
    return OutgoingEmail(
        to=to, subject=subject, body=body, html=_html(title, paragraphs, button, code)
    )


def reset_email(to: str, name: str, link: str, minutes: int) -> OutgoingEmail:
    return _email(
        to,
        "Bosque Vivo: restablecer tu contraseña",
        "Restablecer tu contraseña",
        [
            f"Hola, {name}. Recibimos una solicitud para restablecer la contraseña de tu cuenta "
            "de auditor en Bosque Vivo.",
            f"El enlace vence en {minutes} minutos y solo se puede usar una vez.",
            "Si no hiciste esta solicitud, ignora este correo: tu contraseña no cambiará.",
        ],
        button=("Elegir una contraseña nueva", link),
    )


def invitation_email(to: str, name: str, link: str, hours: int) -> OutgoingEmail:
    return _email(
        to,
        "Bosque Vivo: activa tu cuenta de auditor",
        "Te invitaron al área de auditores",
        [
            f"Hola, {name}. Se creó una cuenta de auditor de Bosque Vivo con este correo.",
            f"Elige tu contraseña con el enlace; vence en {hours} horas y solo sirve una vez.",
            "Si no esperabas esta invitación, ignora este correo.",
        ],
        button=("Activar mi cuenta", link),
    )


def login_code_email(to: str, name: str, code: str, minutes: int) -> OutgoingEmail:
    return _email(
        to,
        f"Bosque Vivo: tu código de verificación es {code}",
        "Código de verificación",
        [
            f"Hola, {name}. Usa este código para terminar de iniciar sesión:",
            f"Vence en {minutes} minutos. Nadie del equipo te lo pedirá.",
            "Si no estabas iniciando sesión, cambia tu contraseña: alguien la conoce.",
        ],
        code=code,
    )


def new_login_email(to: str, name: str, when: datetime, client: str) -> OutgoingEmail:
    return _email(
        to,
        "Bosque Vivo: nuevo inicio de sesión",
        "Nuevo inicio de sesión",
        [
            f"Hola, {name}. Se inició sesión en tu cuenta de auditor el {local_time(when)}.",
            f"Origen: {client}.",
            "Si no fuiste tú, restablece tu contraseña desde «¿Olvidaste tu contraseña?».",
        ],
    )


def password_changed_email(to: str, name: str, when: datetime) -> OutgoingEmail:
    return _email(
        to,
        "Bosque Vivo: tu contraseña cambió",
        "Tu contraseña cambió",
        [
            f"Hola, {name}. La contraseña de tu cuenta de auditor se cambió el {local_time(when)}.",
            "Si no fuiste tú, solicita un nuevo enlace de restablecimiento y avisa al equipo.",
        ],
    )


def account_locked_email(to: str, name: str, minutes: int) -> OutgoingEmail:
    return _email(
        to,
        "Bosque Vivo: bloqueamos temporalmente tu cuenta",
        "Cuenta bloqueada por intentos fallidos",
        [
            f"Hola, {name}. Hubo varios intentos fallidos de iniciar sesión en tu cuenta.",
            f"Por seguridad la bloqueamos {minutes} minutos.",
            "Si no fuiste tú, restablece tu contraseña cuando termine el bloqueo.",
        ],
    )


def test_email(to: str) -> OutgoingEmail:
    return _email(
        to,
        "Bosque Vivo: prueba de correo",
        "El correo funciona",
        ["Este mensaje confirma que Bosque Vivo puede enviar correos con la configuración actual."],
    )
