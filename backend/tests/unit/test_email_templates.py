from datetime import UTC, datetime

from bosquevivo.accounts import templates

SITE = "https://bosque.test/"


def test_html_has_brand_button_and_legal_links():
    message = templates.reset_email(
        "a@b.co", "Ana", "https://bosque.test/acceso/restablecer?token=abc", 30, site=SITE
    )
    html = message.html or ""
    assert html.startswith("<!doctype html>")
    assert 'lang="es"' in html
    assert "Bosque Vivo" in html
    assert html.count('href="https://bosque.test/acceso/restablecer?token=abc"') == 2
    assert 'href="https://bosque.test/privacidad"' in html
    assert 'href="https://bosque.test/terminos"' in html
    assert "Restablecer tu contraseña" in html
    assert "30 minutos" in html


def test_text_version_keeps_link_privacy_and_footer():
    message = templates.reset_email(
        "a@b.co", "Ana", "https://bosque.test/acceso/restablecer?token=abc", 30, site=SITE
    )
    body = message.body
    assert "Elegir una contraseña nueva: https://bosque.test/acceso/restablecer?token=abc" in body
    assert "Privacidad: https://bosque.test/privacidad" in body
    assert "no lo respondas" in body
    assert "<" not in body


def test_code_is_highlighted_and_in_preheader():
    message = templates.login_code_email("a@b.co", "Ana", "482913", 10, site=SITE)
    html = message.html or ""
    assert "482913" in message.subject
    assert "Código: 482913" in message.body
    assert html.count("482913") >= 2
    assert "Código de verificación" in html
    assert "Vence en 10 minutos" in html


def test_user_values_are_escaped():
    message = templates.new_login_email(
        "a@b.co", "<script>x</script>", datetime(2026, 11, 5, 15, 0, tzinfo=UTC), "Chrome & Co"
    )
    html = message.html or ""
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "Chrome &amp; Co" in html
    assert "05/11/2026 10:00 (hora de Colombia)" in message.body


def test_without_site_there_are_no_legal_links():
    message = templates.test_email("a@b.co")
    assert "/privacidad" not in (message.html or "")
    assert "Privacidad:" not in message.body
    assert "El correo funciona" in (message.html or "")


def test_every_template_has_text_and_html():
    now = datetime(2026, 11, 5, tzinfo=UTC)
    messages = [
        templates.reset_email("a@b.co", "Ana", "https://x/l", 30, site=SITE),
        templates.invitation_email("a@b.co", "Ana", "https://x/l", 72, site=SITE),
        templates.login_code_email("a@b.co", "Ana", "123456", 10, site=SITE),
        templates.new_login_email("a@b.co", "Ana", now, "Chrome", site=SITE),
        templates.password_changed_email("a@b.co", "Ana", now, site=SITE),
        templates.account_locked_email("a@b.co", "Ana", 10, site=SITE),
        templates.test_email("a@b.co", site=SITE),
    ]
    for message in messages:
        assert message.subject.startswith("Bosque Vivo: ")
        assert message.body.strip()
        assert "</html>" in (message.html or "")
        assert "Proyecto académico del Politécnico" in message.body
