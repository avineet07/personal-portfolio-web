"""
test_markdown_pipeline.py — Test Markdown to HTML conversion and sanitization.
"""

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from markdown_pipeline import md_to_html, slugify, parse_front_matter


class TestMarkdownPipeline(unittest.TestCase):
    def test_headings_conversion(self):
        """Verify all heading levels # through ###### convert to h1-h6."""
        md = (
            "# Heading 1\n\n"
            "## Heading 2\n\n"
            "### Heading 3\n\n"
            "#### Heading 4\n\n"
            "##### Heading 5\n\n"
            "###### Heading 6\n"
        )
        html = md_to_html(md)
        self.assertIn("<h1>Heading 1</h1>", html)
        self.assertIn("<h2>Heading 2</h2>", html)
        self.assertIn("<h3>Heading 3</h3>", html)
        self.assertIn("<h4>Heading 4</h4>", html)
        self.assertIn("<h5>Heading 5</h5>", html)
        self.assertIn("<h6>Heading 6</h6>", html)

    def test_heading_without_empty_line_before_text(self):
        """Heading followed immediately by paragraph text without blank line."""
        md = "#### Domain Taxonomy Explained\nThere might be multiple website names."
        html = md_to_html(md)
        self.assertIn("<h4>Domain Taxonomy Explained</h4>", html)
        self.assertIn("<p>There might be multiple website names.</p>", html)
        self.assertNotIn("####", html)

    def test_horizontal_rule_conversion(self):
        """Dashes '---' and '***' convert to <hr>."""
        md = "Section A\n\n---\n\nSection B\n\n***\n\nSection C"
        html = md_to_html(md)
        self.assertTrue("<hr>" in html or "<hr />" in html)
        self.assertNotIn("<p>---</p>", html)
        self.assertNotIn("<p>***</p>", html)

    def test_table_conversion(self):
        """GFM pipe tables convert to <table><thead>...<tbody>...</table>."""
        md = (
            "| Phase | Change | Why |\n"
            "|---|---|---|\n"
            "| **V1** | Initial app | MVP |\n"
            "| **V2** | Markdown pipeline | Modular |\n"
        )
        html = md_to_html(md)
        self.assertIn("<table class=\"markdown-table\">", html)
        self.assertIn("<th>Phase</th>", html)
        self.assertIn("<strong>V1</strong>", html)
        self.assertIn("<td>Modular</td>", html)

    def test_table_with_empty_cells_and_breaks(self):
        """Tables with blank first cells, <br> tags, and multiple rows stay in one table."""
        md = (
            "Intro paragraph:\n"
            "| Team | Role | Responsibilities |\n"
            "| :--- | :--- | :--- |\n"
            "| **Core** | **Dev** | Backend APIs<br>- Tests |\n"
            "| | **Data** | Pipelines<br>- Audits |\n"
            "| **Ops** | **SRE** | Deployments |\n"
            "Outro paragraph."
        )
        html = md_to_html(md)
        self.assertEqual(html.count("<table class=\"markdown-table\">"), 1)
        self.assertIn("<td>Backend APIs<br>- Tests</td>", html)
        self.assertIn("<td>Pipelines<br>- Audits</td>", html)
        self.assertIn("<td>Deployments</td>", html)

    def test_inline_code_preserves_special_characters(self):
        """Asterisks inside inline code spans are not corrupted into italics."""
        md = "Use `*.<DOMAIN>.com` pattern for wildcard routing."
        html = md_to_html(md)
        self.assertIn("<code>*.&lt;DOMAIN&gt;.com</code>", html)
        self.assertNotIn("<em>", html)

    def test_markdown_links(self):
        """[text](url) converts to secure <a href=...> tags."""
        md = "Visit [Example](https://example.com) for details."
        html = md_to_html(md)
        self.assertIn('<a href="https://example.com" target="_blank" rel="noopener noreferrer">Example</a>', html)

    def test_code_blocks_with_comments_not_treated_as_headings(self):
        """Lines starting with '#' inside code blocks must remain code."""
        md = (
            "```bash\n"
            "# Configure proxy daemon\n"
            "sudo systemctl restart tinyproxy\n"
            "```"
        )
        html = md_to_html(md)
        self.assertIn("# Configure proxy daemon", html)
        self.assertNotIn("<h1>", html)


if __name__ == "__main__":
    unittest.main()
