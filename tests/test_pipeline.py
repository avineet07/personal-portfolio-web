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


class TestResumePipeline(unittest.TestCase):
    def setUp(self):
        self.resume_dir = RESUME_DIR
        self.cover_letter_dir = COVER_LETTER_DIR
        self.output_json = os.path.join(PROJECT_ROOT, "src", "data", "test_portfolio_output.json")

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
        self.assertEqual(historical["profile"]["name"], "Ashish Vineet")
        self.assertGreaterEqual(len(historical["resume"]["workExperience"]), 3)

    def test_document_extraction(self):
        resume_doc = extract_resume_document(str(self.resume_dir))
        self.assertIsNotNone(resume_doc, "Must extract resume document from ref/resume")
        self.assertIn("ASHISH VINEET", resume_doc["full_text"].upper())

        cover_doc = extract_cover_letter_document(str(self.cover_letter_dir))
        self.assertIsNotNone(cover_doc, "Must extract cover letter document from ref/cover_letter")
        self.assertIn("DEAR SIR/MADAM", cover_doc["full_text"].upper())

    def test_hierarchical_section_splitter(self):
        resume_doc = extract_resume_document(str(self.resume_dir))
        self.assertIsNotNone(resume_doc)
        sections = split_resume_into_sections(resume_doc["full_text"])

        # Check section boundary extraction
        self.assertIn("ASHISH VINEET", sections["header"].upper())
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
        self.assertEqual(profile_data["name"], "Ashish Vineet")
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
