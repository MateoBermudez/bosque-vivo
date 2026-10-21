// Textos de apoyo. Reflejan la base de conocimiento del backend
// (backend/src/bosquevivo/ai/knowledge/corpus) y el ERS: si allá cambian, se actualizan aquí.

export const GLOSSARY: { term: string; definition: string }[] = [
  {
    term: "NDVI",
    definition:
      "Un número entre -1 y 1 que se calcula con las imágenes del satélite. Mientras más alto, más verde y sana está la vegetación. Un bosque denso suele estar por encima de 0,7.",
  },
  {
    term: "Sentinel-2",
    definition: "Satélite europeo que toma fotos de la Tierra cada 5 días con detalle de 10 metros. Se usa desde 2017.",
  },
  {
    term: "Landsat",
    definition:
      "Serie de satélites de Estados Unidos que toman fotos desde hace décadas con detalle de 30 metros. Sirve para mirar el pasado.",
  },
  {
    term: "Hansen",
    definition:
      "Mapa mundial que muestra dónde se perdieron árboles cada año desde el 2001. Se usa para calcular las hectáreas perdidas.",
  },
  { term: "Polígono", definition: "Es el contorno del terreno del proyecto, registrado públicamente." },
  {
    term: "T0",
    definition:
      "Es la fecha desde la que el proyecto empezó a contar como acreditado. Se compara lo que pasó antes y después.",
  },
  {
    term: "Crédito de carbono",
    definition:
      "Certificado que representa una tonelada de dióxido de carbono que, según el proyecto, se evitó emitir o se capturó.",
  },
  {
    term: "REDD+",
    definition: "Tipo de proyecto que busca evitar la deforestación y la degradación de bosques.",
  },
  {
    term: "MRV",
    definition:
      "Medición, Reporte y Verificación: el proceso con el que se certifica cuánto carbono captura o evita un proyecto.",
  },
  {
    term: "Correspondencia observada",
    definition:
      "Qué tanto coincide lo que se ve desde el satélite con lo que el proyecto declara. No es una acusación a nadie.",
  },
  {
    term: "Nubosidad",
    definition: "Cuando hay nubes, el satélite no ve el suelo. Por eso a veces no se puede concluir con seguridad.",
  },
];

export const FAQ: { question: string; answer: string }[] = [
  {
    question: "¿Bosque Vivo acusa a alguien de fraude?",
    answer:
      "No. Bosque Vivo describe lo que se observa desde el satélite frente a lo que declara un proyecto. No atribuye intenciones ni emite juicios sobre las personas.",
  },
  {
    question: "¿Por qué a veces dice que no hay datos suficientes?",
    answer:
      "Porque las nubes o la falta de imágenes impiden medir con seguridad. Prefiere decir que no puede concluir antes que dar un número dudoso.",
  },
  {
    question: "¿Qué tan segura es la respuesta?",
    answer:
      "Cada respuesta indica una confianza alta, media o baja. Si es baja, conviene hablar con una persona del equipo.",
  },
  {
    question: "¿Quién procesa mi mensaje?",
    answer:
      "Un asistente de inteligencia artificial, con apoyo de un servicio de un tercero. Por eso no debe enviar datos como cédula o dirección. Puede pedir que se borren sus datos en cualquier momento.",
  },
  {
    question: "¿Qué pasa con mis fotos y audios?",
    answer:
      "Solo se usan si usted lo autoriza de forma expresa. Se tratan como información de la comunidad que aún no está verificada.",
  },
  {
    question: "¿Cada cuánto se actualizan los resultados?",
    answer: "Los resultados se calculan cuando se solicita un análisis y se muestra siempre la fecha del cálculo.",
  },
  {
    question: "¿Qué es Verra y qué es Gold Standard?",
    answer:
      "Son dos organizaciones que certifican proyectos de créditos de carbono y publican registros públicos de esos proyectos.",
  },
];

export const REGULATIONS: { name: string; summary: string }[] = [
  {
    name: "Ley 1931 de 2018",
    summary:
      "Establece directrices para la gestión del cambio climático en Colombia y crea el Registro Nacional de Reducción de las Emisiones de Gases de Efecto Invernadero (RENARE).",
  },
  {
    name: "Resolución 1447 de 2018",
    summary: "Reglamenta el sistema de monitoreo, reporte y verificación (MRV) de las acciones de mitigación y el RENARE.",
  },
  {
    name: "Decreto 926 de 2017",
    summary: "Reglamenta el impuesto nacional al carbono y el mecanismo de no causación mediante la cancelación de créditos de carbono.",
  },
  {
    name: "Ley 2169 de 2021",
    summary: "Impulsa el desarrollo bajo en carbono del país mediante metas y medidas mínimas en materia de carbono neutralidad y resiliencia climática.",
  },
  {
    name: "Ley 1581 de 2012",
    summary:
      "Régimen general de protección de datos personales. Exige finalidad definida, autorización previa del titular y permite solicitar la supresión de los datos.",
  },
];

export const REFERENCES: string[] = [
  "Banin, L. F., et al. (2022). The road to recovery: a synthesis of outcomes from ecosystem restoration in tropical and sub-tropical Asian forests. Phil. Trans. R. Soc. B, 378(1867).",
  "DANE. (2024). Encuesta Nacional de Calidad de Vida (ECV) 2023: TIC en hogares.",
  "Drusch, M., et al. (2012). Sentinel-2: ESA's optical high-resolution mission for GMES operational services. Remote Sens. Environ., 120, 25–36.",
  "Foster, B. C., et al. (2017). Assessing audit impact and thoroughness of VCS forest carbon offset projects. Environ. Sci. Policy, 78, 121–141.",
  "Gorelick, N., et al. (2017). Google Earth Engine: Planetary-scale geospatial analysis for everyone. Remote Sens. Environ., 202, 18–27.",
  "Guizar-Coutiño, A., et al. (2022). A global evaluation of the effectiveness of voluntary REDD+ projects. Conserv. Biol., 36(6), e13970.",
  "IDEAM y MinAmbiente. (2025, 31 de julio). En 2024, Colombia consolidó la segunda cifra de deforestación más baja en la historia.",
  "Karnik, A., et al. (2025). An open-access database of nature-based carbon offset project boundaries. Sci. Data, 12, 581.",
  "Probst, B. S., et al. (2024). Systematic assessment of the achieved emission reductions of carbon crediting projects. Nat. Commun., 15, 9562.",
  "West, T. A. P., et al. (2023). Action needed to make carbon offsets from forest conservation work for climate change mitigation. Science, 381(6660), 873–877.",
];
