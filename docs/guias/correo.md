# Guía: correo SMTP (verificación en dos pasos, avisos y recuperación de contraseña)

Bosque Vivo envía estos correos a las cuentas de auditor:

| Correo | Cuándo |
|---|---|
| Código de verificación (6 dígitos) | Al iniciar sesión, si la verificación en dos pasos está activa. Vence en `AUTH_CODE_TTL_MINUTES` (10) y admite 5 intentos y 3 reenvíos |
| Nuevo inicio de sesión | Después de cada inicio de sesión correcto (navegador, sistema e IP). Se apaga con `AUTH_LOGIN_ALERTS=false` |
| Restablecer contraseña (RF09) | Desde «¿Olvidaste tu contraseña?». Enlace de un solo uso que vence en `PASSWORD_RESET_TTL_MINUTES` (30) |
| Tu contraseña cambió | Después de restablecerla |
| Cuenta bloqueada | Tras 5 contraseñas incorrectas (10 minutos) |
| Invitación | Al crear una cuenta con `user-invite`: enlace para elegir la primera contraseña, válido `INVITATION_TTL_HOURS` (72) |

Todos llevan versión de texto y HTML.

## Activar el envío real (gratis con Gmail)

1. En la cuenta de Google que enviará los correos active la **verificación en dos pasos**.
2. Cree una **contraseña de aplicación** en [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) (16 letras).
3. En `backend/.env` complete solo dos líneas:

   ```
   SMTP_USER=su-cuenta@gmail.com
   SMTP_PASSWORD=<contraseña de aplicación>
   ```

   El servidor se detecta solo para Gmail, cuentas de Google Workspace como `@elpoli.edu.co`, Outlook/Hotmail y Yahoo. Para otro proveedor añada `SMTP_HOST` y `SMTP_PORT` (465 activa SSL directo).
4. Pruebe:

   ```
   cd backend
   uv run bosquevivo mail-test su-correo@dominio
   ```

5. Ponga en `WEB_BASE_URL` la dirección con la que los auditores abren el sitio (por ejemplo la URL del túnel); con ella se arman los enlaces de los correos.

Con SMTP configurado, la verificación en dos pasos se activa sola (`AUTH_TWO_FACTOR=auto`). Se puede forzar con `on` u `off`.

## Sin SMTP

`MAIL_BACKEND=auto` guarda cada correo como `.eml` en `backend/data/outbox/` y el inicio de sesión funciona sin código de verificación. Sirve para desarrollo y demostraciones locales.

## Cuentas de auditor

```
cd backend
uv run bosquevivo user-invite auditor@elpoli.edu.co --name "Nombre Apellido"
uv run bosquevivo user-list
uv run bosquevivo user-disable auditor@elpoli.edu.co
uv run bosquevivo user-reset auditor@elpoli.edu.co
```

`user-invite` envía el enlace para que la persona elija su contraseña (sin SMTP, el comando imprime el enlace). `user-create` sigue disponible para crear una cuenta con contraseña directamente.

Si un correo no se puede enviar, queda un incidente de origen «externo» (`uv run bosquevivo incidents`). Si falla el código de verificación, el sitio lo informa y no deja entrar.
