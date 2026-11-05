import type { Metadata } from "next";
import Link from "next/link";

import { ContactLine, LegalDocument, type LegalSection } from "@/components/legal/legal-document";

export const metadata: Metadata = {
  title: "Uso de datos y fuentes",
  description:
    "De dónde vienen los datos de Bosque Vivo, con qué licencias se usan, cómo citarlos y cuáles son sus limitaciones.",
};

const SOURCES: {
  name: string;
  use: string;
  license: string;
  citation: string;
  href: string;
}[] = [
  {
    name: "Base de polígonos de proyectos de carbono",
    use: "Contornos y atributos de los proyectos (país, tipo, estándar, fecha de registro).",
    license: "CC BY 4.0",
    citation:
      "Karnik, A., Kilbride, J. B., Goodbody, T. R. H., Ross, R. y Ayrey, E. (2025). An open-access database of nature-based carbon offset project boundaries. Scientific Data, 12, 581.",
    href: "https://doi.org/10.5281/zenodo.11459391",
  },
  {
    name: "Hansen Global Forest Change (GFC-2024-v1.12)",
    use: "Cobertura arbórea del año 2000 y pérdida de bosque por año (componente de permanencia y alertas).",
    license: "CC BY 4.0",
    citation:
      "Hansen, M. C., et al. (2013). High-resolution global maps of 21st-century forest cover change. Science, 342, 850–853.",
    href: "https://glad.earthengine.app/view/global-forest-change",
  },
  {
    name: "Sentinel-2 (Copernicus, ESA)",
    use: "NDVI de 10 m para tendencia y estabilidad, cuando se usa Google Earth Engine.",
    license: "Uso libre y abierto de los datos Copernicus",
    citation: "Contiene datos modificados de Copernicus Sentinel procesados por Bosque Vivo.",
    href: "https://sentinels.copernicus.eu",
  },
  {
    name: "Landsat 8 y 9 (USGS/NASA)",
    use: "NDVI de 30 m como serie alternativa a Sentinel-2.",
    license: "Dominio público (USGS)",
    citation: "Imágenes Landsat cortesía del Servicio Geológico de los Estados Unidos (USGS).",
    href: "https://www.usgs.gov/landsat-missions",
  },
  {
    name: "MODIS MOD13Q1 v061 (NASA LP DAAC)",
    use: "NDVI de 250 m cuando no se usa Earth Engine (proveedor de datos abiertos).",
    license: "Sin restricciones (política de datos de NASA EOSDIS)",
    citation: "Didan, K. (2021). MODIS/Terra Vegetation Indices 16-Day L3 Global 250m SIN Grid V061. NASA LP DAAC.",
    href: "https://doi.org/10.5067/MODIS/MOD13Q1.061",
  },
  {
    name: "Mapa base satelital (Esri World Imagery)",
    use: "Fondo de los mapas del sitio. Solo se muestra; no se descarga ni se analiza.",
    license: "Condiciones de uso de Esri",
    citation: "Imágenes © Esri, Maxar, Earthstar Geographics y la comunidad GIS.",
    href: "https://www.esri.com/en-us/legal/terms/full-master-agreement",
  },
];

const SECTIONS: LegalSection[] = [
  {
    id: "fuentes",
    title: "Fuentes y licencias",
    body: (
      <ul className="list-none! space-y-4 pl-0!">
        {SOURCES.map((source) => (
          <li key={source.name} className="rounded-xl border border-border p-4">
            <p className="font-semibold text-foreground">{source.name}</p>
            <p className="mt-1">{source.use}</p>
            <p className="mt-2 text-sm">
              <span className="font-semibold text-foreground">Licencia:</span> {source.license}
            </p>
            <p className="mt-1 text-sm">
              <span className="font-semibold text-foreground">Cita:</span> {source.citation}{" "}
              <a href={source.href} className="underline underline-offset-4" target="_blank" rel="noreferrer">
                Fuente
              </a>
            </p>
          </li>
        ))}
      </ul>
    ),
  },
  {
    id: "tratamiento",
    title: "Cómo usamos estos datos",
    body: (
      <ul>
        <li>
          Los polígonos se importan tal como los publican los autores; los que tienen geometría inválida o sin fecha de
          registro se rechazan o se marcan, sin corregirlos en silencio.
        </li>
        <li>
          Las imágenes se procesan para obtener series mensuales de NDVI y de pérdida de bosque dentro de cada polígono;
          se descartan píxeles con nubes y escenas con más nubosidad que el umbral configurado.
        </li>
        <li>
          Cada informe registra las fuentes, las fechas de las escenas, la versión de la metodología y los parámetros
          usados, para que el resultado se pueda reproducir.
        </li>
        <li>Las respuestas del asistente citan las evidencias (consultas a la base, informes y documentos) que usó.</li>
      </ul>
    ),
  },
  {
    id: "reutilizacion",
    title: "Cómo reutilizar los resultados",
    body: (
      <>
        <p>
          Puedes reutilizar los índices, informes y mapas de Bosque Vivo con fines académicos, periodísticos o de
          veeduría ciudadana, siempre que:
        </p>
        <ul>
          <li>Cites «Bosque Vivo, Politécnico Colombiano Jaime Isaza Cadavid» y la fecha de consulta.</li>
          <li>Cites también las fuentes originales indicadas arriba, como exigen sus licencias.</li>
          <li>Indiques la versión de la metodología y las limitaciones que aparecen en el informe.</li>
          <li>No presentes los resultados como una certificación ni como una acusación contra nadie.</li>
        </ul>
      </>
    ),
  },
  {
    id: "limitaciones",
    title: "Limitaciones y descargo",
    body: (
      <ul>
        <li>
          La base de Karnik et al. no es un censo: no incluye todos los proyectos y sus contornos pueden diferir de los
          oficiales.
        </li>
        <li>Hansen mide pérdida de cobertura arbórea, sin distinguir tala, incendio, plaga o manejo autorizado.</li>
        <li>
          La resolución (10 m a 250 m según el sensor) impide ver claros pequeños; la nubosidad de la selva húmeda
          reduce los datos válidos, y la confianza del índice lo refleja.
        </li>
        <li>
          Los resultados son observaciones; las causas y responsabilidades solo pueden establecerse con verificación en
          campo. Detalles en{" "}
          <Link href="/metodologia" className="underline underline-offset-4">
            Metodología
          </Link>
          .
        </li>
      </ul>
    ),
  },
  {
    id: "personales",
    title: "Datos personales",
    body: (
      <p>
        Los datos de los proyectos no son datos personales. Lo que tratamos de quienes usan el asistente o el área de
        auditores se explica en la{" "}
        <Link href="/privacidad" className="underline underline-offset-4">
          política de privacidad
        </Link>
        .
      </p>
    ),
  },
  {
    id: "correcciones",
    title: "Correcciones",
    body: (
      <p>
        Si eres parte de un proyecto y crees que un polígono, una fecha o un resultado es incorrecto, escríbenos a{" "}
        <ContactLine /> con la evidencia. Revisaremos el caso y, si corresponde, corregiremos los datos y lo indicaremos
        en el informe.
      </p>
    ),
  },
];

export default function DataUsePage() {
  return (
    <LegalDocument
      eyebrow="Datos abiertos"
      title="Uso de datos y fuentes"
      version="v1"
      current="/uso-de-datos"
      intro={
        <p>De dónde vienen los datos, con qué licencias se usan, cómo citarlos y qué no se puede concluir de ellos.</p>
      }
      sections={SECTIONS}
    />
  );
}
