---
id: portfolio-evolution
order: 2
title: "How This Portfolio Was Built — Architecture, Features, and Pipeline Evolution"
date: Oct-2026
summary: A comprehensive technical deep dive into the portfolio's architecture — featuring an automated resume ingestion pipeline, interactive client-side detail reader, bidirectional graph cross-linking, custom Markdown engine, and Cloudflare Pages static pre-rendering.
topic: Engineering
readTime: 10 min read
tags:
  - portfolio
  - architecture
  - pipeline
  - markdown
  - flask
  - static-site
related:
  - sears-agentic-workflow
  - onecard-data-mesh
  - aws-smart-proxy
---

This article is a live checkpoint of the portfolio itself. Where the other case studies in this site detail enterprise engineering at Sears Holdings, OneCard, and Auronova Consulting, this document explores how the platform presenting that work was engineered — from an automated resume extraction pipeline to a zero-framework, Markdown-first static architecture deployed to Cloudflare Pages.

It is a meta-document, written in standard Markdown in `content/projects/portfolio-evolution.md`, rendered dynamically during development by Python Flask, pre-compiled into static HTML for production, and verified by a strict test suite.

---

### Core Architectural Philosophy

The design rests on three core principles:

1. **Markdown as the Single Source of Truth**: Content is authored once in clean Markdown with frontmatter. Adding or editing an engineering case study requires zero modifications to Python routes or HTML templates.
2. **Zero Client-Side Framework Overhead**: The application deliberately avoids heavyweight frontend frameworks (React, Next.js, Vue). The UI is rendered server-side via Jinja2 templates, styled with modern vanilla CSS design tokens, and augmented with lightweight, dependency-free vanilla JavaScript.
3. **Deterministic Separation of Content, Data, and Presentation**:
   - `content/`: Authored Markdown case studies and technical deep dives.
   - `src/data/`: Structured, human-editable JSON and Python data layers.
   - `src/pipeline/`: Document ingestion and optional LLM synthesis pipeline.
   - `templates/`: Presentation layer (Jinja2 templates, CSS variables, and modal controllers).
   - `dist/`: Pre-rendered static compilation target for edge CDN deployment.

---

### Key Feature Capabilities

The platform combines automated content generation with high-performance presentation features:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                SYSTEM ARCHITECTURE OVERVIEW                            │
└────────────────────────────────────────────────────────────────────────────────────────┘

  [ PDF Documents ]
   ├── ref/resume/CV_AshishVineet.pdf
   └── ref/cover_letter/Cover_Letter.pdf
            │
            ▼
  [ Extraction & Synthesis Pipeline (src/pipeline/) ]
   ├── PDF Extractor: pypdf (fallbacks: pdfplumber, pymupdf)
   ├── Section Generators: Profile, Pillars, Experience, Education
   ├── Grounding Gate: PARSING_GROUNDING_RULES.md (Zero Hallucination)
   └── Optional Synthesis: LLM Engine (Gemini / OpenAI / Anthropic)
            │
            ▼
  [ Intermediate Data Feed (src/data/portfolio_data.json) ]
            │
            ├─────────────────────────────────────────┐
            ▼                                         ▼
  [ Content Service (src/content.py) ]    [ Markdown Engine (src/markdown_pipeline.py) ]
   ├── Frontmatter Metadata Parser         ├── Headings (H1–H6) & Spacing Normalizer
   ├── Bidirectional Graph Cross-Linker    ├── GFM Tables with Responsive Wrappers
   └── In-Memory Mtime Invalidation Cache  └── Attribute-Level XSS Sanitizer
            │                                         │
            └────────────────────┬────────────────────┘
                                 ▼
                     [ SSR & Static Pre-Renderer ]
                      ├── Local Dev: app.py (Flask SSR)
                      └── Build Gate: scripts/build.py ──► dist/ (Cloudflare Pages)
