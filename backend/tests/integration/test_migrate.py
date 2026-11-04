from sqlalchemy import insert

from bosquevivo.db.migrate import copy_database
from bosquevivo.db.models import AuditorUser, Project
from bosquevivo.db.session import build_engine, init_db, make_session_factory
from bosquevivo.demo import seed_demo


def make_source(tmp_path):
    engine = build_engine(f"sqlite:///{tmp_path / 'origen.db'}")
    init_db(engine)
    with make_session_factory(engine)() as session:
        seed_demo(session, tmp_path / "images")
        session.add(AuditorUser(email="a@b.co", name="A", password_hash="x"))
        session.commit()
    return engine


def test_copies_every_table_and_refuses_to_overwrite(tmp_path):
    source = make_source(tmp_path)
    target = build_engine(f"sqlite:///{tmp_path / 'destino.db'}")
    report = copy_database(source, target)
    assert report.problems == []
    assert report.copied["project"] == 3 and report.copied["auditor_user"] == 1
    assert report.copied["ndvi_observation"] > 0
    again = copy_database(source, target)
    assert again.problems and "ya tiene datos" in again.problems[0]
    replaced = copy_database(source, target, replace=True)
    assert replaced.problems == [] and replaced.copied["project"] == 3


def test_reports_values_longer_than_the_column(tmp_path):
    source = make_source(tmp_path)
    with source.begin() as connection:
        connection.execute(
            insert(Project.__table__),
            {
                "source_registry": "x" * 60,
                "registry_id": "1",
                "name": "Largo",
                "geometry": "{}",
                "source": "prueba",
            },
        )
    report = copy_database(source, build_engine(f"sqlite:///{tmp_path / 'd.db'}"))
    assert any("project.source_registry" in problem for problem in report.problems)
    assert report.copied == {}
