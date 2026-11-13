# Personal Portfolio & Data Science Showcase (Python Flask SSR)

Welcome to the source code repository for **Ashish Vineet's** personal portfolio and engineering case study website. This project is built using a modern, minimalist **Python Flask** stack with server-side rendering (SSR) via **Jinja2** templates, paired with vanilla CSS and lightweight JavaScript primitives. It completely eliminates client-side framework bloat while providing an app-like reader experience.

The application has **zero heavy framework dependencies**, loads instantaneously, is optimized for SEO and accessibility, and features an interactive modal reader with bidirectional card linking, history navigation, and instant client-side sorting.

---

## 📂 Project Directory Structure

```text
personal-website-portfolio/
├── .env.example               # Cloudflare & deployment configuration template
├── .github/
│   └── workflows/
│       └── deploy.yml         # GitHub Actions CI/CD to Cloudflare Pages & R2
├── .gitignore                 # Ignores .venv, ref/, dist/, .env, and build artifacts
├── AGENTS.md                  # Working principles and AI agent instructions
├── README.md                  # Project overview, architecture, and developer guide
├── app.py                     # Main Flask routing engine, security headers, and static server
├── content/                   # Modular markdown content source
│   ├── projects/              # Technical deep dives and personal projects (.md)
│   │   ├── churn-risk-modeling.md
│   │   ├── data-mesh-fintech.md
│   │   ├── langgraph-agents.md
│   │   └── snowflake-dms-cdc.md
│   └── work/                  # Production engineering case studies (.md)
│       ├── 01-sears-agentic-workflow.md
│       ├── 02-onecard-data-mesh.md
│       ├── 03-onecard-churn-engine.md
│       ├── 04-sears-cdc-snowflake.md
│       └── 05-auronova-risk-analytics.md
├── manage_blogs.py            # Content developer CLI (scaffold, list, and compile)
├── pyproject.toml             # Project dependencies and packaging (uv)
├── ref/                       # Grounding reference documents (CV, Cover Letter; gitignored)
├── requirements.txt           # Pip-compatible dependency export
├── scripts/
│   ├── build.py               # Static site generator (pre-renders HTML to dist/)
│   └── deploy.sh              # Production deployment script (Cloudflare Pages + R2 sync)
├── src/
│   ├── assets/                # SVGs, diagrams, and PDF assets (CV, Cover Letter)
│   │   ├── agentic-ai-flow.svg
│   │   ├── churn-model-pipeline.svg
│   │   ├── data-mesh-arch.svg
│   │   ├── snowflake-cdc-flow.svg
│   │   ├── Ashish_Vineet_Cover_Letter.pdf
│   │   └── CV_AshishVineet.pdf
│   ├── content.py             # Content pipeline: dynamic parser, caching, indexing, cross-linking
│   ├── css/
│   │   └── styles.css         # Design tokens, unified card styles, reader modal, themes
│   ├── data/                  # Static metadata and legacy fallbacks
│   │   ├── experience.py      # Biography, milestones, skills matrix
│   │   ├── projects/          # Fallback project definitions
│   │   └── work/              # Fallback work case definitions
│   ├── js/
│   │   └── detail-reader.js   # Interactive modal reader, zoom, fullscreen, history stack, delegation
│   └── markdown_pipeline.py   # Custom Markdown-to-HTML parser with alerts, code blocks, media
├── templates/                 # Jinja2 HTML layout templates
│   ├── base.html              # Shell layout, navbar, reader modal container, scripts
│   ├── components/            # Reusable UI component macros
│   │   └── content_card.html  # Unified content card component for Work, Projects & Home
│   ├── home.html              # Executive summary, core pillars, milestones, skills
│   ├── projects.html          # Projects view with tag filtering & instant sorting
│   └── work.html              # Work case studies view with org/domain filters & instant sorting
├── tests/
│   └── test_app.py            # Unit test suite (routing, loaders, indexing, cross-linking)
└── uv.lock                    # Cryptographic dependency lockfile
```

---

## 🚀 Getting Started

### 1. Setup & Installation
Ensure you have Python 3.12+ and the `uv` package manager installed. Navigate to the project root and synchronize the virtual environment:
```bash
# Automatically creates .venv and installs locked dependencies
uv sync
```
*(Alternatively, use `pip install -r requirements.txt`)*

