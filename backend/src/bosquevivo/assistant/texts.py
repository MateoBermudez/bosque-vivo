NOTICE_VERSION = "v1"

WELCOME = (
    "Hola, soy el asistente de Bosque Vivo. Soy una inteligencia artificial: "
    "puedo contarle qué se ve desde el satélite en proyectos de bosque. Puedo equivocarme."
)
NOTICE = (
    "Su mensaje lo procesa un servicio de un tercero (Google). No envíe cédula, "
    "dirección ni datos privados. Para continuar escriba ACEPTO. Puede borrar sus datos "
    "cuando quiera escribiendo BORRAR MIS DATOS."
)
CONSENT_GRANTED = (
    "Gracias. Ya puede preguntarme, por ejemplo: «¿Cómo está Concosta?». También puede "
    "elegir su proyecto con el botón de abajo o compartir su ubicación."
)
CONSENT_PENDING = "Para ayudarle necesito su autorización. Escriba ACEPTO para continuar."
MEDIA_NOTICE = (
    "Para usar fotos o audios necesito su permiso aparte: se procesan con un servicio externo "
    "y son información no verificada. Si está de acuerdo, escriba ACEPTO FOTOS."
)
MEDIA_GRANTED = "Listo, ya puedo usar sus fotos y audios. Envíelos cuando quiera."
DELETED = "Listo. Borré sus datos, consultas y permisos. Si me escribe de nuevo empezamos de cero."
UNSUPPORTED = "Por ahora solo entiendo texto, ubicación, fotos y notas de voz."
FAILURE = "Tuve un problema para responder. Intente de nuevo en unos minutos."
AUDIO_UNCLEAR = "No pude entender el audio. ¿Puede escribirme su pregunta?"
HELP = (
    "Puede escribirme el nombre de un proyecto (por ejemplo, «¿Cómo está Concosta?»), o usar: "
    "ESTADO (cómo está su bosque), ALERTAS (cambios recientes), PROYECTO y el número para "
    "elegir su proyecto, o enviar su ubicación. También puede preguntar con sus palabras. "
    "BORRAR MIS DATOS elimina todo."
)
NEED_PROJECT = (
    "Primero dígame cuál es su proyecto: escriba su nombre (por ejemplo, Concosta), elíjalo con "
    "el botón «Elegir mi proyecto», escriba PROYECTO y el número (por ejemplo PROYECTO 7) o "
    "comparta su ubicación con el botón de ubicación del chat."
)
PROJECT_NOT_FOUND = "No encontré ese número de proyecto. Revise el número o envíe su ubicación."
LOCATION_OUTSIDE = (
    "Ese punto no queda dentro de ningún proyecto registrado. Si conoce su proyecto, escriba "
    "PROYECTO y el número (por ejemplo PROYECTO 7)."
)
NOT_AUTHORIZED = (
    "Este número no está habilitado para el piloto de Bosque Vivo. Si cree que es un error, "
    "comuníquese con el equipo del proyecto."
)


GREETING_NO_PROJECT = (
    "Hola, gusto en saludarle. Cuénteme de qué proyecto quiere saber: escriba su nombre "
    "(por ejemplo, «¿Cómo está Concosta?»), elíjalo con el botón «Elegir mi proyecto» o "
    "comparta su ubicación."
)
THANKS = "Con gusto. Si quiere saber algo más de su proyecto o de otro, escríbame."
ABOUT = (
    "Soy el asistente de Bosque Vivo, una inteligencia artificial. Le cuento qué se ve desde el "
    "satélite en los proyectos de bosque cargados: cómo está su bosque, si hay alertas de "
    "pérdida y qué significa su índice. Puedo equivocarme, y no acuso a nadie: describo lo que "
    "se observa."
)
DEGRADED = (
    "No pude armar una respuesta completa a su pregunta, pero esto es lo que ya está calculado."
)


def project_registered(name: str) -> str:
    return f"Listo, quedó registrado el proyecto {name}."


def greeting_with_project(name: str) -> str:
    return (
        f"Hola de nuevo. Tengo registrado el proyecto {name}. ¿Qué quiere saber: cómo está, "
        "si hay alertas o qué significa su índice?"
    )
