import pytest

from agent.tests.test_packet import alive, make_packet
from agent.worker import Deps, WorkerError, build_row, run


def make_deps(**overrides):
    saved = []
    base = dict(
        research=lambda idea: ("agent37", "notes about " + idea),
        structure=lambda idea, notes: make_packet(),
        url_ok=alive,
        save=lambda row: saved.append(row) or {"id": 7},
    )
    return Deps(**{**base, **overrides}), saved


def test_run_saves_audited_packet_with_provenance():
    deps, saved = make_deps()
    result = run("an idea for a fintech", deps)
    assert result["id"] == 7
    spec = saved[0]["spec"]
    assert saved[0]["title"] == "Acme"
    assert spec["kind"] == "startup-packet"
    assert spec["worker"] == "agent37"
    assert spec["idea"] == "an idea for a fintech"
    assert spec["audit"]["sources"]["downgraded"] == 2
    assert spec["packet"]["funding"][0]["confidence"] == "unverified"


@pytest.mark.parametrize("idea", ["", "   ", "x" * 4001])
def test_run_rejects_bad_idea_before_spending(idea):
    calls = []
    deps, saved = make_deps(research=lambda i: calls.append(i))
    with pytest.raises(WorkerError):
        run(idea, deps)
    assert calls == [] and saved == []


def test_run_does_not_save_an_invalid_packet():
    broken = make_packet()
    del broken["stages"]
    deps, saved = make_deps(structure=lambda idea, notes: broken)
    with pytest.raises(WorkerError, match="stages"):
        run("an idea", deps)
    assert saved == []


def test_build_row_shape():
    row = build_row("idea", "openai-direct", make_packet(), {"sources": {}})
    assert set(row) == {"title", "spec"}
    assert set(row["spec"]) == {"kind", "idea", "worker", "packet", "audit"}


def test_main_reports_unexpected_errors_cleanly(monkeypatch):
    from agent import worker

    monkeypatch.setattr(worker.clients, "load_env", lambda path: (_ for _ in ()).throw(KeyError("choices")))
    assert worker.main(["an idea"]) == 1


def packet_row():
    return {"id": 1, "title": "Acme", "spec": {"kind": "startup-packet", "idea": "an idea", "worker": "agent37", "packet": make_packet(), "audit": {}}}


def decision_row(row_id, choice, packet_id=1, decision_id="entity"):
    return {"id": row_id, "spec": {"kind": "startup-decision", "packet_id": packet_id, "decision_id": decision_id, "choice": choice}}


def test_collect_choices_latest_valid_choice_wins():
    from agent.worker import collect_choices

    rows = [decision_row(5, "LLC"), decision_row(9, "C-corp"), decision_row(7, "LLC")]
    assert collect_choices(packet_row(), rows) == {"entity": "C-corp"}


def test_collect_choices_ignores_untrusted_junk():
    from agent.worker import collect_choices

    rows = [
        decision_row(9, "S-corp <script>"),  # not one of the options
        decision_row(8, "LLC", packet_id=2),  # another packet
        decision_row(7, "LLC", decision_id="nope"),  # unknown decision
        {"id": 6, "spec": None},
        {"id": 5},
    ]
    assert collect_choices(packet_row(), rows) == {}


def test_steer_saves_a_revision_that_records_the_choices():
    from agent.worker import steer

    seen = []
    deps, saved = make_deps(research=lambda brief: seen.append(brief) or ("agent37", "notes"))
    steer(packet_row(), {"entity": "C-corp"}, deps)
    spec = saved[0]["spec"]
    assert spec["revision_of"] == 1
    assert spec["decided"] == {"entity": "C-corp"}
    assert spec["idea"] == "an idea"
    assert "Entity type?" in seen[0] and "C-corp" in seen[0]


def test_steer_refuses_when_nothing_was_decided():
    from agent.worker import steer

    deps, saved = make_deps()
    with pytest.raises(WorkerError, match="No decisions"):
        steer(packet_row(), {}, deps)
    assert saved == []


def test_run_records_measured_seconds():
    deps, saved = make_deps()
    run("an idea", deps)
    assert isinstance(saved[0]["spec"]["audit"]["seconds"], float)