```

---

### 1. Document Ingestion & Pipeline Orchestrator (`src/pipeline/`)

To prevent manual data entry across multiple site sections whenever a resume changes, the platform includes an automated ingestion pipeline:

- **Decoupled Drop Folders**: Resumes and cover letters live in dedicated directories (`ref/resume/` and `ref/cover_letter/`). The pipeline automatically resolves the latest modified PDF document.
- **Robust Multi-Engine PDF Extraction (`pdf_extractor.py`)**: Uses `pypdf` as the primary engine with automatic fallbacks to `pdfplumber` or `pymupdf` (fitz) to reliably extract clean text and metadata across different PDF encoding variants.
- **Anti-Hallucination & Grounding Gate (`PARSING_GROUNDING_RULES.md`)**: A strict validation rulebook prevents the extraction layer from inventing metrics, hallucinating enterprise roles, or fabricating credentials. If a metric or institution is not present in the source PDF, the generator safely omits the field.
- **Dual-Engine Execution**:
  - *Offline Deterministic Mode*: Regex and heuristic state machines extract clean profile identity, skill taxonomies, and employment timelines with zero external API calls or network dependencies.
  - *LLM-Augmented Mode*: Optional integration via `LLMClient` supporting Google Gemini (`gemini-1.5-flash`), OpenAI (`gpt-4o-mini`), and Anthropic (`claude-3-5-haiku`). Generates concise, metric-focused bullet summaries and extracts architectural pillars.
- **Human-Editable Intermediate JSON**: The pipeline compiles into `src/data/portfolio_data.json`. Because JSON nesting is transparent, developers can fine-tune generated copy without touching Python source code. A verified baseline is preserved in `src/data/portfolio_data_historical.json`.

---

### 2. Interactive Modal Detail Reader (`templates/js/detail-reader.js`)

Case studies and technical articles can be consumed either as standalone pages or through an interactive in-page reader:

- **Zero-Dependency Vanilla Architecture**: The detail reader runs without external libraries, ensuring sub-millisecond initialization and 60fps rendering.
- **Deep-Linking & History Synchronization**: Opening any study updates the browser URL query parameter (`?page=projects&post=<id>` or `?page=work&case=<id>`) using `window.history.pushState`. Sharing or refreshing the URL immediately opens the requested article in context.
- **Draggable & Resizable Viewport**: Users on wide displays can drag the modal header to reposition the modal or pull the custom resize handle to widen the reading container.
- **Fullscreen Mode & Keyboard Shortcuts**:
  - `Esc`: Closes the reader and restores scroll position.
  - `F`: Toggles edge-to-edge fullscreen reading mode.
- **Connected Study Traversal**: Clicking a "Connected Case Study" pill transitions the reader directly to the related study without closing and reopening the modal.
- **Diagram Lightbox**: Architectural flowcharts and system diagrams include inline lightbox zoom controls for high-resolution inspection.

---

### 3. Bidirectional Content Relationship Graph (`src/content.py`)

Rather than maintaining static lists of related reading, the platform computes a live relationship graph:

- **Declarative Frontmatter**: Markdown files specify relationships in frontmatter:
  ```yaml
  related:
    - sears-agentic-workflow
    - snowflake-dms-cdc
  ```
- **Bidirectional Graph Resolution**: If Article A links to Case Study B, Case Study B automatically registers Article A in its `related_items` collection.
- **Self-Healing Link Integrity**: If a connected document is deleted or renamed, `_link_relationships()` silently prunes the dangling reference, guaranteeing zero dead links on cards or reader footers.

---

### 4. Custom Zero-Dependency Markdown Engine (`src/markdown_pipeline.py`)

To eliminate heavyweight runtime dependencies like external CommonMark packages, the site utilizes an audited, custom Markdown pipeline:

- **Complete Heading Hierarchy (`h1` through `h6`)**: Normalizes heading boundaries and translates markdown headings into semantic HTML elements with styling hooks.
- **GFM Table Parsing**: Automatically identifies pipe-delimited tables and wraps them in scroll-safe containers:
  ```html
  <div class="table-wrapper"><table class="markdown-table">...</table></div>
  ```
- **GitHub-Style Callouts**: Supports blockquote callout notation (`> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`, `> [!WARNING]`), converting them into styled alert boxes.
- **Code Span Token Protection**: Protects inline code blocks (`<code>...</code>`) before parsing bold or italic markup, ensuring wildcards (`*.<domain>.com`) and snake_case variables (`user_id`) are never corrupted.
- **Horizontal Dividers (`---`, `***`)**: Cleanly renders semantic `<hr />` elements with automated margin spacing.
- **Attribute-Level Sanitization**: Whitelists both allowed tags (`h1-h6`, `table`, `pre`, `code`, `video`, `figure`) and permitted per-tag attributes (`href`, `lightbox`, `controls`) to neutralize XSS vulnerabilities.

---

### 5. Multi-Faceted Client-Side Filtering & Sorting

The `Work` and `Projects` catalog views provide instant client-side data exploration:

- **Work Organization & Domain Filtering**: Filter case studies simultaneously across enterprise organizations (Sears Holdings, OneCard, Auronova) and technical categories (Agentic AI, Data Architecture, Predictive ML).
- **Personal Projects Tag Cloud**: Real-time multi-tag selection across domain topics (`#langgraph`, `#snowflake`, `#aws`, `#lightgbm`).
- **Flexible Sorting Engine**:
  - *Default Order*: Curated narrative sequence.
  - *Chronological*: Newest first or oldest first based on ISO date stamps.
  - *Estimated Reading Time*: Shortest read to longest read (calculated dynamically at 200 WPM).
  - *Alphabetical*: Title A–Z.

