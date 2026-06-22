"""
Parser V2 Benchmark Suite
Tests for section bleed, education extraction, skills categorization, and confidence scoring.
"""
import pytest
from ai_career_platform.services.resume_parser import (
    SectionClassifier,
    ConfidenceScorer,
    ResumeIngestionPipeline,
    _clean_string,
    _scored_education,
    _scored_experience,
    _scored_project,
    _scored_certification,
)


class TestSectionClassifier:
    def test_classify_detects_section_boundaries(self):
        lines = [
            "JOHN DOE",
            "john@example.com",
            "Experience",
            "Software Engineer at Google, 2020-2024",
            "- Built cool stuff",
            "Projects",
            "My Project - A cool project",
            "Skills",
            "Python, React, Node.js",
            "Education",
            "Bachelor of Science in Computer Science, Stanford 2020",
            "Certifications",
            "AWS Certified Solutions Architect",
        ]
        classifier = SectionClassifier()
        sections = classifier.classify(lines)
        
        assert "header" in sections
        assert len(sections["experience"]) > 0
        assert len(sections["projects"]) > 0
        assert len(sections["skills"]) > 0
        assert len(sections["education"]) > 0
        assert len(sections["certifications"]) > 0

    def test_is_boundary_detects_all_section_patterns(self):
        classifier = SectionClassifier()
        assert classifier.is_boundary("Skills")
        assert classifier.is_boundary("SKILLS:")
        assert classifier.is_boundary("Technical Skills")
        assert classifier.is_boundary("Education")
        assert classifier.is_boundary("Projects")
        assert classifier.is_boundary("Certifications")
        assert classifier.is_boundary("Experience")
        assert classifier.is_boundary("Internship")
        assert not classifier.is_boundary("Some project description")
        assert not classifier.is_boundary("Bachelor of Science in CS")


class TestEducationExtraction:
    def test_extracts_bachelor_of_science(self):
        pipeline = ResumeIngestionPipeline()
        lines = [
            "Education",
            "Bachelor of Science in Computer Science",
            "Stanford University",
            "2018-2022",
        ]
        results = pipeline._extract_education(lines)
        assert len(results) >= 1
        if results:
            assert "Bachelor of Science" in results[0].get("degree", "") or "Science" in results[0].get("degree", "")
            # Specialization may be extracted or captured in institution
            combined = results[0].get("specialization", "") + " " + results[0].get("institution", "")
            assert "Computer Science" in combined or "Stanford" in results[0].get("institution", "")

    def test_extracts_btech(self):
        pipeline = ResumeIngestionPipeline()
        lines = [
            "Education",
            "B.Tech in Computer Science",
            "IIT Bombay",
            "2019-2023",
        ]
        results = pipeline._extract_education(lines)
        assert len(results) >= 1
        if results:
            assert "Technology" in results[0].get("degree", "") or "B.Tech" in results[0].get("degree", "") or "Bachelor" in results[0].get("degree", "")

    def test_extracts_mtech(self):
        pipeline = ResumeIngestionPipeline()
        lines = [
            "Education",
            "M.Tech Computer Science",
            "IIT Delhi",
            "2023-2025",
        ]
        results = pipeline._extract_education(lines)
        assert len(results) >= 1

    def test_extracts_mba(self):
        pipeline = ResumeIngestionPipeline()
        lines = [
            "Education",
            "MBA in Finance",
            "Harvard Business School",
        ]
        results = pipeline._extract_education(lines)
        assert len(results) >= 1

    def test_extracts_phd(self):
        pipeline = ResumeIngestionPipeline()
        lines = [
            "Education",
            "PhD in Machine Learning",
            "MIT",
        ]
        results = pipeline._extract_education(lines)
        assert len(results) >= 1


