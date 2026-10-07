import copy

import pytest

from agent.packet import PACKET_SCHEMA, PacketError, audit, validate


def make_packet():
    return {
        "company": {"name": "Acme", "one_liner": "x", "sector": "fintech", "jurisdiction": "Delaware, US"},
        "stages": [
            {
                "name": "Formation",
                "goal": "exist legally",
                "exit_criteria": "entity formed",
                "tasks": [
                    {"title": "Draft bylaws", "owner": "agent", "status": "drafted"},
                    {"title": "Pick entity type", "owner": "ceo", "status": "needs_decision"},
                    {"title": "File 83(b)", "owner": "professional", "status": "needs_professional"},
                ],
            }
        ],
        "compliance": [
            {"item": "83(b) election", "why": "tax", "when": "30 days", "source_url": "https://www.irs.gov/a", "confidence": "sourced"},
            {"item": "Money transmitter", "why": "fintech", "when": "pre-launch", "source_url": "", "confidence": "sourced"},
        ],
        "hires": [{"role": "Founding engineer", "stage": "Formation", "why": "build"}],
        "funding": [
            {"name": "Fund A", "type": "pre-seed VC", "why_fit": "fintech", "source_url": "https://dead.example/x", "confidence": "sourced"}
        ],
        "decisions": [
            {"id": "entity", "question": "Entity type?", "options": ["C-corp", "LLC"], "recommended": "C-corp", "why": "VC norm"}
        ],
        "drafts": [{"title": "Investor one-pager", "kind": "one_pager", "body": "..."}],
        "limits": ["Not legal advice."],
    }


def alive(url):
    return "dead" not in url


def test_schema_is_strict_everywhere():
    def walk(node):
        if node.get("type") == "object":
            assert node["additionalProperties"] is False
            assert sorted(node["required"]) == sorted(node["properties"])
            for child in node["properties"].values():
                walk(child)
        if node.get("type") == "array":
            walk(node["items"])

    walk(PACKET_SCHEMA)


def test_validate_accepts_good_packet():
    assert validate(make_packet()) is None


def test_validate_rejects_missing_section():
    packet = make_packet()
    del packet["decisions"]
    with pytest.raises(PacketError, match="decisions"):
        validate(packet)


def test_validate_rejects_recommendation_outside_options():
    packet = make_packet()
    packet["decisions"][0]["recommended"] = "S-corp"
    with pytest.raises(PacketError, match="recommended"):
        validate(packet)


def test_validate_rejects_single_option_decision():
    packet = make_packet()
    packet["decisions"][0]["options"] = ["C-corp"]
    with pytest.raises(PacketError, match="options"):
        validate(packet)


def test_audit_downgrades_missing_and_dead_sources():
    audited, report = audit(make_packet(), alive)
    assert [c["confidence"] for c in audited["compliance"]] == ["sourced", "unverified"]
    assert audited["funding"][0]["confidence"] == "unverified"
    assert report["sources"] == {"claimed": 3, "verified": 1, "downgraded": 2}


def test_audit_rejects_non_http_urls_without_fetching():
    packet = make_packet()
    packet["compliance"][0]["source_url"] = "javascript:alert(1)"
    calls = []
    audited, _ = audit(packet, lambda url: calls.append(url) or True)
    assert audited["compliance"][0]["confidence"] == "unverified"
    assert audited["compliance"][0]["source_url"] == ""
    assert "javascript:alert(1)" not in calls


def test_audit_counts_who_does_the_work():
    _, report = audit(make_packet(), alive)
    assert report["workload"] == {"agent": 1, "ceo": 1, "professional": 1, "total": 3}
    assert report["decisions"] == 1


def test_audit_does_not_mutate_input():
    packet = make_packet()
    before = copy.deepcopy(packet)
    audit(packet, alive)
    assert packet == before


def test_validate_rejects_duplicate_decision_ids():
    packet = make_packet()
    packet["decisions"] = [packet["decisions"][0], dict(packet["decisions"][0])]
    with pytest.raises(PacketError, match="duplicate"):
        validate(packet)
