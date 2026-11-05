from dataclasses import dataclass
from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo

from bosquevivo.accounts.mailer import OutgoingEmail

BOGOTA = ZoneInfo("America/Bogota")
FOREST = "#1c2e21"
FOREST_SOFT = "#2c4433"
LIME = "#d4e157"
PAPER = "#f5f4ee"
INK = "#1c2a20"
MUTED = "#5b6b5f"
LINE = "#e4e7dc"
FONT = "Manrope,'Segoe UI',Helvetica,Arial,sans-serif"
FOOTER = (
    "Bosque Vivo · Proyecto académico del Politécnico Colombiano Jaime Isaza Cadavid. "
    "Este es un mensaje automático; no lo respondas."
)


def local_time(moment: datetime) -> str:
    return moment.astimezone(BOGOTA).strftime("%d/%m/%Y %H:%M (hora de Colombia)")


@dataclass(frozen=True)
class Content:
    eyebrow: str
    title: str
    paragraphs: list[str]
    button: tuple[str, str] | None = None
    code: str | None = None
    note: str | None = None
    preheader: str = ""


def _paragraph(text: str) -> str:
    return (
        f'<p style="margin:0 0 16px;font-size:15px;line-height:24px;color:{INK}">{escape(text)}</p>'
    )


def _button(label: str, url: str) -> str:
    link = escape(url, quote=True)
    return (
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
        'style="margin:8px 0 24px"><tr>'
        f'<td align="center" bgcolor="{FOREST}" style="border-radius:999px">'
        f'<a href="{link}" target="_blank" style="display:inline-block;padding:14px 28px;'
        f"font-family:{FONT};font-size:15px;font-weight:700;color:#ffffff;"
        f'text-decoration:none;border-radius:999px">{escape(label)} &rarr;</a>'
        "</td></tr></table>"
        f'<p style="margin:0 0 20px;font-size:12px;line-height:18px;color:{MUTED}">'
        "Si el botón no funciona, copia y pega este enlace en tu navegador:<br>"
        f'<a href="{link}" style="color:{FOREST_SOFT};word-break:break-all">{escape(url)}</a></p>'
    )


def _code(code: str) -> str:
    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
        'style="margin:4px 0 20px"><tr>'
        f'<td align="center" style="background:#f3f6e6;border:1px dashed #b9c94a;'
        'border-radius:14px;padding:20px 12px">'
        f'<div style="font-size:12px;letter-spacing:2px;text-transform:uppercase;color:{MUTED};'
        'margin-bottom:6px">Código de verificación</div>'
        f"<div style=\"font-family:'SFMono-Regular',Consolas,'Courier New',monospace;"
        f'font-size:34px;font-weight:700;letter-spacing:10px;color:{FOREST}">{escape(code)}</div>'
        "</td></tr></table>"
    )


def _note(text: str) -> str:
    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
        'style="margin:8px 0 0"><tr>'
        f'<td style="background:{PAPER};border-left:4px solid {LIME};border-radius:10px;'
        f'padding:14px 16px;font-size:13px;line-height:20px;color:{MUTED}">{escape(text)}</td>'
        "</tr></table>"
    )


def _footer_links(site: str) -> str:
    if not site:
        return ""
    base = site.rstrip("/")
    links = [
        ("Sitio", base),
        ("Privacidad", f"{base}/privacidad"),
        ("Términos", f"{base}/terminos"),
    ]
    rendered = " &nbsp;·&nbsp; ".join(
        f'<a href="{escape(url, quote=True)}" style="color:{FOREST_SOFT};text-decoration:none">'
        f"{escape(label)}</a>"
        for label, url in links
    )
    return f'<p style="margin:0 0 8px;font-size:12px">{rendered}</p>'


TABLE = 'role="presentation" cellpadding="0" cellspacing="0" border="0"'