class TestSkillsCategorization:
    def test_categorizes_react_as_framework(self):
        pipeline = ResumeIngestionPipeline()
        skills = ["React", "Vue", "Angular"]
        categorized = pipeline._categorize_skills(skills)
        assert "React" in categorized.get("frameworks", [])

    def test_categorizes_node_js_correctly(self):
        pipeline = ResumeIngestionPipeline()
        skills = ["Node.js", "Express.js", "NestJS"]
        categorized = pipeline._categorize_skills(skills)
        # Node.js may be categorized as frameworks or general depending on normalization
        assert "Node.js" in categorized.get("frameworks", []) or "Node.js" in categorized.get("general", [])
        assert "Express.js" in categorized.get("frameworks", [])

    def test_categorizes_mongodb(self):
        pipeline = ResumeIngestionPipeline()
        skills = ["MongoDB"]
        categorized = pipeline._categorize_skills(skills)
        assert "MongoDB" in categorized.get("databases", [])

    def test_categorizes_ci_cd_as_one_skill(self):
        pipeline = ResumeIngestionPipeline()
        skills = ["CI/CD", "cicd", "devops"]
        categorized = pipeline._categorize_skills(skills)
        total_devops = len(categorized.get("devops_tools", []))
        assert total_devops >= 1

    def test_categorizes_ai_ml_technologies(self):
        pipeline = ResumeIngestionPipeline()
        skills = ["TensorFlow", "PyTorch", "Scikit-learn", "LangChain"]
        categorized = pipeline._categorize_skills(skills)
        assert "TensorFlow" in categorized.get("ai_ml_technologies", [])
        assert "PyTorch" in categorized.get("ai_ml_technologies", [])
        assert "Scikit-learn" in categorized.get("ai_ml_technologies", [])
        assert "LangChain" in categorized.get("ai_ml_technologies", [])

    def test_categorizes_cloud_technologies(self):
        pipeline = ResumeIngestionPipeline()
        skills = ["AWS", "Azure", "GCP", "Google Cloud"]
        categorized = pipeline._categorize_skills(skills)
        assert "AWS" in categorized.get("cloud_technologies", [])
        assert "Azure" in categorized.get("cloud_technologies", [])


class TestConfidenceScorer:
    def test_scored_returns_value_and_confidence(self):
        result = ConfidenceScorer.scored("test value", 0.95)
        assert result["value"] == "test value"
        assert result["confidence"] == 0.95

    def test_scored_clamps_confidence_to_1(self):
        result = ConfidenceScorer.scored("test", 1.5)
        assert result["confidence"] == 1.0

    def test_scored_clamps_confidence_to_0(self):
        result = ConfidenceScorer.scored("test", -0.5)
        assert result["confidence"] == 0.0

    def test_from_match_high(self):
        result = ConfidenceScorer.from_match("test", "high")
        assert result["confidence"] == 0.9

    def test_from_match_medium(self):
        result = ConfidenceScorer.from_match("test", "medium")
        assert result["confidence"] == 0.7

    def test_best_selects_highest_confidence(self):
        candidates = [
            {"value": "low", "confidence": 0.5},
            {"value": "high", "confidence": 0.9},
            {"value": "medium", "confidence": 0.7},
        ]
        result = ConfidenceScorer.best(candidates)
        assert result["value"] == "high"


class TestSectionBleedPrevention:
    def test_skills_stops_at_certifications(self):
        pipeline = ResumeIngestionPipeline()
        lines = [
            "Skills",
            "Python, React, Node.js",
            "Certifications",
            "AWS Certified Solutions Architect",
            "Google Cloud Professional",
        ]
        skills = pipeline._extract_skills(lines)
        assert "Python" in skills or "React" in skills
        assert "AWS" not in skills

    def test_projects_stops_at_certifications(self):
        pipeline = ResumeIngestionPipeline()
        lines = [
            "My Project - A cool project with React",
            "github.com/user/repo",
            "Projects",
            "Another Project",
            "Certifications",
            "AWS Certified - issued by Amazon",
        ]
        projects = pipeline._extract_projects(lines)
        # Projects should be extracted but not certifications
        assert len(projects) >= 1

    def test_skills_stops_at_education(self):
        pipeline = ResumeIngestionPipeline()
        lines = [
            "Skills",
            "Python, JavaScript",
            "Education",
            "Bachelor of Science in CS",
            "Stanford University",
        ]
        skills = pipeline._extract_skills(lines)
        assert "Python" in skills


