from stale_obsidian_note_detector.logic import count_links, StaleDetectorError, ProviderSetupError, LLMRunError


def test_count_links():
    content = "This is a [[Link 1]] and another [[Link 2]]."
    assert count_links(content) == 2

    assert count_links("No links here.") == 0
    assert count_links("[[One link]]") == 1


class TestTypedErrors:
    def test_error_hierarchy(self):
        assert issubclass(ProviderSetupError, StaleDetectorError)
        assert issubclass(LLMRunError, StaleDetectorError)

    def test_provider_setup_error_message(self):
        err = ProviderSetupError("bad provider")
        assert "bad provider" in str(err)

    def test_llm_run_error_message(self):
        err = LLMRunError("timeout")
        assert "timeout" in str(err)
