import pytest

from bosquevivo.audit import AuditService
from bosquevivo.demo import DEMO_PROJECTS, seed_demo


@pytest.fixture
def seeded(db, tmp_path):
    projects = seed_demo(db, tmp_path)
    db.commit()
    return dict(zip([s.registry_id for s in DEMO_PROJECTS], projects, strict=True))


@pytest.mark.golden
@pytest.mark.parametrize("spec", DEMO_PROJECTS, ids=lambda s: s.registry_id)
def test_expected_category(db, seeded, spec):
    run = AuditService(db).latest(seeded[spec.registry_id].id)
    assert run is not None and run.result is not None
    assert run.result.category == spec.expected_category


@pytest.mark.golden
def test_intact_scores_higher_than_damaged(db, seeded):
    audit = AuditService(db)
    good = audit.latest(seeded["DEMO-1"].id).result
    bad = audit.latest(seeded["DEMO-2"].id).result
    assert good.score is not None and bad.score is not None
    assert good.score - bad.score > 30


@pytest.mark.golden
def test_insufficient_project_has_no_score_and_low_confidence(db, seeded):
    result = AuditService(db).latest(seeded["DEMO-3"].id).result
    assert result.score is None
    assert result.confidence_label == "baja"
