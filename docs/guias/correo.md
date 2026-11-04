# Guía: correo para recuperar contraseñas (RF09)

El restablecimiento de contraseña envía un enlace de un solo uso que vence en `PASSWORD_RESET_TTL_MINUTES` (30 por defecto).

## Desarrollo (sin enviar correos)

Con `MAIL_BACKEND=outbox` (valor por defecto) cada correo se guarda como archivo `.eml` en `backend/data/outbox/`. Se abre con cualquier cliente de correo o un editor de texto.

## Envío real gratuito con Gmail

1. Active la verificación en dos pasos en la cuenta de Google que enviará los correos.
2. Cree una **contraseña de aplicación** en [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
3. En `backend/.env`:

   ```
   MAIL_BACKEND=smtp
   MAIL_FROM=Bosque Vivo <su-cuenta@gmail.com>
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=su-cuenta@gmail.com
   SMTP_PASSWORD=<contraseña de aplicación>
   SMTP_STARTTLS=true
   WEB_BASE_URL=http://localhost:3000
   ```

   `WEB_BASE_URL` es la dirección pública del sitio: con ella se arma el enlace del correo.

## Cuentas de auditor

```
cd backend
uv run bosquevivo user-create auditor@elpoli.edu.co --name "Nombre Apellido"
uv run bosquevivo user-list
uv run bosquevivo user-disable auditor@elpoli.edu.co
uv run bosquevivo user-reset auditor@elpoli.edu.co
```

En el sitio (`BV_DATA_SOURCE=live` y `SESSION_SECRET` definido) se inicia sesión en `/acceso`; «¿Olvidaste tu contraseña?» lleva a `/acceso/recuperar`.
