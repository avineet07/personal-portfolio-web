# Resume Parsing & Content Generation Grounding Rules

> **Core Mandate**: All published portfolio content must be strictly grounded in verified source documents (`ref/resume/` and `ref/cover_letter/`). Never fabricate, hallucinate, or extrapolate unverified claims. If content cannot be corroborated by the source materials, it must not be published.

---

## 1. Absolute Truthfulness & Negative Constraints

1. **Zero Hallucination Tolerance**:
   - Never invent job titles, employer names, dates of employment, degrees, GPA/grades, or geographical locations.
   - Never invent quantitative metrics (e.g., claiming "improved model accuracy by 45%" when the resume states "84% accuracy" or doesn't mention a percentage).
   - Never fabricate GitHub repositories, live demo URLs, conference talks, or publication citations.

2. **Relevance & The "Do Not Publish" Directive**:
   - Only publish roles, projects, and skills that the candidate has genuinely worked on.
   - If a technical domain, case study, or section is not supported by evidence in the resume or cover letter, **omit that section entirely**.
   - An omitted section is professional; an invented claim is a critical failure.

3. **No Exaggeration of Scope**:
   - Maintain the candidate's exact level of ownership (e.g., contributor vs. architect vs. lead).
   - If the candidate implemented an internal prototype or Proof-of-Concept (PoC), do not misrepresent it as a global production system serving millions of users unless explicitly documented.

---

## 2. Extraction & Synthesis Protocol

### 2.1 Identity & Profile
- **Name**: Must match the exact name header in `ref/resume/`.
- **Contact Info**: Phone numbers, emails, and LinkedIn/GitHub handles must be extracted verbatim. If a handle is missing, leave the field empty (`""`) rather than guessing.
- **Headline**: Must synthesize the verified domains present in the resume (e.g., AI/ML, Data Engineering, Product Analytics). Do not add unrelated specialties (e.g., do not add "Mobile App Developer" or "Cybersecurity Specialist" if not in the resume).

### 2.2 Work Experience & Case Studies
- **Roles & Dates**: Dates must preserve the exact period from the resume (e.g., "May 2024 – Present", "Jan 2021 – May 2024").
- **Summaries**: Summaries must be faithful syntheses of the actual bullet points listed under that specific role.
- **Article Generation / Scaffolding**: Case studies scaffolded into `content/work/` or `content/projects/` must directly correspond to projects documented in the candidate's resume or cover letter. Never scaffold speculative projects.

### 2.3 Technical Skills Matrix
- Only include programming languages, frameworks, databases, and tools explicitly named in the `TECHNICAL SKILLS` or experience bullets of the resume.
- Do not add trending buzzwords (e.g., Quantum Computing, Web3, Rust) unless specifically listed in the candidate's verified documents.

---

## 3. Fallback Hierarchy

Whenever this pipeline runs:
1. **Source Grounding**: Read documents from `ref/resume/` and `ref/cover_letter/`.
2. **Deterministic & Vetted Verification**: If LLM parsing produces any claims that cannot be traced back to the source text, reject the LLM output and fall back to the human-vetted production data in `src/data/loader.py`.
3. **Audit Trail**: Every compiled `portfolio_data.json` records the exact source filenames in `source_documents` along with a UTC generation timestamp.

