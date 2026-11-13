#!/usr/bin/env python3
"""
content.py — Centralized content service for blogs, projects, and work case studies.

Provides a unified interface for loading, caching, querying, and scaffolding
blog articles, project case studies, and detailed work cases from Markdown files.
"""

import os
import sys
import re
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Set

# Ensure paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from markdown_pipeline import md_to_html, parse_front_matter, calculate_read_time, slugify  # noqa: E402

work_cases_data: List[Dict[str, Any]] = []

# Directory Resolution: unified content folder with work and projects subfolders
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONTENT_DIR = os.path.join(BASE_DIR, "content")
WORK_DIR = os.path.join(CONTENT_DIR, "work")
PROJECTS_DIR = os.path.join(CONTENT_DIR, "projects")
BLOGS_DIR = PROJECTS_DIR

# Internal in-memory caches and last-modified tracking
_BLOG_CACHE: Optional[List[Dict[str, Any]]] = None
_BLOG_CACHE_MTIME: float = 0.0

_WORK_CACHE: Optional[List[Dict[str, Any]]] = None
_WORK_CACHE_MTIME: float = 0.0

# Default media diagrams for key case studies
DEFAULT_BLOG_MEDIA = {
    "langgraph-agents": {
        "type": "image",
        "src": "/src/assets/agentic-ai-flow.svg",
        "alt": "LangGraph Multi-Agent Architecture with HITL"
    },
    "data-mesh-fintech": {
        "type": "image",
        "src": "/src/assets/data-mesh-arch.svg",
        "alt": "OneCard Decentralized Data Mesh Architecture"
    },
    "snowflake-dms-cdc": {
        "type": "image",
        "src": "/src/assets/snowflake-cdc-flow.svg",
        "alt": "AWS DMS CDC to Snowpipe Streaming Engine"
    },
    "churn-risk-modeling": {
        "type": "image",
        "src": "/src/assets/churn-model-pipeline.svg",
        "alt": "Predictive LightGBM Churn Classifier Pipeline"
    }
}


def _get_dir_mtime(directory: str) -> float:
    """Returns the max modification time of the directory and any markdown files inside."""
    if not os.path.exists(directory):
        return 0.0
    latest = os.path.getmtime(directory)
    try:
        for entry in os.scandir(directory):
            if entry.name.endswith(".md") and entry.is_file():
                latest = max(latest, entry.stat().st_mtime)
    except Exception:
        pass
    return latest


def _parse_blog_date(date_str: str) -> datetime:
    """Helper to convert date string (e.g. 'June 2026', 'May 2024 – Present', or '2026-06-01') to datetime."""
    if not date_str:
        return datetime.min
    clean = date_str.split("–")[0].split("-")[0].strip()
    for fmt in ("%B %Y", "%b %Y", "%Y-%m-%d", "%Y/%m/%d", "%Y"):
        try:
            return datetime.strptime(clean, fmt)
        except ValueError:
            continue
    return datetime.min


# ===========================================================================
# PROJECTS / BLOGS MARKDOWN LOADER
# ===========================================================================

