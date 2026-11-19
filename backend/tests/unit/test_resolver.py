import pytest

from bosquevivo.ai.agent.resolver import ProjectResolver, message_tokens, normalize

PROJECTS = [
    (1, "Carmen del Darien (CDD) REDD+ Project"),
    (2, "The Choco-Darien Conservation Corridor REDD Project"),
    (3, "Concosta REDD+ Project"),
    (4, "REDD+ Pazcifico"),
    (5, "Proyecto REDD+ Pazcifico Sur"),
    (6, "Cajambre REDD+ Project"),
    (7, "Awakadaa Matsiadali REDD+ Project"),
    (8, "Proyecto de Conservacion Delfines Cupica REDD+"),
    (9, "Grouped Project REDD+ Conservation of the Oak Ecosystem Corridor"),
    (10, "Yagual - Carbon Sequestration Grouped Project for Reforestation"),
    (11, "Mutatá REDD+ Project"),
    (12, "Blue Carbon Project Gulf of Morrosquillo Vida Manglar"),
    (13, "Pedeguita Jiguamiandó REDD+"),
    (14, "Riscales REDD+ Project"),
    (
        15,
        "Grouped Project for Commercial Forest Plantations Initiative in the Department of Vichada",
    ),
]


@pytest.fixture(scope="module")
def resolver():
    return ProjectResolver(PROJECTS)


def ids(resolution):
    return [c.project_id for c in resolution.candidates]


def test_normalize_quita_tildes_y_signos():
    assert normalize("¡Carmen del Darién!") == "carmen del darien"


def test_message_tokens_descarta_palabras_vacias():
    assert message_tokens("¿Cómo está el bosque?") == ["bosque"]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("¿Cómo está el bosque de Carmen del Darién?", 1),
        ("Quiero saber cómo va Concosta", 3),
        ("cómo está cajambre", 6),
        ("y awakadaa matsiadali?", 7),
        ("explícame el índice de Mutatá", 11),
        ("Delfines Cupica", 8),
        ("blue carbon morrosquillo", 12),
        ("Yagual", 10),
        ("riscales", 14),
        ("pazcifico sur", 5),
        ("REDD+ Pazcifico", 4),
    ],
)
def test_reconoce_el_proyecto_dentro_de_la_frase(resolver, text, expected):
    resolution = resolver.resolve(text)
    assert resolution.confident
    assert resolution.best.project_id == expected


@pytest.mark.parametrize(("text", "expected"), [("Concosa", 3), ("pedeguita jiguamiando", 13)])
def test_tolera_errores_de_tipeo(resolver, text, expected):
    resolution = resolver.resolve(text)
    assert resolution.confident and resolution.best.project_id == expected


@pytest.mark.parametrize("text", ["pazcifico", "como va el de pasifico"])
def test_pide_aclarar_cuando_hay_dos_candidatos(resolver, text):
    resolution = resolver.resolve(text)
    assert not resolution.confident
    assert set(ids(resolution)) == {4, 5}


def test_el_numero_explicito_gana(resolver):
    resolution = resolver.resolve("dame el proyecto 3")
    assert resolution.confident and resolution.best.project_id == 3


def test_un_numero_que_no_existe_no_resuelve_nada(resolver):
    assert resolver.resolve("proyecto 999").best is None


@pytest.mark.parametrize(
    "text",
    [
        "¿Qué es el NDVI?",
        "¿Cómo se calcula la permanencia forestal?",
        "Don Pedro dice que están talando cerca de mi finca",
        "¿Me das una receta de sancocho?",
        "Hola",
        "gracias",
        "cuál es el índice más bajo",
        "¿Qué proyectos hay en el Chocó?",
        "proyectos del Pacífico",
        "darién",
        "¿En qué departamento está?",
        "¿Dónde queda mi proyecto?",
        "¿En qué municipio queda?",
        "",
    ],
)
def test_no_inventa_proyectos_en_preguntas_generales(resolver, text):
    assert resolver.resolve(text).best is None


def test_una_region_sola_no_identifica_un_proyecto(resolver):
    assert resolver.resolve("choco").best is None


def test_una_palabra_comun_a_muchos_nombres_no_identifica(resolver):
    assert resolver.resolve("redd project").best is None


def test_sin_proyectos_no_falla():
    assert ProjectResolver([]).resolve("Carmen del Darién").best is None
