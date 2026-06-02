from query_utils import build_page_query_params, resolve_section_page, sync_page_query_params


def test_build_page_query_params_for_overview():
    params = build_page_query_params("overview")

    assert params == {"page": ["overview"]}


def test_build_page_query_params_for_guidance_with_focus():
    params = build_page_query_params("guidance", "Fitness risk")

    assert params == {
        "page": ["guidance"],
        "focus": ["Fitness risk"],
    }


def test_build_page_query_params_clears_focus_when_not_guidance():
    params = build_page_query_params("overview", "Fitness risk")

    assert params == {"page": ["overview"]}


def test_sync_page_query_params_returns_expected_overview_params():
    params = sync_page_query_params("overview", "Fitness risk")

    assert params == {"page": ["overview"]}


def test_sync_page_query_params_returns_expected_guidance_params():
    params = sync_page_query_params("guidance", "Fitness risk")

    assert params == {
        "page": ["guidance"],
        "focus": ["Fitness risk"],
    }


def test_resolve_section_page_uses_query_page_when_session_state_missing():
    assert resolve_section_page("guidance", None) == "Guidance"


def test_resolve_section_page_keeps_session_page_if_same():
    assert resolve_section_page("guidance", "Guidance") == "Guidance"


def test_resolve_section_page_overrides_session_page_when_query_changes():
    assert resolve_section_page("overview", "Guidance") == "Overview"


def test_build_page_query_params_handles_unknown_section_as_guidance():
    params = build_page_query_params("random", "Fitness risk")

    assert params == {"page": ["random"]}