def parse_single_blog(filepath: str) -> Dict[str, Any]:
    """Parses a single markdown file into a blog/project post data dictionary."""
    filename = os.path.basename(filepath)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    meta, body = parse_front_matter(content)
    base_slug = filename[:-3] if filename.endswith(".md") else filename
    clean_slug = re.sub(r'^\d+[-_]', '', base_slug)

    slug = meta.get("id") or slugify(clean_slug)
    meta["id"] = slug
    meta["type"] = "project"

    if not meta.get("title"):
        meta["title"] = clean_slug.replace("-", " ").title()

    if not meta.get("readTime"):
        meta["readTime"] = calculate_read_time(body)
    rt_match = re.search(r'(\d+)', meta["readTime"])
    meta["read_time_minutes"] = int(rt_match.group(1)) if rt_match else 5

    if not meta.get("topic"):
        meta["topic"] = meta.get("category") or "General"
    if not meta.get("category"):
        meta["category"] = meta.get("topic")

    if not meta.get("date"):
        meta["date"] = datetime.now().strftime("%B %Y")
    if not meta.get("period"):
        meta["period"] = meta.get("date")

    if not meta.get("company"):
        meta["company"] = meta.get("org") or "Open Source / Lab"
    if not meta.get("role"):
        meta["role"] = "Architecture & Deep Dive"
    if not meta.get("metrics"):
        meta["metrics"] = []

    dt = _parse_blog_date(meta.get("date", ""))
    meta["sort_timestamp"] = int(dt.timestamp()) if dt != datetime.min else 0
    meta["sort_date"] = dt.strftime("%Y-%m-%d") if dt != datetime.min else ""

    if not meta.get("summary"):
        clean_body = body.strip().replace("\n", " ")
        meta["summary"] = (clean_body[:120].strip() + "...") if len(clean_body) > 120 else clean_body

    if not meta.get("tags") or not isinstance(meta["tags"], list):
        meta["tags"] = []

    raw_rel = meta.get("related", [])
    if isinstance(raw_rel, str):
        raw_rel = [r.strip() for r in raw_rel.split(",") if r.strip()]
    meta["related"] = raw_rel if isinstance(raw_rel, list) else []

    # Extract order: from frontmatter or filename prefix (e.g. 01-slug.md)
    order_match = re.match(r'^(\d+)[-_]', filename)
    default_order = int(order_match.group(1)) if order_match else 999
    try:
        meta["order"] = int(meta.get("order", default_order))
    except (ValueError, TypeError):
        meta["order"] = default_order

    # Normalize media support (image, video, diagrams)
    raw_media = meta.get("media")
    if not raw_media and meta.get("image"):
        raw_media = {"type": "image", "src": meta["image"], "alt": meta.get("title", "")}
    elif not raw_media and meta.get("video"):
        raw_media = {"type": "video", "src": meta["video"], "poster": meta.get("poster", "")}
    elif isinstance(raw_media, str):
        if any(raw_media.lower().endswith(ext) for ext in ('.mp4', '.webm', '.ogg', '.mov')):
            raw_media = {"type": "video", "src": raw_media, "poster": meta.get("poster", "")}
        else:
            raw_media = {"type": "image", "src": raw_media, "alt": meta.get("title", "")}
    elif not raw_media and slug in DEFAULT_BLOG_MEDIA:
        raw_media = DEFAULT_BLOG_MEDIA[slug]

    meta["media"] = raw_media
    meta["content"] = md_to_html(body)
    return meta


def _resolve_projects_dir(explicit_dir: Optional[str] = None) -> str:
    """Finds the active projects directory (content/projects)."""
    if explicit_dir and os.path.exists(explicit_dir):
        return explicit_dir
    return PROJECTS_DIR


def load_blogs(directory: Optional[str] = None, force_reload: bool = False) -> List[Dict[str, Any]]:
    """
    Returns blog/project posts sorted newest first.
    Uses cached data when files haven't changed, but automatically invalidates
    and re-parses when any markdown file is added, modified, or removed.
    """
    global _BLOG_CACHE, _BLOG_CACHE_MTIME

    target_dir = _resolve_projects_dir(directory)
    current_mtime = _get_dir_mtime(target_dir)

    if not force_reload and _BLOG_CACHE is not None and current_mtime <= _BLOG_CACHE_MTIME:
        return _BLOG_CACHE

    if not os.path.exists(target_dir):
        _BLOG_CACHE = []
        _BLOG_CACHE_MTIME = current_mtime
        return _BLOG_CACHE

    posts = []
    for filename in os.listdir(target_dir):
        if not filename.endswith(".md"):
            continue
        filepath = os.path.join(target_dir, filename)
        try:
            post = parse_single_blog(filepath)
            posts.append(post)
        except Exception as e:
            print(f"Error parsing project '{filepath}': {e}", file=sys.stderr)

    posts.sort(key=lambda p: (p.get("order", 999), -_parse_blog_date(p.get("date", "")).toordinal()))
    _BLOG_CACHE = posts
    _BLOG_CACHE_MTIME = current_mtime

    # Cross-link if work cases already loaded or load work cases
    if _WORK_CACHE is not None:
        _ensure_linked()

    return _BLOG_CACHE


