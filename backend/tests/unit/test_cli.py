import pytest

from bosquevivo.cli import build_parser, main
from bosquevivo.core.config import Settings, get_settings


def test_parser_accepts_known_commands():
    parser = build_parser()
    assert parser.parse_args(["init-db"]).command == "init-db"
    args = parser.parse_args(["import", "datos.gpkg", "--source", "karnik", "--limit", "5"])
    assert args.path == "datos.gpkg" and args.limit == 5
    assert parser.parse_args(["audit", "3"]).project_id == 3


def test_parser_rejects_missing_command():
    with pytest.raises(SystemExit):
        build_parser().parse_args([])


def test_gemini_check_sin_clave_explica_donde_ponerla(monkeypatch, capsys):
    monkeypatch.setattr("bosquevivo.cli.get_settings", lambda: Settings(gemini_api_key=""))
    get_settings.cache_clear()

    assert main(["gemini-check"]) == 1
    assert "GEMINI_API_KEY" in capsys.readouterr().out