def _header() -> str:
    return (
        f'<tr><td bgcolor="{FOREST}" style="background:{FOREST};'
        'border-radius:20px 20px 0 0;padding:22px 32px">'
        f"<table {TABLE}><tr>"
        f'<td width="34" height="34" align="center" bgcolor="{LIME}" '
        f'style="background:{LIME};border-radius:999px;font-size:18px;line-height:34px;'
        f'color:{FOREST}">&#127807;</td>'
        '<td style="padding-left:12px">'
        '<div style="font-size:18px;font-weight:800;color:#ffffff;letter-spacing:-0.2px">'
        "Bosque Vivo</div>"
        '<div style="font-size:12px;color:#c7d3c3">Auditoría satelital de carbono forestal</div>'
        "</td></tr></table>"
        "</td></tr>"
    )


def _card(content: Content, body: str) -> str:
    return (
        '<tr><td bgcolor="#ffffff" style="background:#ffffff;'
        f'border:1px solid {LINE};border-top:0;border-radius:0 0 20px 20px;padding:32px">'
        '<div style="font-size:12px;font-weight:700;letter-spacing:1.5px;'
        'text-transform:uppercase;color:#6f8a2e;margin:0 0 8px">'
        f"{escape(content.eyebrow)}</div>"
        '<h1 style="margin:0 0 18px;font-size:24px;line-height:30px;font-weight:800;'
        f'color:{FOREST}">{escape(content.title)}</h1>'
        f"{body}"
        "</td></tr>"
    )


def render_html(content: Content, site: str = "") -> str:
    body = [_paragraph(content.paragraphs[0])]
    if content.code:
        body.append(_code(content.code))
    if content.button:
        body.append(_button(*content.button))
    body.extend(_paragraph(text) for text in content.paragraphs[1:])
    if content.note:
        body.append(_note(content.note))
    preheader = escape(content.preheader or content.paragraphs[0])
    footer = (
        '<tr><td align="center" style="padding:20px 24px 0;font-size:12px;line-height:18px;'
        f'color:{MUTED}">{_footer_links(site)}<p style="margin:0">{escape(FOOTER)}</p>'
        "</td></tr>"
    )
    return (
        "<!doctype html>\n"
        '<html lang="es" xmlns="http://www.w3.org/1999/xhtml">\n'
        '<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        '<meta name="color-scheme" content="light">\n'
        '<meta name="supported-color-schemes" content="light">\n'
        f"<title>{escape(content.title)}</title>\n</head>\n"
        f'<body style="margin:0;padding:0;background:{PAPER};font-family:{FONT};color:{INK}">\n'
        f'<div style="display:none;max-height:0;overflow:hidden;opacity:0">{preheader}</div>\n'
        f'<table {TABLE} width="100%" bgcolor="{PAPER}">'
        '<tr><td align="center" style="padding:32px 12px">'
        f'<table {TABLE} width="100%" style="max-width:560px">'
        f"{_header()}{_card(content, ''.join(body))}{footer}"
        "</table></td></tr></table>\n"
        "</body>\n</html>\n"
    )


def render_text(content: Content, site: str = "") -> str:
    lines = [content.title.upper(), content.paragraphs[0]]
    if content.code:
        lines.append(f"Código: {content.code}")
    if content.button:
        lines.append(f"{content.button[0]}: {content.button[1]}")
    lines.extend(content.paragraphs[1:])
    if content.note:
        lines.append(content.note)
    if site:
        lines.append(f"Privacidad: {site.rstrip('/')}/privacidad")
    lines.append(FOOTER)
    return "\n\n".join(lines) + "\n"


def _email(to: str, subject: str, content: Content, site: str) -> OutgoingEmail:
    return OutgoingEmail(
        to=to,
        subject=subject,
        body=render_text(content, site),
        html=render_html(content, site),
    )


