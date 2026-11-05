# Documentos legales

El sitio publica tres documentos, con versión y fecha de actualización en cada página:

| Página | Contenido |
|---|---|
| `/terminos` | Términos y condiciones (v1): naturaleza académica del servicio, alcance de los resultados, asistente de IA, cuentas de auditor, uso aceptable, propiedad intelectual, responsabilidad y ley aplicable |
| `/privacidad` | Política de privacidad y tratamiento de datos (v2, Ley 1581 de 2012 y Decreto 1377 de 2013): responsable, datos tratados, finalidades, autorización, encargados y transferencias internacionales, derechos, procedimiento (consultas 10 días hábiles, reclamos 15 días hábiles), seguridad, retención, cookies, IA y vigencia |
| `/uso-de-datos` | Uso de datos y fuentes (v1): licencias y citas de Karnik et al., Hansen GFC, Sentinel-2, Landsat, MODIS y el mapa base de Esri; reutilización, limitaciones y correcciones |

El correo de contacto que aparece en las tres páginas sale de `PRIVACY_CONTACT_EMAIL` en el proyecto web de Vercel. Las páginas son estáticas: después de cambiar esa variable hay que volver a desplegar.

El aviso corto que muestra el asistente antes de pedir `ACEPTO` sigue en la versión `v1` (`backend/src/bosquevivo/assistant/texts.py`); su resumen está en [`aviso-de-privacidad.md`](aviso-de-privacidad.md). Si cambia, se sube `NOTICE_VERSION` y el asistente vuelve a pedir la autorización.

Los correos del sistema enlazan a `/privacidad` y `/terminos` en el pie.
