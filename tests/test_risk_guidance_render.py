from unittest.mock import patch

from risk_guidance import GUIDANCE_POINTS, render_guidance_page


def test_render_guidance_page_with_focus_renders_primary_and_other_sections():
    with patch("risk_guidance.st.header") as header, \
         patch("risk_guidance.st.write") as write, \
         patch("risk_guidance.st.markdown") as markdown, \
         patch("risk_guidance.st.subheader") as subheader:
        render_guidance_page("Fitness risk")

    header.assert_called_once_with("Risk reduction guidance")
    assert any("Focus: Fitness risk" in str(call) for call in markdown.call_args_list)
    # "Other guidance" subheader only — focused dimension is rendered inline, not as a subheader
    assert subheader.call_count == 1


def test_render_guidance_page_without_focus_renders_all_sections():
    with patch("risk_guidance.st.header") as header, \
         patch("risk_guidance.st.write") as write, \
         patch("risk_guidance.st.markdown") as markdown, \
         patch("risk_guidance.st.subheader") as subheader:
        render_guidance_page(None)

    header.assert_called_once_with("Risk reduction guidance")
    assert subheader.call_count == len(GUIDANCE_POINTS)
