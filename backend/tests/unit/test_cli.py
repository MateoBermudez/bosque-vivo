import pytest

from bosquevivo.cli import build_parser


def test_parser_accepts_known_commands():
    parser = build_parser()
    assert parser.parse_args(["init-db"]).command == "init-db"
    args = parser.parse_args(["import", "datos.gpkg", "--source", "karnik", "--limit", "5"])
    assert args.path == "datos.gpkg" and args.limit == 5
    assert parser.parse_args(["audit", "3"]).project_id == 3


def test_parser_rejects_missing_command():
    with pytest.raises(SystemExit):
        build_parser().parse_args([])
