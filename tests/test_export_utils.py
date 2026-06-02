import os
from export_utils import build_markdown_filename, export_markdown_to_file, markdown_bytes, pdf_bytes


def test_build_markdown_filename_contains_route_and_days():
    filename = build_markdown_filename("Patagonia W Trek", {"number_of_days": 5, "pack_weight_preference": "Light"})
    assert filename.startswith("Patagonia_W_Trek_5d_light_briefing")
    assert filename.endswith(".md")


def test_export_markdown_to_file(tmp_path):
    markdown = "# Test Briefing\n- sample item"
    file_path = tmp_path / "briefing.md"
    returned_path = export_markdown_to_file(markdown, file_path)

    assert os.path.exists(returned_path)
    assert returned_path.read_text(encoding="utf-8") == markdown


def test_markdown_bytes_returns_utf8_bytes():
    text = "# Heading\nLine"
    data = markdown_bytes(text)

    assert isinstance(data, bytes)
    assert data.decode("utf-8") == text


def test_pdf_bytes_returns_valid_pdf():
    data = pdf_bytes("# Heading\n\n- item one\n- item two\n\nSome body text.")
    assert isinstance(data, bytes)
    assert data[:4] == b"%PDF"


def test_pdf_bytes_with_title():
    data = pdf_bytes("# Test", title="My Expedition")
    assert data[:4] == b"%PDF"
    assert len(data) > 100


def test_pdf_bytes_handles_empty_content():
    data = pdf_bytes("")
    assert data[:4] == b"%PDF"
