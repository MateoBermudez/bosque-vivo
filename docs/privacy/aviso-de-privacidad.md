# Aviso de privacidad (Ley 1581 de 2012)

Versión del aviso: `v1`.

## Qué datos tratamos
- Su número de teléfono: se guarda únicamente como una huella cifrada (HMAC); no se almacena el número.
- Sus mensajes y las respuestas, para poder atenderle y revisar la calidad del servicio.
- Fotos y notas de voz, solo si usted lo autoriza de forma expresa con `ACEPTO FOTOS`. No se guardan los archivos: se procesan y se descartan.

## Para qué
Responder consultas sobre el estado de bosques de proyectos de carbono con información satelital.

## Quién procesa
Un asistente de inteligencia artificial. El procesamiento del texto, las imágenes y el audio lo realiza un tercero (Google Gemini) en sus servidores, posiblemente fuera de Colombia. No envíe cédula, dirección ni datos privados. En la capa gratuita de ese servicio el contenido puede usarse para mejorar sus productos.

## Sus derechos
- Conocer, actualizar y rectificar sus datos.
- Revocar su autorización y pedir la supresión escribiendo `BORRAR MIS DATOS`: se eliminan su registro, sus permisos y sus consultas.
- Hablar con una persona del equipo cuando lo necesite, por el correo de contacto publicado en `/privacidad` (variable `PRIVACY_CONTACT_EMAIL` del sitio).

## Cuentas de auditor (sitio web)
Para el área de auditores se guarda el correo, el nombre y la contraseña cifrada (scrypt con sal). Los enlaces para restablecer la contraseña (RF09) se guardan solo como huella SHA-256, vencen a los 30 minutos y sirven una sola vez. El mensaje de recuperación no revela si un correo está registrado.

## Retención
Las consultas se conservan solo mientras el usuario no pida su borrado y por el tiempo del piloto.

## Limitaciones
Las respuestas pueden contener errores. Describen lo que se observa desde el satélite y no atribuyen intenciones a nadie.
