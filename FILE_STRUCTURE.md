# FILE_STRUCTURE.md

This document outlines the directory structure and metadata for the Personal Portfolio codebase.

```
personal-website-portfolio/
├── AGENTS.md                          # Engineering and agent protocol rules
├── FILE_STRUCTURE.md                  # Semantic directory structure and metadata
├── README.md                          # Documentation and developer runbooks
├── app.py                             # Development server & SSR entry point
├── pyproject.toml                     # Python packaging and dependency specifications
├── requirements.txt                   # Dependency list (Flask, pypdf, requests, python-dotenv)
├── uv.lock                            # Deterministic uv dependency lockfile
│
├── content/                           # Single source of truth for authored Markdown content
│   ├── projects/                      # Personal projects & non-work deep dives
│   │   ├── 01-aws-smart-proxy.md      # AWS EC2 L7 Reverse Proxy implementation guide
│   │   └── 02-portfolio-evolution.md  # Architecture & features of this portfolio
│   └── work/                          # Production enterprise work case studies
│       ├── 01-sears-agentic-workflow.md
│       ├── 02-onecard-data-mesh.md
│       ├── 03-onecard-churn-engine.md
│       ├── 04-sears-cdc-snowflake.md
│       └── 05-auronova-risk-analytics.md
│
├── ref/                               # Ingestion reference directory for resumes and cover letters
│   ├── resume/                        # PDF resume drop folder
│   │   └── CV_AshishVineet.pdf
│   └── cover_letter/                  # PDF cover letter drop folder
│       └── Ashish Vineet Cover Letter.pdf
│
├── scripts/                           # Developer automation and deployment utilities
│   ├── build.py                       # Static site pre-renderer for Cloudflare Pages (`dist/`)
│   ├── deploy.sh                      # Zero-downtime deployment script to Cloudflare Pages & R2
│   ├── manage_content.py              # CLI for scaffolding work cases, project drafts, & pipeline
│   └── run_pipeline.py                # CLI runner for automated resume/cover letter extraction
│
├── src/                               # Application source code and core service layers
│   ├── assets/                        # SVG diagrams and architectural media assets
│   ├── content.py                     # Central content service (caching, querying, cross-linking)
│   ├── markdown_pipeline.py           # Markdown to sanitized HTML parser (H1-H6, tables, hr, code)
│   ├── data/                          # Structured JSON data feeds
│   │   ├── loader.py                  # Accessor helpers for portfolio data
│   │   ├── portfolio_data.json        # Compiled active data driving templates
│   │   ├── portfolio_data_historical.json # Verified historical archive data
│   │   ├── profile.py                 # Profile identity layer
│   │   └── resume.py                  # Resume experience and education layer
│   └── pipeline/                      # Automated document extraction and LLM pipeline
│       ├── config.py                  # Pipeline paths and environment configurations
│       ├── coordinator.py             # Pipeline orchestrator
│       ├── llm_client.py              # Multi-provider LLM interface (Gemini/OpenAI/Anthropic/Offline)
│       ├── pdf_extractor.py           # Robust PDF text extractor (pypdf with fallbacks)
│       ├── section_splitter.py        # Hierarchical resume section boundary & grounding resolver
│       ├── PARSING_GROUNDING_RULES.md # Truthfulness and anti-hallucination guidelines
│       └── generators/                # Modular section synthesis generators
│           ├── article_context_generator.py
│           ├── education_generator.py
│           ├── experience_generator.py
│           ├── pillars_generator.py
│           └── profile_generator.py
│
├── templates/                         # Jinja2 presentation templates and frontend assets
│   ├── base.html                      # Global shell with navigation and detail reader modal
│   ├── home.html                      # Homepage template
│   ├── projects.html                  # Project deep-dives listing and filter interface
│   ├── work.html                      # Work case studies listing and filter interface
│   ├── WEBPAGE_GENERATION.md          # Visual standards and layout design guidelines
│   ├── components/                    # Reusable UI component macros
│   │   └── content_card.html          # Unified card macro for work and project listings
│   ├── css/
│   │   └── styles.css                 # Master responsive stylesheet
│   └── js/
│       └── detail-reader.js           # Client-side interactive reader modal controller
│
└── tests/                             # Strict automated test suite
    ├── test_app.py                    # Server routes and lifecycle tests
    ├── test_content_links.py          # Bi-directional relationship graph tests
    ├── test_markdown_pipeline.py      # Markdown parser, headings, tables, and sanitization tests
    └── test_pipeline.py               # Document ingestion and generator test suite
```

