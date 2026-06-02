from risk_guidance import build_guidance_link, normalize_focus


def test_build_guidance_link_encodes_focus_dimension():
    link = build_guidance_link("Fitness risk")
    assert link == "?page=guidance&focus=Fitness%20risk"


def test_normalize_focus_decodes_plus_encoded_string():
    assert normalize_focus("Fitness+risk") == "Fitness risk"
    assert normalize_focus("Fitness%20risk") == "Fitness risk"
    assert normalize_focus(None) is None
