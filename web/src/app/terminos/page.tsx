import type { Metadata } from "next";
import Link from "next/link";

import { ContactLine, LegalDocument, type LegalSection } from "@/components/legal/legal-document";

export const metadata: Metadata = {
  title: "Términos y condiciones",
  description:
    "Condiciones de uso del sitio, el chat en línea, el asistente de WhatsApp y el área de auditores de Bosque Vivo.",
};

const SECTIONS: LegalSection[] = [
  {
    id: "aceptacion",
    title: "Aceptación",
    body: (
      <p>
        Al usar el sitio de Bosque Vivo, el chat en línea, el asistente de WhatsApp o el área de auditores aceptas estos
        términos y la{" "}
        <Link href="/privacidad" className="underline underline-offset-4">
          política de privacidad
        </Link>
        . Si no estás de acuerdo, no uses el servicio.
      </p>
    ),
  },
  {
    id: "servicio",
    title: "Qué es el servicio",
    body: (
      <>
        <p>
          Bosque Vivo es un proyecto integrador académico de Ingeniería Informática del Politécnico Colombiano Jaime
          Isaza Cadavid. Contrasta lo que declaran los proyectos de carbono forestal con lo que se observa desde el
          satélite (NDVI, pérdida de cobertura arbórea) y lo resume en un índice de supervivencia forestal.
        </p>
        <p>
          Es un piloto gratuito, sin fines de lucro, y no es un servicio oficial del Politécnico, de ninguna autoridad
          ambiental ni de ningún estándar de certificación de carbono.
        </p>
      </>
    ),
  },
  {
    id: "alcance",
    title: "Alcance de los resultados",
    body: (
      <>
        <p>Los índices, alertas, informes y respuestas del asistente:</p>
        <ul>
          <li>
            Describen lo que se observa desde el satélite con la metodología publicada en{" "}
            <Link href="/metodologia" className="underline underline-offset-4">
              Metodología
            </Link>
            , con sus limitaciones de resolución, nubosidad y cobertura de datos.
          </li>
          <li>
            No son una verificación, una auditoría certificada, un dictamen técnico ni una opinión legal, y no
            reemplazan la verificación en campo.
          </li>
          <li>
            No atribuyen intenciones ni responsabilidades a ninguna persona u organización. Una alerta indica que la
            observación satelital merece revisión, no que alguien haya incumplido.
          </li>
          <li>No deben usarse como única base para decisiones de inversión, compra de créditos o sanciones.</li>
        </ul>
      </>
    ),
  },
  {
    id: "asistente",
    title: "Asistente de inteligencia artificial",
    body: (
      <ul>
        <li>El chat en línea y el de WhatsApp los atiende una inteligencia artificial que puede equivocarse.</li>
        <li>
          Antes de responder pide tu autorización (<strong>ACEPTO</strong>). Puedes borrar tus datos cuando quieras con{" "}
          <strong>BORRAR MIS DATOS</strong>.
        </li>
        <li>No envíes cédula, dirección, datos de salud ni otros datos privados o de terceros.</li>
        <li>Las fotos y audios que envíes se tratan como información no verificada.</li>
        <li>En cualquier momento puedes pedir hablar con una persona del equipo.</li>
      </ul>
    ),
  },
  {
    id: "auditores",
    title: "Cuentas de auditor",
    body: (
      <ul>
        <li>Las cuentas se crean por invitación del equipo y son personales e intransferibles.</li>
        <li>
          Eres responsable de guardar tu contraseña y el acceso a tu correo, que se usa para la verificación en dos
          pasos.
        </li>
        <li>
          Avísanos de inmediato si recibes un aviso de inicio de sesión o de cambio de contraseña que no reconoces.
        </li>
        <li>
          Las preguntas al agente y sus trazas se registran para la trazabilidad del sistema y pueden revisarse con
          fines académicos.
        </li>
      </ul>
    ),
  },
  {
    id: "uso",
    title: "Uso aceptable",
    body: (
      <>
        <p>No está permitido:</p>
        <ul>
          <li>Intentar acceder sin autorización a cuentas, al área de auditores o a la infraestructura.</li>
          <li>Automatizar consultas masivas, saturar el servicio o eludir sus límites.</li>
          <li>Enviar contenido ilegal, ofensivo o datos personales de terceros.</li>
          <li>
            Presentar los resultados como una certificación, una acusación o una opinión oficial del proyecto o del
            Politécnico.
          </li>
        </ul>
        <p>El equipo puede bloquear el acceso de quien incumpla estas reglas.</p>
      </>
    ),
  },
  {
    id: "propiedad",
    title: "Propiedad intelectual y citación",
    body: (
      <>
        <p>
          El software, los textos y el diseño de Bosque Vivo son obra del equipo del proyecto. Los datos de terceros
          conservan sus propias licencias, descritas en{" "}
          <Link href="/uso-de-datos" className="underline underline-offset-4">
            uso de datos y fuentes
          </Link>
          .
        </p>
        <p>
          Puedes compartir los informes y capturas con fines académicos, periodísticos o de veeduría citando «Bosque
          Vivo, Politécnico Colombiano Jaime Isaza Cadavid» y las fuentes de datos indicadas en cada informe.
        </p>
      </>
    ),
  },
  {
    id: "responsabilidad",
    title: "Disponibilidad y responsabilidad",
    body: (
      <>
        <p>
          El servicio se ofrece «tal cual», sin garantía de disponibilidad continua ni de exactitud. Depende de
          servicios externos (imágenes satelitales, inteligencia artificial, alojamiento, correo y WhatsApp) que pueden
          fallar o cambiar.
        </p>
        <p>
          En la medida que lo permita la ley, el equipo del proyecto no responde por decisiones tomadas con base en los
          resultados ni por daños derivados de interrupciones o errores del servicio.
        </p>
      </>
    ),
  },
  {
    id: "cambios",
    title: "Cambios, ley aplicable y contacto",
    body: (
      <>
        <p>
          Podemos actualizar estos términos; la versión y la fecha vigentes aparecen al inicio de esta página. Se rigen
          por las leyes de la República de Colombia.
        </p>
        <p>
          Preguntas, reportes de errores o solicitudes: <ContactLine />.
        </p>
      </>
    ),
  },
];

export default function TermsPage() {
  return (
    <LegalDocument
      eyebrow="Condiciones de uso"
      title="Términos y condiciones"
      version="v1"
      current="/terminos"
      intro={<p>Las reglas para usar el sitio, el asistente y el área de auditores de Bosque Vivo.</p>}
      sections={SECTIONS}
    />
  );
}