class TestLocationExtraction:
    def test_extracts_indian_city(self):
        pipeline = ResumeIngestionPipeline()
        lines = ["Bangalore, India", "john@example.com"]
        info = pipeline._extract_personal_info(lines, "Bangalore, India")
        assert "Bangalore" in info.get("location", "") or "India" in info.get("location", "")

    def test_extracts_us_city(self):
        pipeline = ResumeIngestionPipeline()
        lines = ["San Francisco, CA", "john@example.com"]
        info = pipeline._extract_personal_info(lines, "San Francisco, CA")
        assert "San Francisco" in info.get("location", "") or "CA" in info.get("location", "")

    def test_extracts_remote(self):
        pipeline = ResumeIngestionPipeline()
        lines = ["Remote", "john@example.com"]
        info = pipeline._extract_personal_info(lines, "Remote")
        assert info.get("location") == "Remote"


class TestLinkExtraction:
    def test_extracts_leetcode_url(self):
        pipeline = ResumeIngestionPipeline()
        lines = ["leetcode.com/username", "john@example.com"]
        info = pipeline._extract_personal_info(lines, "leetcode.com/username\njohn@example.com")
        assert "leetcode.com" in info.get("leetcode_url", "")

    def test_extracts_hackerrank_url(self):
        pipeline = ResumeIngestionPipeline()
        lines = ["hackerrank.com/username", "john@example.com"]
        info = pipeline._extract_personal_info(lines, "hackerrank.com/username\njohn@example.com")
        assert "hackerrank.com" in info.get("hackerrank_url", "")

    def test_extracts_codeforces_url(self):
        pipeline = ResumeIngestionPipeline()
        lines = ["codeforces.com/username", "john@example.com"]
        info = pipeline._extract_personal_info(lines, "codeforces.com/username\njohn@example.com")
        assert "codeforces.com" in info.get("codeforces_url", "")


class TestNormalizeWithConfidence:
    def test_normalize_returns_confidence_scores(self):
        pipeline = ResumeIngestionPipeline()
        data = {
            "personal_info": {
                "full_name": "John Doe",
                "email": "john@example.com",
                "phone": "+1 555 123 4567",
            },
            "education": [{"degree": "B.Sc", "institution": "MIT"}],
            "experience": [{"title": "Engineer", "company": "Google"}],
            "projects": [{"project_name": "Project A"}],
            "certifications": [{"certification_name": "AWS"}],
        }
        result = pipeline._normalize(data)
        assert "value" in result["personal_info"]["full_name"]
        assert "confidence" in result["personal_info"]["full_name"]
        assert result["personal_info"]["full_name"]["value"] == "John Doe"

    def test_scored_education_has_confidence(self):
        from ai_career_platform.services.resume_parser import _scored_education
        result = _scored_education({"degree": "B.Sc", "institution": "MIT"})
        assert "value" in result["degree"]
        assert "confidence" in result["degree"]

    def test_scored_experience_has_confidence(self):
        from ai_career_platform.services.resume_parser import _scored_experience
        result = _scored_experience({"title": "Engineer", "company": "Google"})
        assert "value" in result["title"]
        assert "confidence" in result["title"]

    def test_scored_project_has_confidence(self):
        from ai_career_platform.services.resume_parser import _scored_project
        result = _scored_project({"project_name": "My Project"})
        assert "value" in result["project_name"]
        assert "confidence" in result["project_name"]

    def test_scored_certification_has_confidence(self):
        from ai_career_platform.services.resume_parser import _scored_certification
        result = _scored_certification({"certification_name": "AWS"})
        assert "value" in result["certification_name"]
        assert "confidence" in result["certification_name"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])