---

### 6. Developer CLI & Content Management (`scripts/manage_content.py`)

A centralized developer CLI streamlines authoring and pipeline maintenance:

```bash
# List all active work studies and project deep-dives with metadata
python scripts/manage_content.py list

# Scaffold a new production work case study draft in content/work/
python scripts/manage_content.py new work "Real-Time Fraud Detection Engine"

# Scaffold a new technical project deep-dive in content/projects/
python scripts/manage_content.py new project "Vector Indexing with pgvector"

# Run the end-to-end resume extraction pipeline
python scripts/manage_content.py pipeline --scaffold
```

---

### 7. Zero-Framework Hybrid SSR & Static Pre-Rendering

The architecture provides the best of both local agility and edge deployment:

- **Local Development**: `python app.py` serves a live Flask development server with automatic cache invalidation on markdown edits.
- **Cloudflare Edge Deployment (`scripts/build.py`)**: Crawls all dynamic routes and generates pre-rendered, standalone HTML files into `dist/`. All CSS, JS, content diagrams, and media are copied automatically.
- **Zero Cold-Start Latency**: Because Cloudflare Pages serves pre-rendered HTML files directly from edge points of presence, the site loads instantaneously with zero server-side cold starts or database query latencies.

---

### Checkpoints of the Evolution

The table below traces the architectural transformation across the project lifecycle:

| Phase | Core Mechanism | Engineering Rationale & Outcome |
|---|---|---|
| **Phase 1: Monolithic Flask SSR** | `app.py` + hardcoded HTML in Jinja2 templates | Fast initial prototype, but content was duplicated between Python dictionaries and HTML markup. |
| **Phase 2: Markdown-First Architecture** | `content/work/`, `content/projects/`, `src/content.py` | Established a single source of truth. New articles are isolated `.md` files that appear automatically without route edits. |
| **Phase 3: Structured Data Layer Split** | `src/data/profile.py`, `src/data/resume.py` | Separated immutable profile identity (links, core skills) from narrative career milestones to eliminate deadweight schema keys. |
| **Phase 4: Document Ingestion Pipeline** | `src/pipeline/`, `scripts/run_pipeline.py` | Automated resume & cover letter PDF ingestion with offline deterministic heuristics and optional LLM synthesis. |
| **Phase 5: Bidirectional Link Graph** | `_link_relationships()` in `src/content.py` | Automated bidirectional relationship mapping between enterprise work studies and personal projects. |
| **Phase 6: Custom Markdown Engine Hardening** | `src/markdown_pipeline.py` | Native H1–H6 parsing, GFM tables, GitHub callouts, code span protection, and XSS sanitization. |
| **Phase 7: Cloudflare Static Pre-Render** | `scripts/build.py` ──► `dist/` | Compiles the dynamic Flask site into zero-latency static HTML for edge hosting on Cloudflare Pages and R2. |

---

### Summary

The portfolio is engineered not as a generic template, but as a transparent, modular system: authored Markdown in `content/`, normalization in `src/content.py`, structured data in `src/data/`, and pre-rendered templates in `dist/`.

Every layer is verifiable, every script can be executed independently from the terminal, and any new resume PDF can refresh the underlying content model in seconds.
