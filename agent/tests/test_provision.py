from agent.provision import with_instance_id


def test_replaces_existing_line():
    assert with_instance_id("A=1\nAGENT37_INSTANCE_ID=\nB=2\n", "abc") == "A=1\nAGENT37_INSTANCE_ID=abc\nB=2\n"


def test_appends_when_absent():
    assert with_instance_id("A=1", "abc") == "A=1\nAGENT37_INSTANCE_ID=abc\n"
