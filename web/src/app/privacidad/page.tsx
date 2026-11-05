import type { Metadata } from "next";
import Link from "next/link";

import { ContactLine, LegalDocument, type LegalSection } from "@/components/legal/legal-document";

export const metadata: Metadata = {
  title: "Política de privacidad",
  description:
    "Política de tratamiento de datos personales de Bosque Vivo: qué datos se tratan, para qué, con quién se comparten y cómo ejercer tus derechos según la Ley 1581 de 2012.",
};

const SECTIONS: LegalSection[] = [
  {
    id: "responsable",
    title: "Responsable del tratamiento",
    body: (
      <>
        <p>
          Bosque Vivo es un proyecto integrador académico de estudiantes de Ingeniería Informática del Politécnico
          Colombiano Jaime Isaza Cadavid (Medellín, Colombia). El equipo del proyecto es el responsable del tratamiento
          de los datos que se recogen en este sitio, en el chat en línea y en el asistente de WhatsApp.
        </p>
        <p>
          Contacto para temas de privacidad: <ContactLine />.
        </p>
        <p>
          Esta política aplica la Ley 1581 de 2012 y el Decreto 1377 de 2013 (compilado en el Decreto Único 1074 de
          2015).
        </p>
      </>
    ),
  },
  {
    id: "datos",
    title: "Qué datos tratamos",
    body: (
      <>
        <p>
          <strong>Visitantes del sitio.</strong> Consultar proyectos, mapas, metodología e informes no exige registrarse
          ni entregar datos personales. Los servidores de alojamiento registran de forma técnica la dirección IP y el
          navegador de cada solicitud para operar y proteger el servicio.
        </p>
        <p>
          <strong>Asistente de WhatsApp y chat en línea.</strong>
        </p>
        <ul>
          <li>
            El número de teléfono se guarda solo como una huella cifrada (HMAC-SHA256); el número no se almacena. En el
            chat en línea se usa un identificador aleatorio guardado en tu navegador en lugar del teléfono.
          </li>
          <li>Tus preguntas, las respuestas y el proyecto que elijas, para atenderte y revisar la calidad.</li>
          <li>La fecha y la versión del aviso con que diste tu autorización.</li>
          <li>
            Fotos, notas de voz y ubicación solo si las envías; las fotos y audios requieren una autorización aparte (
            <strong>ACEPTO FOTOS</strong>). Los archivos se procesan y se descartan: no se guardan.
          </li>
        </ul>
        <p>
          <strong>Cuentas de auditor.</strong> Correo, nombre, contraseña cifrada (scrypt con sal), intentos fallidos y
          bloqueos, y el navegador y la IP aproximada de cada inicio de sesión para enviarte avisos de seguridad. Los
          enlaces de invitación y restablecimiento y los códigos de verificación se guardan solo como huellas SHA-256,
          vencen y sirven una sola vez.
        </p>
        <p>
          <strong>Datos de los proyectos.</strong> Los polígonos y atributos de los proyectos de carbono provienen de
          registros públicos y no son datos personales. Ver{" "}
          <Link href="/uso-de-datos" className="underline underline-offset-4">
            uso de datos y fuentes
          </Link>
          .
        </p>
        <p>
          No pedimos ni necesitamos datos sensibles (salud, origen étnico, creencias, biometría) ni datos de niñas,
          niños o adolescentes. No los envíes.
        </p>
      </>
    ),
  },
  {
    id: "finalidades",
    title: "Para qué los usamos",
    body: (
      <ul>
        <li>Responder consultas sobre el estado del bosque de proyectos de carbono con información satelital.</li>
        <li>
          Dar acceso al área de auditores, verificar la identidad en dos pasos y avisar de actividad en la cuenta.
        </li>
        <li>
          Mantener la trazabilidad de las respuestas del agente (herramientas usadas y evidencias) y medir su calidad.
        </li>
        <li>Proteger el servicio frente a abusos, errores e incidentes de seguridad.</li>
        <li>Producir resultados agregados y anónimos para el informe académico del proyecto.</li>
      </ul>
    ),
  },
  {
    id: "autorizacion",
    title: "Autorización",
    body: (
      <>
        <p>
          Antes de procesar cualquier pregunta, el asistente muestra un aviso y solo continúa si escribes{" "}
          <strong>ACEPTO</strong>. El uso de fotos y audios requiere además <strong>ACEPTO FOTOS</strong>. Cada
          autorización queda registrada con su fecha y la versión del aviso.
        </p>
        <p>
          Las cuentas de auditor las crea el equipo por invitación; al activar la cuenta y elegir la contraseña la
          persona acepta estos términos y esta política.
        </p>
      </>
    ),
  },
  {
    id: "encargados",
    title: "Con quién se comparten (encargados y transferencias)",
    body: (
      <>
        <p>No vendemos ni cedemos datos personales. Para funcionar, el servicio usa estos proveedores:</p>
        <ul>
          <li>
            <strong>Google (Gemini)</strong>: procesa el texto, las imágenes y los audios de las consultas. En la capa
            gratuita, Google puede usar el contenido para mejorar sus productos; por eso pedimos no enviar cédula,
            dirección ni datos privados.
          </li>
          <li>
            <strong>Supabase</strong>: aloja la base de datos (PostgreSQL) en servidores de Amazon Web Services en
            Estados Unidos.
          </li>
          <li>
            <strong>Vercel</strong>: aloja el sitio web y la API.
          </li>
          <li>
            <strong>Google (Gmail)</strong>: envía los correos de invitación, verificación y seguridad.
          </li>
          <li>
            <strong>Meta (WhatsApp Business)</strong>: transporta los mensajes del asistente de WhatsApp, según sus
            propias condiciones.
          </li>
        </ul>
        <p>
          Estos proveedores pueden tratar los datos fuera de Colombia, en países como Estados Unidos. Al dar tu
          autorización aceptas esa transferencia, que se limita a lo necesario para prestar el servicio.
        </p>
      </>
    ),
  },
  {
    id: "derechos",
    title: "Tus derechos",
    body: (
      <>
        <p>Como titular de los datos puedes:</p>
        <ul>
          <li>Conocer, actualizar y rectificar tus datos.</li>
          <li>Pedir prueba de la autorización que diste.</li>
          <li>Saber qué uso se ha dado a tus datos.</li>
          <li>Revocar la autorización y pedir la supresión de tus datos.</li>
          <li>Acceder gratis a tus datos.</li>
          <li>
            Presentar quejas ante la Superintendencia de Industria y Comercio (SIC) después de haber agotado el trámite
            de consulta o reclamo con nosotros.
          </li>
        </ul>
      </>
    ),
  },
  {
    id: "procedimiento",
    title: "Cómo ejercerlos",
    body: (
      <>
        <ul>
          <li>
            <strong>Borrado inmediato:</strong> escribe <strong>BORRAR MIS DATOS</strong> en WhatsApp o en el chat en
            línea. Se eliminan tu registro, tus permisos y tus consultas.
          </li>
          <li>
            <strong>Consultas y reclamos:</strong> escribe a <ContactLine /> indicando tu solicitud y cómo identificarte
            (por ejemplo, el correo de tu cuenta o el número desde el que escribiste).
          </li>
        </ul>
        <p>
          Respondemos las consultas en un máximo de 10 días hábiles (prorrogables 5 días hábiles más, avisándote) y los
          reclamos en un máximo de 15 días hábiles (prorrogables 8 días hábiles más), como establece la Ley 1581 de
          2012.
        </p>
        <p>En cualquier momento puedes hablar con una persona del equipo por el mismo canal.</p>
      </>
    ),
  },
  {
    id: "seguridad",
    title: "Seguridad",
    body: (
      <ul>
        <li>Conexiones cifradas (HTTPS/TLS) entre tu navegador, la API y la base de datos.</li>
        <li>Teléfonos guardados como huella HMAC; contraseñas con scrypt; enlaces y códigos como huellas SHA-256.</li>
        <li>
          Verificación en dos pasos por correo, bloqueo temporal tras 5 intentos fallidos y avisos de inicio de sesión.
        </li>
        <li>Acceso al área de auditores y a las trazas solo con sesión iniciada.</li>
        <li>Registro de incidentes para revisar fallas de los servicios externos.</li>
      </ul>
    ),
  },
  {
    id: "retencion",
    title: "Cuánto tiempo los conservamos",
    body: (
      <ul>
        <li>
          Consultas del asistente: hasta que pidas su borrado o, como máximo, hasta que termine el piloto académico.
        </li>
        <li>Códigos de verificación: 10 minutos. Enlaces de restablecimiento: 30 minutos. Invitaciones: 72 horas.</li>
        <li>Sesión de auditor: 8 horas.</li>
        <li>Cuentas de auditor: mientras la persona participe en el proyecto; se desactivan o eliminan a solicitud.</li>
        <li>Al cerrar el proyecto los datos personales se eliminan y solo se conservan cifras agregadas y anónimas.</li>
      </ul>
    ),
  },
  {
    id: "cookies",
    title: "Cookies y almacenamiento local",
    body: (
      <>
        <p>El sitio no usa cookies publicitarias ni de seguimiento, ni herramientas de analítica de terceros.</p>
        <ul>
          <li>
            <strong>Cookie de sesión del auditor</strong> (técnica, <span className="font-mono">httpOnly</span>):
            mantiene la sesión iniciada durante 8 horas. Solo existe si inicias sesión.
          </li>
          <li>
            <strong>Identificador del chat en línea</strong> (almacenamiento local del navegador): un valor aleatorio
            para continuar tu conversación. Puedes borrarlo desde la configuración del navegador.
          </li>
        </ul>
      </>
    ),
  },
  {
    id: "ia",
    title: "Inteligencia artificial",
    body: (
      <p>
        Las respuestas las genera un asistente de inteligencia artificial a partir de datos satelitales y de la base de
        conocimiento del proyecto. Pueden contener errores y no constituyen una decisión sobre ninguna persona:
        describen lo que se observa desde el satélite y no atribuyen intenciones a nadie.
      </p>
    ),
  },
  {
    id: "vigencia",
    title: "Cambios y vigencia",
    body: (
      <p>
        Esta política rige desde su publicación y mientras dure el proyecto. Si cambia de forma importante,
        actualizaremos la versión y la fecha de esta página y, para el asistente, pediremos de nuevo la autorización.
        Ver también los{" "}
        <Link href="/terminos" className="underline underline-offset-4">
          términos y condiciones
        </Link>
        .
      </p>
    ),
  },
];

export default function PrivacyPage() {
  return (
    <LegalDocument
      eyebrow="Ley 1581 de 2012"
      title="Política de privacidad y tratamiento de datos"
      version="v2"
      current="/privacidad"
      intro={
        <p>
          Qué datos personales trata Bosque Vivo, para qué, con quién se comparten y cómo ejercer tus derechos de habeas
          data.
        </p>
      }
      sections={SECTIONS}
    />
  );
}
