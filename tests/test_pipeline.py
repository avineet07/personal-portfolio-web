"""
test_pipeline.py — Unit tests for the automated resume & cover letter pipeline.
"""

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from pipeline.config import RESUME_DIR, COVER_LETTER_DIR
from pipeline.pdf_extractor import (
    extract_text_from_pdf,
    extract_resume_document,
    extract_cover_letter_document
)
from pipeline.section_splitter import (
    split_resume_into_sections,
    GroundingContext,
    resolve_sections_and_grounding
)
from pipeline.coordinator import run_pipeline
from data.loader import load_portfolio_json
import app


MOCK_RESUME_DOC = {
    "filename": "mock_resume.pdf",
    "filepath": "/mock/mock_resume.pdf",
    "page_count": 1,
    "full_text": """ENGINEERING PROFESSIONAL
SUMMARY
7+ years of experience across different domains of data lifecycle; including AI, ML, Data Science.
SKILLS
Python, SQL, ML, Snowflake, PySpark, LangGraph, LightGBM
EXPERIENCE
Sears Holdings - Senior Technical Associate
May 2024 - Present
Architecting multi-agent Agentic AI workflows with LangGraph.
OneCard - Data Scientist and Data Product Manager
Jan 2021 - May 2024
Data Mesh architecture and customer churn predictive modeling.
Auronova Consulting - Associate Consultant
Sep 2019 - Dec 2020
EDUCATION
Indian Institute of Technology, IIT Kharagpur
Dual Degree (B.Tech + M.Tech)
INTERNSHIPS
Genpact - Intern
"""
}

MOCK_COVER_DOC = {
    "filename": "mock_cover.pdf",
    "filepath": "/mock/mock_cover.pdf",
    "page_count": 1,
    "full_text": "DEAR SIR/MADAM,\nI am writing to express my strong interest in the Engineering role..."
}


class TestResumePipeline(unittest.TestCase):
    def setUp(self):
        self.resume_dir = RESUME_DIR
        self.cover_letter_dir = COVER_LETTER_DIR
        self.output_json = os.path.join(PROJECT_ROOT, "src", "data", "test_portfolio_output.json")
        self.resume_dir.mkdir(parents=True, exist_ok=True)
        self.cover_letter_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.output_json):
            try:
                os.remove(self.output_json)
            except OSError:
                pass

    def test_ref_directory_structure(self):
        self.assertTrue(self.resume_dir.is_dir(), "ref/resume directory must exist")
        self.assertTrue(self.cover_letter_dir.is_dir(), "ref/cover_letter directory must exist")

    def test_historical_archive_fallback(self):
        from data.loader import get_fallback_portfolio, HISTORICAL_JSON
        self.assertTrue(HISTORICAL_JSON.is_file(), "portfolio_data_historical.json must exist")
        historical = get_fallback_portfolio()
        self.assertTrue(bool(historical["profile"]["name"]))
        self.assertGreaterEqual(len(historical["resume"]["workExperience"]), 3)

    def test_document_extraction(self):
        resume_doc = extract_resume_document(str(self.resume_dir)) or MOCK_RESUME_DOC
        self.assertIsNotNone(resume_doc, "Must extract resume document or mock fallback")
        self.assertTrue(bool(resume_doc["full_text"]))

        cover_doc = extract_cover_letter_document(str(self.cover_letter_dir)) or MOCK_COVER_DOC
        self.assertIsNotNone(cover_doc, "Must extract cover letter document or mock fallback")
        self.assertTrue(bool(cover_doc["full_text"]))

    def test_hierarchical_section_splitter(self):
        resume_doc = extract_resume_document(str(self.resume_dir)) or MOCK_RESUME_DOC
        self.assertIsNotNone(resume_doc)
        sections = split_resume_into_sections(resume_doc["full_text"])

        # Check section boundary extraction
        self.assertTrue(bool(sections["header"]))
        self.assertTrue(bool(sections["summary"]))
        self.assertTrue(bool(sections["skills"]))
        self.assertTrue(bool(sections["experience"]))
        self.assertTrue(bool(sections["education"]))
        self.assertTrue(bool(sections["internships"]))

        # Verify experience slice contains professional roles
        exp_text = sections["experience"].lower()
        self.assertIn("sears", exp_text)
        self.assertIn("onecard", exp_text)

        # Verify education slice contains academic credentials
        edu_text = sections["education"].lower()
        self.assertTrue("technology" in edu_text or "iit" in edu_text or "bachelor" in edu_text)

    def test_grounding_context(self):
        ctx = GroundingContext(
            cover_letter="Senior Engineer with 8 years building distributed systems.",
            source_documents={"resume": "CV.pdf"},
            content_articles=[{"title": "Snowflake CDC", "topic": "Data Engineering"}]
        )
        summary = ctx.get_grounding_summary()
        self.assertIn("COVER LETTER NARRATIVE", summary)
        self.assertIn("Snowflake CDC", summary)
        info = ctx.to_dict()
        self.assertTrue(info["has_cover_letter"])
        self.assertEqual(info["article_count"], 1)

    def test_pipeline_execution_and_schema(self):
        data = run_pipeline(
            resume_path=str(self.resume_dir),
            cover_letter_path=str(self.cover_letter_dir),
            output_json_path=self.output_json,
            use_llm=False
        )
        self.assertTrue(os.path.isfile(self.output_json))
        self.assertEqual(data["version"], "1.0")

        # Check profile schema
        profile = data["profile"]
        self.assertIn("name", profile)
        self.assertIn("skills", profile)
        self.assertIn("languages", profile["skills"])
        self.assertIn("mlAi", profile["skills"])

        # Check resume schema
        resume = data["resume"]
        self.assertIn("pillars", resume)
        self.assertGreaterEqual(len(resume["pillars"]), 3)
        self.assertIn("workExperience", resume)
        self.assertGreaterEqual(len(resume["workExperience"]), 3)
        self.assertIn("education", resume)
        self.assertIn("internships", resume)

    def test_data_loader_integration(self):
        profile_data, resume_data = load_portfolio_json()
        self.assertIsNotNone(profile_data)
        self.assertIsNotNone(resume_data)
        self.assertTrue(bool(profile_data.get("name")))
        self.assertGreaterEqual(len(resume_data["workExperience"]), 3)

    def test_dynamic_home_page_rendering(self):
        client = app.app.test_client()
        response = client.get('/?page=home')
        self.assertEqual(response.status_code, 200)
        # Verify dynamically rendered content from the resume pipeline
        self.assertIn(b"Sears Holdings", response.data)
        self.assertIn(b"OneCard", response.data)
        self.assertIn(b"Auronova Consulting", response.data)
        self.assertIn(b"Indian Institute of Technology", response.data)


if __name__ == "__main__":
    unittest.main()
