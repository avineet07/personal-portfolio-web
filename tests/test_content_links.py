"""
test_content_links.py — Cross-link integrity between Work cases and Project articles.

Related articles are declared in each Markdown file's `related:` frontmatter. This
module verifies that removing a linked article never leaves a dangling reference in
the reader's related-cards list.
"""

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from content import _link_relationships


class TestRelatedArticleLinks(unittest.TestCase):
    """Removing a linked article must not break its neighbours."""

    def test_removed_article_is_dropped_from_related_items(self):
        """An article referenced by `related:` but no longer loaded is skipped."""
        work = [
            {"id": "w1", "title": "Work One", "related": ["b1", "b2"]},
            {"id": "w2", "title": "Work Two", "related": ["b1"]},
        ]
        blogs = [{"id": "b2", "title": "Blog Two", "related": []}]

        _link_relationships(work, blogs)

        ids = {w["id"] for w in work} | {b["id"] for b in blogs}
        dangling = [(i["id"], r["id"]) for i in work + blogs
                    for r in i.get("related_items", []) if r["id"] not in ids]
        self.assertEqual(dangling, [], "removed article left a dangling related ref")
        self.assertEqual([r["id"] for r in work[0]["related_items"]], ["b2"])
        self.assertEqual([r["id"] for r in work[1]["related_items"]], [])

    def test_bidirectional_link_is_resolved(self):
        """If A links to B, B also lists A as a connected study."""
        work = [{"id": "w1", "title": "Work One", "related": ["b1"]}]
        blogs = [{"id": "b1", "title": "Blog One", "related": ["w1"]}]

        _link_relationships(work, blogs)
        self.assertEqual([r["id"] for r in blogs[0]["related_items"]], ["w1"])
        self.assertEqual([r["id"] for r in work[0]["related_items"]], ["b1"])

    def test_missing_related_id_is_never_rendered(self):
        """A related id that exists in neither set is silently ignored."""
        work = [{"id": "w1", "title": "Work One", "related": ["nope"]}]
        blogs = []

        _link_relationships(work, blogs)
        self.assertEqual(work[0]["related_items"], [])


if __name__ == "__main__":
    unittest.main()
