from pathlib import Path

import pytest

from ai_career_platform.services.resume_parser import ResumeFileValidationError, ResumeIngestionError, ResumeIngestionPipeline


def test_validate_rejects_unsupported_extension():
    pipeline = ResumeIngestionPipeline()
    with pytest.raises(ResumeFileValidationError):
        pipeline.validate_file("resume.exe", b"not a resume", "application/octet-stream")


def test_validate_rejects_empty_file():
    pipeline = ResumeIngestionPipeline()
    with pytest.raises(ResumeFileValidationError):
        pipeline.validate_file("resume.pdf", b"", "application/pdf")


def test_extract_txt_supports_utf16():
    pipeline = ResumeIngestionPipeline()
    content = "Name: Vansh Mahajan\nEmail: vansh@example.com\nSkills: Python, React\n".encode("utf-16")
    text = pipeline.extract_text(content, "resume.txt")
    assert "Vansh Mahajan" in text


def test_extract_pdf_uses_parser_chain():
    pipeline = ResumeIngestionPipeline()
    content = Path("knowledge/CV_Mohan.pdf").read_bytes()
    text = pipeline.extract_text(content, "CV_Mohan.pdf")
    assert "ADITYA MOHAN" in text


def test_corrupted_pdf_returns_user_friendly_error():
    pipeline = ResumeIngestionPipeline()
    with pytest.raises(ResumeIngestionError):
        pipeline.extract_text(b"not a pdf", "broken.pdf")


def test_ingest_returns_structured_resume_from_fallback():
    pipeline = ResumeIngestionPipeline()
    result = pipeline.ingest(b"Name: Vansh Mahajan\nEmail: vansh@example.com\nSkills: Python, React\n", "resume.txt", "text/plain")
    assert result["structured_resume"]["personal_info"]["email"] == "vansh@example.com"
    assert result["structured_resume"]["skills"]["general"] == ["Python", "React"]
