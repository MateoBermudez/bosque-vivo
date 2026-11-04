from bosquevivo.ai.llm import UnavailableLLM
from bosquevivo.core.config import Settings
from bosquevivo.db.models import WaUser
from bosquevivo.measure import check_determinism, measure_audits, measure_chat, summarize
from bosquevivo.satellite.providers import FakeProvider
from tests.integration.test_whatsapp_flow import seeded

__all__ = ["seeded"]


def test_summarize_percentiles():
    summary = summarize([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 12.0], 10.0, 0.9)
    assert summary.p50 == 5.5 and summary.p90 == 9.0 and summary.maximum == 12.0
    assert summary.share_within_limit == 0.9 and summary.meets_target


def test_measure_chat_cleans_up(db, seeded):
    summary = measure_chat(
        db, Settings(phone_hmac_key="k"), UnavailableLLM("sin clave"), seeded.id, 10
    )
    assert summary.samples == 10
    assert db.query(WaUser).count() == 0


def test_measure_audits_and_determinism(db, seeded, tmp_path):
    summary, detail = measure_audits(db, FakeProvider(), tmp_path, [seeded.id], "v1")
    assert summary.samples == 1 and seeded.id in detail
    deterministic, scores = check_determinism(db, [seeded.id], "v1")
    assert deterministic and len(scores[seeded.id]) == 2
