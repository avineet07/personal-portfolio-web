#!/usr/bin/env python3
import os
import re
import sys
from datetime import datetime
from flask import Flask, request, render_template, send_from_directory, make_response

# Import personal profile data
# Add current directory and src directory to path to support both IDE resolution and runtime imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
from data.loader import load_portfolio_json
from data.profile import profile_data
from data.resume import resume_data
from content import (
    load_blogs,
    get_all_tags,
    get_blog_by_id,
    load_work_cases,
    get_work_case_by_id,
    get_item_by_id,
    get_content_index,
    get_all_work_orgs,
    get_all_work_categories,
    invalidate_cache
)

app = Flask(__name__)
app.jinja_env.auto_reload = True
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True
app.jinja_env.globals['set'] = set

@app.context_processor
def inject_global_content():
    profile_data, resume_data = load_portfolio_json()
    return {
        'all_work_cases': load_work_cases(),
        'all_blogs': load_blogs(),
        'content_index': get_content_index(),
        'title': resume_data.get('title', 'Portfolio & Engineering Case Studies'),
        'meta_description': resume_data.get('meta_description', 'Portfolio and case studies.'),
    }

# ==========================================
# SECURITY HEADERS (Fix #6)
# ==========================================
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

# ==========================================
# FLASK WEB ROUTING
# ==========================================

@app.route('/favicon.ico')
def favicon():
    """Serves the favicon with appropriate caching and mime-type."""
    if os.path.isfile('favicon.ico'):
        return send_from_directory('.', 'favicon.ico', mimetype='image/x-icon')
    asset_fallback = os.path.join('src', 'assets', 'favicon.ico')
    if os.path.isfile(asset_fallback):
        return send_from_directory(os.path.join('src', 'assets'), 'favicon.ico', mimetype='image/x-icon')
    return send_from_directory(os.path.join('src', 'assets'), 'favicon.svg', mimetype='image/svg+xml')

@app.route('/')
@app.route('/work')
@app.route('/work.html')
@app.route('/projects')
@app.route('/projects.html')
def index():
    profile_data, resume_data = load_portfolio_json()
    # Support both static path routing (/work, /projects) and legacy query parameters (?page=work)
    path = request.path.strip('/')
    if path.startswith('work'):
        state_view = 'work'
    elif path.startswith('projects'):
        state_view = 'projects'
    else:
        state_view = request.args.get('page', 'home')

    post_id = request.args.get('post', '').strip()

    if state_view == 'work':
        work_cases = load_work_cases()
        work_orgs = get_all_work_orgs()
        work_categories = get_all_work_categories()
        active_work = get_work_case_by_id(post_id) if post_id else None
        return render_template('work.html',
                               profile_data=profile_data, resume_data=resume_data,
                               state_view='work',
                               work_cases=work_cases,
                               work_orgs=work_orgs,
                               work_categories=work_categories,
                               active_work=active_work)
    elif state_view == 'projects':
        # Load blogs and tags on projects page; pass full data for client-side detail reader
        blogs = load_blogs()
        all_tags = get_all_tags(blogs)
        active_blog = get_blog_by_id(post_id) if post_id else None
        return render_template('projects.html',
                               profile_data=profile_data, resume_data=resume_data,
                               state_view='projects',
                               blogs=blogs,
                               all_tags=all_tags,
                               active_blog=active_blog)
    else:
        # Home is the executive summary & visual showcase
        featured_work = load_work_cases()[:3]
        featured_blogs = load_blogs()[:3]
        return render_template('home.html',
                               profile_data=profile_data, resume_data=resume_data,
                               state_view='home',
                               featured_work=featured_work,
                               featured_blogs=featured_blogs)

# Whitelist of allowed file extensions for serving (Fix #4)
_ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico'}

@app.route('/<path:filename>')
def serve_root_file(filename):
    """Serves static files located in the root directory (like PDFs and images)."""
    # URL-decode the filename to catch encoded traversal attempts (Fix #4)
    from urllib.parse import unquote
    decoded = unquote(unquote(filename))  # double-decode to catch double-encoding

    # Normalize path separators (catch backslash variants)
    normalized = decoded.replace('\\', '/')

    # Check for traversal in decoded/normalized path
    if '..' in normalized or normalized.startswith('/'):
        return "Access Denied", 403

    # Whitelist-only: only serve allowed file extensions (Fix #4)
    _, ext = os.path.splitext(normalized.lower())
    if ext not in _ALLOWED_EXTENSIONS:
        return "File Not Found", 404

    if os.path.isfile(filename):
        return send_from_directory('.', filename)
    asset_fallback = os.path.join('src', 'assets', filename)
    if os.path.isfile(asset_fallback):
        return send_from_directory(os.path.join('src', 'assets'), filename)
    return "File Not Found", 404

# ==========================================
# CACHE HEADERS FOR STATIC ASSETS (Fix #5)
# ==========================================
@app.route('/templates/<path:filename>')
def serve_template_assets(filename):
    """Serve template assets (css, js) with Cache-Control headers."""
    response = make_response(send_from_directory('templates', filename))
    _, ext = os.path.splitext(filename.lower())
    if ext in ('.css', '.js'):
        response.headers['Cache-Control'] = 'no-cache, must-revalidate'
    else:
        response.headers['Cache-Control'] = 'public, max-age=3600'
    return response

@app.route('/src/<path:filename>')
def serve_static_with_cache(filename):
    """Serve static assets with Cache-Control headers (Fix #5)."""
    # Check templates/ first if css or js was moved
    if filename.startswith(('css/', 'js/')):
        tmpl_file = os.path.join('templates', filename)
        if os.path.isfile(tmpl_file):
            return serve_template_assets(filename)

    response = make_response(send_from_directory('src', filename))
    _, ext = os.path.splitext(filename.lower())
    # Do not cache CSS and JS aggressively to ensure live code updates are visible immediately
    if ext in ('.css', '.js'):
        response.headers['Cache-Control'] = 'no-cache, must-revalidate'
    elif ext in ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.woff', '.woff2', '.ttf', '.ico'):
        response.headers['Cache-Control'] = 'public, max-age=3600'
    else:
        response.headers['Cache-Control'] = 'public, max-age=600'
    return response

if __name__ == '__main__':
    # Debug mode controlled by environment variable (Fix #7)
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() in ('true', '1', 'yes')
    app.run(host='127.0.0.1', port=5001, debug=debug)
