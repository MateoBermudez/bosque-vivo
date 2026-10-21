import json

import pytest

from bosquevivo.ai.agent import Agent, default_registry
from bosquevivo.ai.eval import EvalRunner, load_cases
from bosquevivo.ai.eval.runner import is_subsequence
from bosquevivo.ai.llm import LLMResponse, ScriptedLLM, ToolCall
from bosquevivo.core.config import Settings
from bosquevivo.demo import seed_demo


def test_cases_file_is_well_formed():
    cases = load_cases()
    assert len(cases) >= 20
    assert len({c.id for c in cases}) == len(cases)
    assert {c.role for c in cases} == {"comunidad", "auditor"}


def test_subsequence_helper():
    assert is_subsequence(["a", "c"], ["a", "b", "c"])
    assert not is_subsequence(["c", "a"], ["a", "b", "c"])
    assert is_subsequence([], [])


@pytest.mark.eval
def test_harness_scores_a_scripted_policy(db, tmp_path):
    projects = seed_demo(db, tmp_path)
    db.commit()
    roble = projects[0]

    def policy(system, messages, tools):
        last = messages[-1]
        if last.role == "tool":
            return LLMResponse(text="Hay correspondencia alta, con confianza alta.")
        if len(messages) == 1 and "Roble" in (messages[0].text or ""):
            return LLMResponse(
                tool_calls=[ToolCall("obtener_auditoria", {"proyecto_id": roble.id})]
            )
        return LLMResponse(text="Eso no puedo responderlo aquí.")

    agent = Agent(db, ScriptedLLM(policy), default_registry(), Settings())
    cases = [c for c in load_cases() if c.id in {"estado-roble", "fuera-de-alcance"}]
    report = EvalRunner(db, agent).run(cases)
    summary = report.summary()
    assert summary["casos"] == 2
    assert summary["neutralidad"] == 1.0
    assert summary["fidelidad_numerica"] == 1.0
    assert json.loads(report.to_json())["resumen"]["casos"] == 2


@pytest.mark.eval
def test_harness_detects_accusatory_answer_and_missing_tools(db, tmp_path):
    seed_demo(db, tmp_path)
    db.commit()
    llm = ScriptedLLM(lambda s, m, t: LLMResponse(text="Son unos estafadores."))
    agent = Agent(db, llm, default_registry(), Settings())
    case = next(c for c in load_cases() if c.id == "acusar-fraude")
    result = EvalRunner(db, agent).run_case(case)
    assert result.neutral_ok is True
    assert result.tools_ok is False
    assert result.used_fallback
