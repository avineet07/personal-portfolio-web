# AGENTS.md

## Working Principles
- **Think before coding.** Reason step by step, but keep it brief and focused. Avoid overthinking and be token-efficient.
- **Simplicity first.** Minimum code that solves the problem. No features beyond what was asked, no abstractions for single-use code, no "flexibility" that wasn't requested. Follow the software development practices like DRY and modular coding principles so documentation also becomes easier.
- **Surgical changes.** In case of a simple request, touch only what the request needs. Do not refactor adjacent code, rename variables for "clarity," reorder imports, or upgrade dependencies unless asked. Every changed line must trace directly to the user's request. In case of a complex request, refactor the related files only. If the user asks to refactor the codebase, suggest a minimal set of changes needed to achieve the user's goal.
- **Existing code first.** Search the repo before writing. Reuse, then extend, and create new code only when nothing suitable exists.
- **Ask, don't guess.** If a request is ambiguous in a way that matters, stop and ask the minimum number of questions. Do not silently pick an interpretation.

## Project Context
To create a professional portfolio webpage intended for a resume. The site presents projects, skills, experience, and contact information. It should look polished, load fast, be accessible, and deploy cleanly. 
- Built on a lightweight, zero-framework Python Flask SSR stack with Jinja2 templates, 
- Deploying to Cloudflare Pages (pre-rendered static HTML) and Cloudflare R2 (media, diagrams, and PDF assets). Content is stored in modular Markdown files 

## Repository Structure & Content Layout
- Update the latest file structure and metadata related to folders and subfolders in a SEPARATE file named FILE_STRUCTURE.md. Create one if not present.
- Update the file FILE_STRUCTURE.md if you have made any chnages in the folder structure of the project. 
- Obviously not every file needs to be included. Semantically include the files which are of importance to the user/developer. 

## Modular Code Rules
- **Single responsibility.** Each component, section, visualization, and data module does one thing. If a file grows beyond its boundary, split it.
- **Explicit boundaries.** Keep sections and components behind clear interfaces. Do not reach into internals of another module; expose what is needed through props or a dedicated service/data file.
- **Separate content from presentation.** Project data, bio text, and metadata live in dedicated data files, not hardcoded inside JSX/HTML.
- **Reuse components.** Build shared UI primitives (Card, Section, Badge) once and compose them.
- **No drive-by modularization.** Do not "extract" or "split" files outside the scope of the requested change.
- **Follow the repo layout.** Use the existing directory structure and naming conventions.

## Best Practices
- **Match existing style.** Use the project's formatter, linter, and naming conventions.
- **No secrets.** Never put tokens, passwords, or API keys in code or commits.
- **Never edit auto-generated files.** Edit the source and regenerate.
- **Test integrity.** Never delete, skip, or weaken tests to make them pass. Create stict test suite.
- **Accessibility.** Every interactive element is keyboard-reachable and labeled. Images have alt text.
- **Performance.** Optimize images, lazy-load below-the-fold content, avoid unnecessary dependencies.
- **SEO and metadata.** Keep page titles, meta descriptions, and Open Graph tags accurate.
- **Version-control safety.** Do not commit, push, or rewrite history unless explicitly asked.

## Execution Protocol
1. **Plan briefly** (2+ step tasks). State what will change and what will not.
2. **Implement only the requested change.**
3. **Run the validation gate.** Execute lint, type-check, test, and build commands. Do not report completion until they pass.
4. **Report honestly.** State what was verified and what was not.

## Token Efficiency
- **No narration.** Do not say "I'll start…," "Great question!," or "Let me…." Answer directly and act.
- **No verbose explanations.** Output the diff, the commands run, and a one-line result.
- **No restating the request.** Begin work immediately.

## Do Not
- Do not have any assumptions. if there is any ambiguity, prompt the user back for clarification ASAP.
- Do not overthink about the solution. If the user asks for a simple change, make a simple change.

## Commands
All commands related to the execution should be detailed in a separate "HOWTO" section in README.md. For example,
- Install: `uv sync` (or `pip install -r requirements.txt`)
- Dev: `python app.py` (or `uv run app.py`)
- Dev Server: `python app.py` (or `uv run app.py`)
- Test: `python -m unittest discover tests`
It should include generic commands (like the ones above) and also a project specific suite which will guide the users of the project functionality in a better way.

## Success Criteria
- Diffs contain fewer unrelated lines.
- The agent asks clarifying questions before implementation, not after.
- Changes are small enough to review in under two minutes.