def reset_email(to: str, name: str, link: str, minutes: int, site: str = "") -> OutgoingEmail:
    return _email(
        to,
        "Bosque Vivo: restablecer tu contraseña",
        Content(
            eyebrow="Seguridad de la cuenta",
            title="Restablecer tu contraseña",
            paragraphs=[
                f"Hola, {name}. Recibimos una solicitud para restablecer la contraseña de tu "
                "cuenta de auditor en Bosque Vivo.",
                f"El enlace vence en {minutes} minutos y solo se puede usar una vez.",
            ],
            button=("Elegir una contraseña nueva", link),
            note="Si no hiciste esta solicitud, ignora este correo: tu contraseña no cambiará.",
        ),
        site,
    )


def invitation_email(to: str, name: str, link: str, hours: int, site: str = "") -> OutgoingEmail:
    return _email(
        to,
        "Bosque Vivo: activa tu cuenta de auditor",
        Content(
            eyebrow="Invitación",
            title="Te invitaron al área de auditores",
            paragraphs=[
                f"Hola, {name}. Se creó una cuenta de auditor de Bosque Vivo con este correo.",
                f"Elige tu contraseña con el botón. El enlace vence en {hours} horas y solo "
                "sirve una vez.",
            ],
            button=("Activar mi cuenta", link),
            note="Si no esperabas esta invitación, ignora este correo.",
        ),
        site,
    )


def login_code_email(to: str, name: str, code: str, minutes: int, site: str = "") -> OutgoingEmail:
    return _email(
        to,
        f"Bosque Vivo: tu código de verificación es {code}",
        Content(
            eyebrow="Verificación en dos pasos",
            title="Tu código para iniciar sesión",
            paragraphs=[
                f"Hola, {name}. Usa este código para terminar de iniciar sesión:",
                f"Vence en {minutes} minutos. Nadie del equipo te lo pedirá nunca.",
            ],
            code=code,
            note="Si no estabas iniciando sesión, cambia tu contraseña: alguien la conoce.",
            preheader=f"Tu código es {code}. Vence en {minutes} minutos.",
        ),
        site,
    )


def new_login_email(
    to: str, name: str, when: datetime, client: str, site: str = ""
) -> OutgoingEmail:
    return _email(
        to,
        "Bosque Vivo: nuevo inicio de sesión",
        Content(
            eyebrow="Actividad de la cuenta",
            title="Nuevo inicio de sesión",
            paragraphs=[
                f"Hola, {name}. Se inició sesión en tu cuenta de auditor el {local_time(when)}.",
                f"Origen: {client}.",
            ],
            note="Si no fuiste tú, restablece tu contraseña desde «¿Olvidaste tu contraseña?».",
        ),
        site,
    )


def password_changed_email(to: str, name: str, when: datetime, site: str = "") -> OutgoingEmail:
    return _email(
        to,
        "Bosque Vivo: tu contraseña cambió",
        Content(
            eyebrow="Seguridad de la cuenta",
            title="Tu contraseña cambió",
            paragraphs=[
                f"Hola, {name}. La contraseña de tu cuenta de auditor se cambió el "
                f"{local_time(when)}.",
            ],
            note="Si no fuiste tú, solicita un nuevo enlace de restablecimiento y avisa al equipo.",
        ),
        site,
    )


def account_locked_email(to: str, name: str, minutes: int, site: str = "") -> OutgoingEmail:
    return _email(
        to,
        "Bosque Vivo: bloqueamos temporalmente tu cuenta",
        Content(
            eyebrow="Seguridad de la cuenta",
            title="Cuenta bloqueada por intentos fallidos",
            paragraphs=[
                f"Hola, {name}. Hubo varios intentos fallidos de iniciar sesión en tu cuenta.",
                f"Por seguridad la bloqueamos {minutes} minutos.",
            ],
            note="Si no fuiste tú, restablece tu contraseña cuando termine el bloqueo.",
        ),
        site,
    )


def test_email(to: str, site: str = "") -> OutgoingEmail:
    return _email(
        to,
        "Bosque Vivo: prueba de correo",
        Content(
            eyebrow="Configuración",
            title="El correo funciona",
            paragraphs=[
                "Este mensaje confirma que Bosque Vivo puede enviar correos con la "
                "configuración actual.",
            ],
        ),
        site,
    )