### 2. Run Locally
Launch the development server:
```bash
uv run app.py
# or: python3 app.py
```
Open your browser and navigate to:
👉 **[http://localhost:5000](http://localhost:5000)**

Flask's auto-reloading is enabled: changes to templates, stylesheets, or Markdown files update live on browser refresh with zero rebuild steps required.

### 3. Run Tests
Execute the unit test suite:
```bash
python3 -m unittest discover tests
```

---

## ✍️ Content Architecture & Cadence

Content is separated cleanly into independent Markdown files under `content/`. Adding or deleting any `.md` file updates the website immediately without changing application code.

### Where Content Lives

| Section | Location | Format & Purpose |
| --- | --- | --- |
| **Work Case Studies** | `content/work/*.md` | Production engineering deep dives (company, role, period, business metrics, architecture) |
| **Project Deep Dives** | `content/projects/*.md` | Technical explorations, experiments, and architectures (Agentic AI, Data Mesh, ML) |
| **Templates & Presentation** | `templates/` | Jinja2 templates, stylesheets (`templates/css/styles.css`), and reader (`templates/js/detail-reader.js`) |
| **Structured Portfolio Data** | `src/data/portfolio_data.json` | Compiled static identity, pillars, experience, and education |
| **Media & Diagrams** | `src/assets/` | Architecture SVG diagrams, screenshots, video assets, and resume/cover letter PDFs |
| **Grounding Reference** | `ref/resume/` & `ref/cover_letter/` | Private grounding documents (CV and Cover Letter PDFs; ignored by git) |
| **Parsing Pipeline** | `src/pipeline/` | Automated PDF extraction, section generators, and grounding rules (`PARSING_GROUNDING_RULES.md`) |

---

## 🛠️ Developer & Content CLI (`scripts/`)

All operations, content scaffolding, and pipeline tools are unified under `scripts/`:

```bash
# Extract resume & cover letter from ref/ and compile into static JSON portfolio data
python scripts/run_pipeline.py

# Content management: list, scaffold, and review
python scripts/manage_content.py list

# Create a new production work case study (content/work/...)
python scripts/manage_content.py new work "High-Throughput Streaming Engine"

# Create a new technical project / blog draft (content/projects/...)
python scripts/manage_content.py new project "Autonomous Multi-Agent Evaluation"

# Run static site pre-renderer for Cloudflare Pages (dist/)
python scripts/build.py
```

*(Convenience root proxies `python run_pipeline.py` and `python manage_blogs.py` remain available for quick terminal access).*

---

## 🔗 Bidirectional Cross-Linking & Indexing

Content items can link to one another to guide readers through related systems and projects of larger or smaller scope.

### 1. Defining Relationships
Add related slug IDs to the YAML frontmatter in any Markdown file:

```yaml
---
id: sears-agentic-workflow
title: "Enterprise Agentic Workflow Automation & HITL Infrastructure"
company: "Sears Holdings"
role: "Senior Technical Associate"
period: "May 2024 – Oct 2026"
category: "Agentic AI & LLMs"
summary: "Production cyclic agent graphs built with LangGraph..."
metrics:
  - "45% reduction in manual triage time"
  - "Zero regressions in automated billing escalation"
techStack:
  - langgraph
  - azure-openai
  - python
related:
  - langgraph-agents        # Links to content/projects/langgraph-agents.md
  - sears-cdc-snowflake     # Links to content/work/04-sears-cdc-snowflake.md
---
```

### 2. Automatic Bidirectional Graph Resolution
The content engine in `src/content.py`:
- Parses frontmatter `related:` lists.
- Runs `_link_relationships()` to establish **bidirectional links** (if A links to B, B automatically links back to A).
- Populates `related_items` with rich metadata (title, type, category, read time, company).

### 3. Unified Content Cards (`content_card.html`)
Both Work and Projects views utilize the exact same macro:
```jinja2
{% from "components/content_card.html" import render_content_card %}

{% for case in work_cases %}
  {{ render_content_card(case, loop.index0) }}
{% endfor %}
```
Features:
- **Connected Pill Bar (`.card-connected-box`)**: Compact pills (`.connected-pill`) with badges (`💼 Work` / `🚀 Project`), truncated titles, and hover transition arrows.
- **Instant Client-Side Sorting**: Sort dropdown in sidebar (Newest First, Oldest First, Shortest Read, Longest Read, Title A–Z, Default Order). Moves existing DOM nodes instantly with 0ms latency.
- **Global Event Delegation**: `DetailReader.initGlobalCardDelegation()` in `src/js/detail-reader.js` ensures cards, open buttons, and connected pills remain clickable even after sorting or filtering.

### 4. Interactive Detail Reader Modal (`detail-reader.js`)
When opening any case study or project:
- **Connected Studies Grid (`.dr-related-grid`)**: Clean 2/3-column card grid at the bottom of the article. Clicking any connected card jumps directly to it.
- **History Back Navigation (`← Back`)**: Clicking the toolbar Back button or pressing <kbd>Backspace</kbd> / <kbd>Alt</kbd>+<kbd>←</kbd> navigates back through the history stack.
- **Zoom Controls**: Zoom in (`+`), zoom out (`-`), and reset (`0`) with scale transformation.
- **Fullscreen Mode**: Toggle fullscreen window reader with the toolbar button or <kbd>F</kbd> key.
- **Window Resizing**: Drag-handle at the bottom-right corner to freely resize the modal.
- **Keyboard Shortcuts**: <kbd>Esc</kbd> closes modal, tab-trapping preserves accessibility.

---

## ⚡ Central Indexing Engine (`src/content.py`)

`get_content_index()` provides a central in-memory index across all content items:
- `items_by_id`: Hash map for `O(1)` ID lookup.
- `all_items`: Unified array of work cases and project articles.
- `by_date_desc` / `by_date_asc`: Pre-sorted items by date timestamp.
- `by_read_time_asc` / `by_read_time_desc`: Pre-sorted items by calculated read time.
- `tags_index`: Mapping of tags to matching content IDs.
- `related_graph`: Full adjacency list representing the cross-content relationship graph.

Automatic cache invalidation monitors directory modification time (`mtime`). When any file is created, modified, or removed, caches invalidate automatically on the next request.

---

## 🚀 Deployment to Cloudflare Pages + R2

The site is built for static deployment with pre-rendered HTML and dynamic client-side hydration.

### 1. Build the Static Site
`scripts/build.py` pre-renders all primary views (`index.html`, `work.html`, `projects.html`) and individual case study detail pages into `dist/`, then copies static assets:
```bash
python3 scripts/build.py
```

### 2. Configure Cloudflare Credentials
Copy the deployment template into `.env`:
```bash
cp .env.example .env
```
Fill in the credentials:
- `CLOUDFLARE_API_TOKEN`: Token with `Pages:Deploy` and `R2:Write` permissions.
- `CLOUDFLARE_ACCOUNT_ID`: Your Cloudflare Account ID.
- `CLOUDFLARE_PAGES_PROJECT_ID`: Cloudflare Pages project name/ID.
- `CLOUDFLARE_R2_BUCKET`: R2 bucket for static assets and documents.
- `CLOUDFLARE_R2_ACCESS_KEY_ID` / `CLOUDFLARE_R2_ACCESS_KEY_SECRET`: R2 API credentials.

### 3. Deploy
Execute the deployment script:
```bash
bash scripts/deploy.sh
```
What this does:
1. Executes `python3 scripts/build.py` to compile all static pages.
2. Deploys `dist/` directly to Cloudflare Pages via Wrangler/Cloudflare API.
3. Synchronizes `src/assets/` (diagrams, images, PDFs) to the Cloudflare R2 bucket.

### 4. Continuous Deployment via GitHub Actions
The repository includes `.github/workflows/deploy.yml`. Once the six Cloudflare secrets are added to repository settings, every push to `main` builds and deploys the site automatically.

---

## 🛡️ Best Practices & Quality Gates

- **Unit Tests**: `python3 -m unittest discover tests` covers routing, content parsers, dynamic lifecycle, cross-linking, and index sorting.
- **Syntax Integrity**: `node -c src/js/detail-reader.js` validates reader JavaScript with 0 syntax errors.
- **Security Headers**: `app.py` injects `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, and `Referrer-Policy: strict-origin-when-cross-origin`.
- **Static Asset Fallbacks**: PDF assets (Resume, Cover Letter) resolve from both `/src/assets/<name>` and direct root paths (`/<name>`).
