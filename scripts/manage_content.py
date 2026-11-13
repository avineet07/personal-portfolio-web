#!/usr/bin/env python3
"""
scripts/manage_content.py — Developer CLI for managing work case studies, project deep dives, and pipeline.

Usage:
  python scripts/manage_content.py list
  python scripts/manage_content.py new work "Title of Case Study"
  python scripts/manage_content.py new project "Title of Project"
  python scripts/manage_content.py pipeline
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from content import (
    load_blogs,
    create_blog_post,
    load_work_cases,
    create_work_case,
)
from pipeline import run_pipeline


def cmd_new(args: list):
    """CLI handler for creating new work case study or project draft."""
    if not args:
        print("❌ Error: Please specify a title. e.g. python scripts/manage_content.py new \"My Project\"")
        sys.exit(1)

    first = args[0].lower()
    if first in ("work", "case"):
        if len(args) < 2:
            print("❌ Error: Please specify a title for the work case study. e.g. python scripts/manage_content.py new work \"Agentic AI Architecture\"")
            sys.exit(1)
        title = " ".join(args[1:])
        creator, item_type, tab = create_work_case, "Work Case Study", "Work"
        hint = "Edit frontmatter (company, role, period, metrics) and write in standard Markdown."
    else:
        if first in ("project", "blog"):
            if len(args) < 2:
                print("❌ Error: Please specify a title for the project. e.g. python scripts/manage_content.py new project \"Data Mesh Architecture\"")
                sys.exit(1)
            title = " ".join(args[1:])
        else:
            title = " ".join(args)
        creator, item_type, tab = create_blog_post, "Project", "Projects"
        hint = "Write your content in Markdown."

    try:
        filepath = creator(title)
        print(f"🎉 Created new {item_type} draft: '{filepath}'")
        print(f"💡 {hint} It will immediately appear on the website under '{tab}'!")
    except FileExistsError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def cmd_list():
    """CLI handler for listing all existing work cases and project articles."""
    work_cases = load_work_cases(force_reload=True)
    blogs = load_blogs(force_reload=True)

    print("\n" + "=" * 75)
    print(f"📁 WORK CASE STUDIES ({len(work_cases)}) [content/work/*.md]")
    print("=" * 75)
    if not work_cases:
        print("No work case studies found.")
    else:
        for i, c in enumerate(work_cases, 1):
            metrics = " | ".join(c.get("metrics", [])[:2])
            print(f"{i}. [{c.get('company', 'No Company')}] {c.get('title')}")
            print(f"   Role: {c.get('role')} | Period: {c.get('period')} | Category: {c.get('category')}")
            if metrics:
                print(f"   Metrics: {metrics}")
            print()

    print("=" * 75)
    print(f"📁 PROJECT ARTICLES / DEEP DIVES ({len(blogs)}) [content/projects/*.md]")
    print("=" * 75)
    if not blogs:
        print("No project articles found.")
    else:
        for i, b in enumerate(blogs, 1):
            tags = ", ".join(b.get("tags", []))
            print(f"{i}. [{b.get('date', 'No date')}] {b.get('title')}")
            print(f"   ID: {b.get('id')} | Topic: {b.get('topic')} | Read Time: {b.get('readTime')}")
            if tags:
                print(f"   Tags: #{tags}")
            print()
    print("=" * 75 + "\n")


def cmd_pipeline(args: list):
    """CLI handler for running automated resume & cover letter pipeline."""
    resume_path = None
    scaffold = "--scaffold" in args or "-s" in args
    use_llm = "--llm" in args or "--use-llm" in args
    historical = "--historical" in args or "-h" in args

    for arg in args:
        if not arg.startswith("-"):
            resume_path = arg
            break

    run_pipeline(
        resume_path=resume_path,
        use_llm=use_llm,
        auto_scaffold_articles=scaffold,
        use_historical=historical,
    )


def print_help():
    print("""
Portfolio Content Manager CLI
=============================
Usage:
  python scripts/manage_content.py list
    Displays all current Work case studies and Project articles

  python scripts/manage_content.py pipeline [path/to/resume.pdf] [--scaffold]
    Extracts resume PDF, synthesizes content, and updates src/data/portfolio_data.json

  python scripts/manage_content.py new work "Title of Case Study"
    Creates a new template Markdown draft in content/work/

  python scripts/manage_content.py new project "Title of Project"
    Creates a new template Markdown draft in content/projects/
""")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == "new":
        cmd_new(sys.argv[2:])
    elif cmd == "list":
        cmd_list()
    elif cmd in ("pipeline", "generate", "resume"):
        cmd_pipeline(sys.argv[2:])
    else:
        print(f"❌ Error: Unknown command '{cmd}'")
        print_help()
        sys.exit(1)

