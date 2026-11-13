import unittest
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

import app
from content import (
    load_blogs,
    get_all_tags,
    get_blog_by_id,
    load_work_cases,
    get_work_case_by_id,
    get_content_index,
    get_item_by_id,
)


class TestPortfolioApp(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()

    def test_favicon_status_200(self):
        response = self.client.get('/favicon.ico')
        self.assertEqual(response.status_code, 200)
        self.assertIn(response.mimetype, ['image/x-icon', 'image/vnd.microsoft.icon', 'image/svg+xml'])

    def test_home_page_status_200(self):
        response = self.client.get('/?page=home')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Ashish Vineet", response.data)
        # Verify visual cards rendered
        self.assertIn(b"Core Architectural Pillars", response.data)
        self.assertIn(b"Featured Work", response.data)
        self.assertIn(b"home-hero", response.data)

    def test_work_page_status_200(self):
        response = self.client.get('/?page=work')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Production Work", response.data)
        self.assertIn(b"Engineering Case Studies", response.data)
        self.assertIn(b"Sears Holdings", response.data)
        self.assertIn(b"OneCard", response.data)
        self.assertIn(b"work-card", response.data)

    def test_projects_page_status_200(self):
        response = self.client.get('/?page=projects')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Personal Projects", response.data)
        self.assertIn(b"#aws", response.data)
        self.assertIn(b"card-media-wrapper", response.data)

    def test_project_detail_view(self):
        response = self.client.get('/?page=projects&post=aws-smart-proxy')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Reverse Proxy", response.data)
        self.assertIn(b"server-fullscreen-btn", response.data)
        self.assertIn(b"Fullscreen", response.data)

    def test_content_loader_and_media(self):
        blogs = load_blogs()
        self.assertGreaterEqual(len(blogs), 2)
        tags = get_all_tags(blogs)
        self.assertIn("aws", tags)
        post = get_blog_by_id("aws-smart-proxy")
        self.assertIsNotNone(post)
        self.assertEqual(post["id"], "aws-smart-proxy")
        self.assertIsNotNone(post.get("media"))
        self.assertEqual(post["media"]["type"], "image")

    def test_work_cases_loader(self):
        work_cases = load_work_cases()
        self.assertGreaterEqual(len(work_cases), 4)
        case = get_work_case_by_id("sears-agentic-workflow")
        self.assertIsNotNone(case)
        self.assertEqual(case["company"], "Sears Holdings")
        self.assertIn("metrics", case)
        self.assertIn("media", case)
        auronova_case = get_work_case_by_id("auronova-risk-analytics")
        self.assertIsNotNone(auronova_case)
        self.assertEqual(auronova_case["company"], "Auronova Consulting")

    def test_dynamic_content_lifecycle(self):
        import time
        from content import WORK_DIR, PROJECTS_DIR

        # Test Work dynamic add and delete
        temp_work = os.path.join(WORK_DIR, "99-test-dynamic-case.md")
        with open(temp_work, "w", encoding="utf-8") as f:
            f.write("---\nid: test-dynamic-case\ncompany: Test Corp\nrole: Lead\n---\nBody")
        time.sleep(0.02)
        self.assertIsNotNone(get_work_case_by_id("test-dynamic-case"))
        os.remove(temp_work)
        time.sleep(0.02)
        self.assertIsNone(get_work_case_by_id("test-dynamic-case"))

        # Test Project dynamic add and delete
        temp_proj = os.path.join(PROJECTS_DIR, "test-dynamic-proj.md")
        with open(temp_proj, "w", encoding="utf-8") as f:
            f.write("---\nid: test-dynamic-proj\ntitle: Test Proj\n---\nBody")
        time.sleep(0.02)
        self.assertIsNotNone(get_blog_by_id("test-dynamic-proj"))
        os.remove(temp_proj)
        time.sleep(0.02)
        self.assertIsNone(get_blog_by_id("test-dynamic-proj"))

    def test_content_indexing_and_cross_linking(self):
        index = get_content_index()
        self.assertIn("items_by_id", index)
        self.assertIn("by_date_desc", index)
        self.assertIn("by_read_time_asc", index)
        self.assertIn("related_graph", index)

        # Check cross-linking on Sears agentic workflow
        case = get_item_by_id("sears-agentic-workflow")
        self.assertIsNotNone(case)
        self.assertIn("related_items", case)
        rel_ids = [r["id"] for r in case["related_items"]]
        self.assertIn("portfolio-evolution", rel_ids)

        # Verify sorting variables
        self.assertIn("sort_timestamp", case)
        self.assertIn("read_time_minutes", case)

        # Verify web page rendering of sort and related chips
        res_work = self.client.get('/?page=work')
        self.assertIn(b"sort-select", res_work.data)
        self.assertIn(b"card-related-chip", res_work.data)

        res_proj = self.client.get('/?page=projects')
        self.assertIn(b"sort-select", res_proj.data)
        self.assertIn(b"card-related-chip", res_proj.data)

    def test_template_static_assets(self):
        css_res = self.client.get('/templates/css/styles.css')
        self.assertEqual(css_res.status_code, 200)
        self.assertIn(b"plus jakarta sans", css_res.data.lower())

        js_res = self.client.get('/templates/js/detail-reader.js')
        self.assertEqual(js_res.status_code, 200)
        self.assertIn(b"DetailReader", js_res.data)


if __name__ == "__main__":
    unittest.main()
