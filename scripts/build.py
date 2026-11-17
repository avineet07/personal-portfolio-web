#!/usr/bin/env python3
"""Build the static site into dist/.

This is the production build step for deploying to Cloudflare Pages.
It renders each page template with pre-computed data (so nothing is
rendered per-request at runtime) and copies static assets into dist/.

Usage:
    python scripts/build.py

Output:
    dist/index.html          home page
    dist/work.html           work page
    dist/projects.html       projects page (with blog reader)
    dist/                    static assets (css, js, assets, blogs/)
"""

import os
import sys
import shutil
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from flask import Flask, render_template  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / 'dist'
ASSETS = ROOT / 'src' / 'assets'

app = Flask(__name__)
app.root_path = ROOT
app.template_folder = 'templates'

from content import (  # noqa: E402
    load_blogs,
    load_work_cases,
    get_all_tags,
    get_all_work_orgs,
    get_all_work_categories,
    get_content_index,
)
from data.loader import load_portfolio_json  # noqa: E402

@app.context_processor
def inject_global_content():
    _, resume_data = load_portfolio_json()
    return {
        'all_work_cases': load_work_cases(),
        'all_blogs': load_blogs(),
        'content_index': get_content_index(),
        'title': resume_data.get('title', 'Portfolio & Engineering Case Studies'),
        'meta_description': resume_data.get('meta_description', 'Portfolio and case studies.'),
    }

def get_pages(profile_data, resume_data):
    return [
        ('index', 'home', {
            'profile_data': profile_data,
            'resume_data': resume_data,
            'state_view': 'home',
            'featured_work': load_work_cases()[:3],
            'featured_blogs': load_blogs()[:3],
        }),
        ('work', 'work', {
            'profile_data': profile_data,
            'resume_data': resume_data,
            'state_view': 'work',
            'work_cases': load_work_cases(),
            'work_orgs': get_all_work_orgs(),
            'work_categories': get_all_work_categories(),
        }),
        ('projects', 'projects', {
            'profile_data': profile_data,
            'resume_data': resume_data,
            'state_view': 'projects',
            'blogs': load_blogs(),
            'all_tags': get_all_tags(load_blogs()),
        }),
    ]


def build_detail_pages(profile_data, resume_data):
    """Pre-render each blog/work detail page."""
    blogs = load_blogs()
    work_cases = load_work_cases()
    pages = get_pages(profile_data, resume_data)

    for blog in blogs:
        slug = blog.get('id') or blog.get('slug')
        if not slug:
            continue
        context = dict(pages[2][2], active_blog=blog)
        rendered = render_template('projects.html', **context)
        (DIST / f'projects-{slug}.html').write_text(rendered, encoding='utf-8')
        print(f'  built projects-{slug}.html')

    for case in work_cases:
        slug = case.get('id') or case.get('slug')
        if not slug:
            continue
        context = dict(pages[1][2], active_work=case)
        rendered = render_template('work.html', **context)
        (DIST / f'work-{slug}.html').write_text(rendered, encoding='utf-8')
        print(f'  built work-{slug}.html')


def _copy_without_pycache(src: Path, dest: Path) -> None:
    """Copy a directory tree, skipping __pycache__ (compiled .pyc files)."""
    dest.mkdir(parents=True, exist_ok=True)
    for path in src.rglob('*'):
        if path.is_symlink():
            continue
        # Skip anything inside a __pycache__ directory.
        if path.name == '__pycache__' or path.parent.name == '__pycache__':
            continue
        rel = path.relative_to(src)
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if path.is_dir():
            _copy_without_pycache(path, target)
        else:
            shutil.copy2(path, target)


def build():
    """Render all pages and copy assets into dist/."""
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    profile_data, resume_data = load_portfolio_json()
    pages = get_pages(profile_data, resume_data)

    with app.app_context():
        for name, template, context in pages:
            rendered = render_template(
                f'{template}.html',
                **context,
            )
            (DIST / f'{name}.html').write_text(rendered, encoding='utf-8')
            print(f'  built {name}.html')
            # Also create folder/index.html for /work and /projects directory URLs
            if name != 'index':
                dir_target = DIST / name
                dir_target.mkdir(parents=True, exist_ok=True)
                (dir_target / 'index.html').write_text(rendered, encoding='utf-8')
        build_detail_pages(profile_data, resume_data)

    # Copy static assets (CSS, JS, SVG diagrams, PDFs) and content.
    templates_dir = ROOT / 'templates'
    for sub in ('css', 'js'):
        src_sub = templates_dir / sub
        if src_sub.exists():
            shutil.copytree(src_sub, DIST / 'templates' / sub, dirs_exist_ok=True)
            # Also mirror under dist/src/ for compatibility
            shutil.copytree(src_sub, DIST / 'src' / sub, dirs_exist_ok=True)
            print(f'  copied templates/{sub}')

    # Synchronize latest resume from ref/resume/ into src/assets/
    ref_resume_dir = ROOT / 'ref' / 'resume'
    if ref_resume_dir.is_dir():
        pdfs = sorted(ref_resume_dir.glob('*.pdf'), key=lambda p: p.stat().st_mtime, reverse=True)
        if pdfs:
            latest_pdf = pdfs[0]
            shutil.copy2(latest_pdf, ASSETS / 'resume.pdf')
            shutil.copy2(latest_pdf, ASSETS / latest_pdf.name)
            print(f'  synchronized resume: {latest_pdf.name} -> src/assets/resume.pdf')

    src_dir = ROOT / 'src'
    if src_dir.exists():
        _copy_without_pycache(src_dir, DIST / 'src')
        print('  copied src/')

    # Mirror src/assets directly to dist/assets and dist/resume.pdf for URL routing compatibility
    if ASSETS.exists():
        shutil.copytree(ASSETS, DIST / 'assets', dirs_exist_ok=True)
        print('  copied assets/ -> dist/assets/')
        if (ASSETS / 'resume.pdf').exists():
            shutil.copy2(ASSETS / 'resume.pdf', DIST / 'resume.pdf')
            print('  copied resume.pdf -> dist/resume.pdf')

    if (ROOT / 'content').exists():
        shutil.copytree(ROOT / 'content', DIST / 'content', dirs_exist_ok=True)
        print('  copied content/')
    if (ROOT / 'favicon.ico').exists():
        shutil.copy2(ROOT / 'favicon.ico', DIST / 'favicon.ico')
        print('  copied favicon.ico')

    print(f'\nBuild complete: {DIST}')
    return len(pages)


if __name__ == '__main__':
    build()