def get_blog_by_id(blog_id: str, directory: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Look up a specific blog post by its slug ID."""
    blogs = load_blogs(directory)
    return next((b for b in blogs if b.get("id") == blog_id), None)


def get_all_tags(blogs: Optional[List[Dict[str, Any]]] = None, directory: Optional[str] = None) -> List[str]:
    """Extracts a unique, sorted list of all tags present across blogs."""
    if blogs is None:
        blogs = load_blogs(directory)
    tags_set: Set[str] = set()
    for blog in blogs:
        for t in blog.get("tags", []):
            if t:
                tags_set.add(str(t).strip())
    return sorted(list(tags_set))


# ===========================================================================
# WORK CASE STUDIES MARKDOWN LOADER
# ===========================================================================

def parse_single_work_case(filepath: str) -> Dict[str, Any]:
    """Parses a single markdown file into a work case study data dictionary."""
    filename = os.path.basename(filepath)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    meta, body = parse_front_matter(content)
    base_slug = filename[:-3] if filename.endswith(".md") else filename
    clean_slug = re.sub(r'^\d+[-_]', '', base_slug)

    meta["id"] = meta.get("id") or clean_slug
    meta["type"] = "work"
    meta["title"] = meta.get("title") or clean_slug.replace("-", " ").title()
    meta["company"] = meta.get("company") or "Engineering Case Study"
    meta["role"] = meta.get("role") or ""
    meta["period"] = meta.get("period") or meta.get("date") or ""
    meta["location"] = meta.get("location") or ""
    meta["category"] = meta.get("category") or meta.get("topic") or "Engineering"
    meta["topic"] = meta["category"]
    meta["summary"] = meta.get("summary") or ""
    meta["metrics"] = meta.get("metrics") or []
    meta["techStack"] = meta.get("techStack") or meta.get("tags") or []
    meta["tags"] = meta["techStack"]

    if not meta.get("readTime"):
        meta["readTime"] = calculate_read_time(body)
    rt_match = re.search(r'(\d+)', meta["readTime"])
    meta["read_time_minutes"] = int(rt_match.group(1)) if rt_match else 5

    dt = _parse_blog_date(meta.get("period", ""))
    meta["sort_timestamp"] = int(dt.timestamp()) if dt != datetime.min else 0
    meta["sort_date"] = dt.strftime("%Y-%m-%d") if dt != datetime.min else ""

    raw_rel = meta.get("related", [])
    if isinstance(raw_rel, str):
        raw_rel = [r.strip() for r in raw_rel.split(",") if r.strip()]
    meta["related"] = raw_rel if isinstance(raw_rel, list) else []

    # Extract order: from frontmatter or filename prefix (e.g. 01-slug.md)
    order_match = re.match(r'^(\d+)[-_]', filename)
    default_order = int(order_match.group(1)) if order_match else 999
    try:
        meta["order"] = int(meta.get("order", default_order))
    except (ValueError, TypeError):
        meta["order"] = default_order

    try:
        meta["order"] = int(meta.get("order", 999))
    except (ValueError, TypeError):
        meta["order"] = 999

    # Normalize media support (image, video, diagrams)
    raw_media = meta.get("media")
    if not raw_media and meta.get("image"):
        raw_media = {"type": "image", "src": meta["image"], "alt": meta.get("title", "")}
    elif not raw_media and meta.get("video"):
        raw_media = {"type": "video", "src": meta["video"], "poster": meta.get("poster", "")}
    elif isinstance(raw_media, str):
        if any(raw_media.lower().endswith(ext) for ext in ('.mp4', '.webm', '.ogg', '.mov')):
            raw_media = {"type": "video", "src": raw_media, "poster": meta.get("poster", "")}
        else:
            raw_media = {"type": "image", "src": raw_media, "alt": meta.get("title", "")}

    meta["media"] = raw_media
    meta["content"] = md_to_html(body)
    return meta


def _resolve_work_dir(explicit_dir: Optional[str] = None) -> Optional[str]:
    """Finds the active work cases directory (content/work)."""
    if explicit_dir and os.path.exists(explicit_dir):
        return explicit_dir
    return WORK_DIR


def _link_relationships(work_cases: List[Dict[str, Any]], blogs: List[Dict[str, Any]]):
    """Resolves bidirectional links and attaches rich metadata summaries to related_items."""
    all_map = {}
    for w in work_cases:
        all_map[w["id"]] = w
    for b in blogs:
        all_map[b["id"]] = b

    # Bidirectional resolution
    for item_id, item in list(all_map.items()):
        for rel_id in list(item.get("related", [])):
            if rel_id in all_map:
                target = all_map[rel_id]
                target_rel = target.setdefault("related", [])
                if item_id not in target_rel:
                    target_rel.append(item_id)

    # Attach related_items list with summaries
    for item in all_map.values():
        related_summaries = []
        for rel_id in item.get("related", []):
            if rel_id in all_map:
                target = all_map[rel_id]
                related_summaries.append({
                    "id": rel_id,
                    "title": target.get("title", rel_id),
                    "type": target.get("type", "project"),
                    "category": target.get("category") or target.get("topic") or "",
                    "readTime": target.get("readTime", ""),
                    "company": target.get("company", "")
                })
        item["related_items"] = related_summaries


def _ensure_linked():
    """Ensure both caches are loaded and bidirectionally cross-linked."""
    global _WORK_CACHE, _BLOG_CACHE
    if _WORK_CACHE is not None and _BLOG_CACHE is not None:
        _link_relationships(_WORK_CACHE, _BLOG_CACHE)


def load_work_cases(directory: Optional[str] = None, force_reload: bool = False) -> List[Dict[str, Any]]:
    """
    Returns the list of deep-dive production work case studies.
    Loads dynamically from Markdown files in content/work/ (or fallback work_cases_data).
    Automatically invalidates cache whenever markdown files are added, modified, or removed.
    """
    global _WORK_CACHE, _WORK_CACHE_MTIME

    target_dir = _resolve_work_dir(directory)
    if not target_dir or not os.path.exists(target_dir):
        return list(work_cases_data)

    current_mtime = _get_dir_mtime(target_dir)
    if not force_reload and _WORK_CACHE is not None and current_mtime <= _WORK_CACHE_MTIME:
        return _WORK_CACHE

    cases = []
    for filename in os.listdir(target_dir):
        if not filename.endswith(".md"):
            continue
        filepath = os.path.join(target_dir, filename)
        try:
            case = parse_single_work_case(filepath)
            cases.append(case)
        except Exception as e:
            print(f"Error parsing work case '{filepath}': {e}", file=sys.stderr)

    if not cases and work_cases_data:
        return list(work_cases_data)

    # Sort by explicit order, then newest period/date
    cases.sort(key=lambda c: (c.get("order", 999), -_parse_blog_date(c.get("period", "")).toordinal()))
    _WORK_CACHE = cases
    _WORK_CACHE_MTIME = current_mtime

    # Cross-link if blogs already loaded or load blogs
    if _BLOG_CACHE is None:
        load_blogs()
    else:
        _ensure_linked()

    return _WORK_CACHE


def get_work_case_by_id(case_id: str, directory: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Finds a specific work case study by ID."""
    cases = load_work_cases(directory)
    for case in cases:
        if case.get("id") == case_id:
            return case
    return None


def get_all_work_orgs(cases: Optional[List[Dict[str, Any]]] = None) -> List[str]:
    """Unique sorted companies/organizations across work cases."""
    if cases is None:
        cases = load_work_cases()
    orgs = {c.get("company", "").strip() for c in cases if c.get("company")}
    return sorted(list(orgs))


def get_all_work_categories(cases: Optional[List[Dict[str, Any]]] = None) -> List[str]:
    """Unique sorted categories across work cases."""
    if cases is None:
        cases = load_work_cases()
    cats = {c.get("category", "").strip() for c in cases if c.get("category")}
    return sorted(list(cats))


def get_item_by_id(item_id: str) -> Optional[Dict[str, Any]]:
    """Look up any card (Work case study or Project article) across the entire portfolio."""
    case = get_work_case_by_id(item_id)
    if case:
        return case
    return get_blog_by_id(item_id)


def get_content_index() -> Dict[str, Any]:
    """Returns a unified searchable, sortable, and indexed graph across all content items."""
    work_cases = load_work_cases()
    blogs = load_blogs()
    all_items = work_cases + blogs

    return {
        "items_by_id": {item["id"]: item for item in all_items},
        "all_items": all_items,
        "work_cases": work_cases,
        "projects": blogs,
        "by_date_desc": sorted(all_items, key=lambda x: x.get("sort_timestamp", 0), reverse=True),
        "by_date_asc": sorted(all_items, key=lambda x: x.get("sort_timestamp", 0)),
        "by_read_time_asc": sorted(all_items, key=lambda x: x.get("read_time_minutes", 5)),
        "by_read_time_desc": sorted(all_items, key=lambda x: x.get("read_time_minutes", 5), reverse=True),
        "tags_index": {tag: [item["id"] for item in all_items if tag in (item.get("tags") or item.get("techStack") or [])] for tag in get_all_tags()},
        "related_graph": {item["id"]: [r["id"] for r in item.get("related_items", [])] for item in all_items}
    }


def invalidate_cache():
    """Explicitly clear both in-memory caches."""
    global _BLOG_CACHE, _BLOG_CACHE_MTIME, _WORK_CACHE, _WORK_CACHE_MTIME
    _BLOG_CACHE = None
    _BLOG_CACHE_MTIME = 0.0
    _WORK_CACHE = None
    _WORK_CACHE_MTIME = 0.0


# ===========================================================================
# CONTENT SCAFFOLDING HELPERS (CLI / RUNTIME)
# ===========================================================================

def create_work_case(
    title: str,
    company: str = "Company Name",
    role: str = "Lead Data Scientist",
    category: str = "Engineering",
    period: str = "2024 – Present",
    location: str = "Remote / Hybrid",
    directory: Optional[str] = None
) -> str:
    """Scaffolds a new work case study markdown file in content/work/."""
    target_dir = directory or WORK_DIR
    os.makedirs(target_dir, exist_ok=True)
    slug = slugify(title)

    # Count existing files to determine order
    existing_files = [f for f in os.listdir(target_dir) if f.endswith(".md")]
    order_num = len(existing_files) + 1
    filename = f"{order_num:02d}-{slug}.md"
    filepath = os.path.join(target_dir, filename)

    if os.path.exists(filepath):
        raise FileExistsError(f"File '{filepath}' already exists.")

    template = f"""---
id: {slug}
order: {order_num}
title: "{title}"
company: "{company}"
role: "{role}"
period: "{period}"
location: "{location}"
category: "{category}"
summary: "A crisp executive summary of the engineering challenge, architecture, and business outcome."
metrics:
  - "+25% Efficiency Lift"
  - "-40% Operational Costs"
  - "Zero Production Incidents"
techStack:
  - Python
  - SQL
  - Architecture
media:
  type: image
  src: /src/assets/agentic-ai-flow.svg
  alt: "{title} Architecture Diagram"
---

### Executive Summary

Provide a concise, high-level summary of the initiative, core business problem, and key technical deliverables.

### 1. Problem Statement & Architecture

Explain the legacy architecture, pain points, data volume constraints, and key architectural decisions.

### 2. Implementation & Key Algorithms

Detail the technical design, data structures, pipeline logic, or machine learning models.

```python
# Core pipeline or model logic
def execute_pipeline(dataframe):
    return dataframe
```

### 3. Business Impact & Measurable Results

Highlight concrete metrics, cost savings, latency improvements, and adoption numbers.
"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(template)

    invalidate_cache()
    return filepath


def create_blog_post(
    title: str,
    directory: Optional[str] = None,
    topic: str = "AI/ML",
    tags: Optional[List[str]] = None,
    summary: str = "A brief one-liner summary of this project / case study."
) -> str:
    """Scaffolds a new project / blog post draft markdown file in content/projects/."""
    target_dir = directory or _resolve_projects_dir()
    os.makedirs(target_dir, exist_ok=True)
    slug = slugify(title)

    # Count existing files to determine order
    existing_files = [f for f in os.listdir(target_dir) if f.endswith(".md")]
    order_num = len(existing_files) + 1
    filename = f"{order_num:02d}-{slug}.md"
    filepath = os.path.join(target_dir, filename)

    if os.path.exists(filepath):
        raise FileExistsError(f"File '{filepath}' already exists.")

    date_str = datetime.now().strftime("%B %Y")
    tags_formatted = "\n".join([f"  - {t}" for t in (tags or ["python", "data-science"])])

    template = f"""---
id: {slug}
order: {order_num}
title: "{title}"
summary: "{summary}"
topic: "{topic}"
tags:
{tags_formatted}
date: "{date_str}"
readTime: "5 min read"
media:
  type: image
  src: /src/assets/agentic-ai-flow.svg
  alt: "{title} Architecture Diagram"
---

Write your case study or technical deep dive here in standard Markdown.

### Problem Statement & Architecture

Explain the business or engineering challenge, design constraints, and high-level architecture.

### Implementation Details

Discuss core decisions, code structure, and algorithms.

```python
# Code snippets format cleanly
def pipeline_step(data):
    return data
```

### Business Impact & Results

Highlight measurable outcomes (e.g. latency reduction, cost savings, accuracy lift).
"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(template)

    invalidate_cache()
    return filepath

