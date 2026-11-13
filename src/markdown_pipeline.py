#!/usr/bin/env python3
"""
markdown_pipeline.py — Shared, secure Markdown processing.

Imported by app.py (runtime) and manage_blogs.py (build-time).
Single source of truth for md → HTML conversion + sanitization.
"""

import html
import re

# ---------------------------------------------------------------------------
# Pre-compiled regex (Fix #2)
# ---------------------------------------------------------------------------
_RE_CODE_BLOCK = re.compile(r'```(\w*)\n(.*?)\n```', re.DOTALL)
_RE_BOLD = re.compile(r'\*\*(.*?)\*\*', re.DOTALL)
_RE_ITALIC = re.compile(r'\*(.*?)\*', re.DOTALL)
_RE_INLINE_CODE = re.compile(r'`(.*?)`')
_RE_ORDERED_LIST = re.compile(r'^\d+\.\s')
_RE_HEADING = re.compile(r'^(#{1,6})\s+(.+)$')
_RE_HR = re.compile(r'^([-*_]{3,})\s*$')
_RE_LINK = re.compile(r'(?<!!)\[([^\]]+)\]\(([^)]+)\)')

# Image markdown: ![alt](src) — supports relative paths
_RE_IMAGE = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')

# Video markdown: ![video](src) or [video](src) — detected by extension
_VIDEO_EXTENSIONS = ('.mp4', '.webm', '.ogg', '.mov')


def _is_video_path(path):
    """Return True if the path looks like a video file."""
    return any(path.lower().endswith(ext) for ext in _VIDEO_EXTENSIONS)


# ---------------------------------------------------------------------------
# Sanitizer (Fix #3 — proper attribute whitelisting)
# ---------------------------------------------------------------------------

# Tags we allow (our parser only ever produces these)
_ALLOWED_TAGS = frozenset({
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'p', 'br', 'hr',
    'strong', 'em', 'u', 's',
    'code', 'pre',
    'ul', 'ol', 'li',
    'blockquote',
    'div', 'span',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'a', 'img',
    'figure', 'figcaption',
    'video', 'source',  # media support
})

# Per-tag allowed attributes — anything else is stripped
_ALLOWED_ATTRS = {
    'a':          {'href', 'target', 'rel', 'class', 'title'},
    'img':        {'src', 'alt', 'lightbox', 'class', 'loading', 'width', 'height'},
    'figure':     {'class'},
    'figcaption': {'class'},
    'video':      {'src', 'controls', 'autoplay', 'loop', 'muted', 'playsinline', 'class', 'lightbox', 'preload', 'poster'},
    'source':     {'src', 'type'},
    'code':       {'class'},  # language class from fenced blocks
    'pre':        {'class'},
    'div':        {'class', 'id'},
    'span':       {'class'},
    'hr':         {'class'},
    'table':      {'class'},
    'th':         {'align', 'class'},
    'td':         {'align', 'class'},
    'h1':         {'id', 'class'},
    'h2':         {'id', 'class'},
    'h3':         {'id', 'class'},
    'h4':         {'id', 'class'},
    'h5':         {'id', 'class'},
    'h6':         {'id', 'class'},
}


def _sanitize_html(text):
    """Strip any raw HTML that could carry XSS payloads (Fix #3).

    Whitelists BOTH tags AND per-tag attributes.  Unknown attributes are
    removed, unknown tags are escaped to text.
    """

    def _replace_tag(m):
        raw = m.group(0)
        # Quick extract tag name
        inner = raw[1:].rstrip('/>')
        parts = inner.split()
        tag_name = parts[0].lower() if parts else ''

        # Closing or self-closing tag
        if tag_name.startswith('/'):
            return raw  # leave closers alone

        if tag_name not in _ALLOWED_TAGS:
            return html.escape(raw)

        # Allowed tag — now filter attributes
        allowed_attrs = _ALLOWED_ATTRS.get(tag_name, set())
        if not allowed_attrs:
            # No attributes allowed on this tag (e.g. <p>, <h1>, <li>)
            # Rebuild tag with no attrs
            # Find where the tag name ends
            rest = raw[len('<') + len(tag_name):]
            if rest.lstrip().startswith('>'):
                return f'<{tag_name}>'
            elif rest.lstrip().startswith('/>'):
                return f'<{tag_name} />'
            return raw

        # Parse attributes: rebuild with only allowed ones
        attr_str = raw[len('<') + len(tag_name):]
        # Find the closing > or />
        close_idx = attr_str.rfind('>')
        attrs_part = attr_str[:close_idx]
        close_char = '>' if attr_str[close_idx] == '>' else '/>'

        # Simple attr parser: name="value", name='value', name=value, or bare name
        safe_attrs = []
        for token in _parse_attrs(attrs_part):
            attr_name = token.split('=')[0].strip().lower()
            if attr_name in allowed_attrs:
                safe_attrs.append(token)

        if safe_attrs:
            return '<' + tag_name + ' ' + ' '.join(safe_attrs) + close_char.rstrip('/')
        return '<' + tag_name + close_char.rstrip('/')

    return re.sub(r'<[^>]*>', _replace_tag, text)


def _parse_attrs(attrs_part):
    """Minimal attribute parser. Returns list of 'name="value"' or 'name' strings."""
    result = []
    s = attrs_part.strip()
    if not s:
        return result

    i = 0
    while i < len(s):
        # Skip whitespace
        while i < len(s) and s[i] in (' ', '\t', '\n', '\r'):
            i += 1
        if i >= len(s):
            break

        # Read attribute name
        name_start = i
        while i < len(s) and s[i] not in (' ', '\t', '=', '>', '<', '/'):
            i += 1
        name = s[name_start:i].strip()
        if not name:
            i += 1
            continue

        # Skip whitespace
        while i < len(s) and s[i] in (' ', '\t'):
            i += 1

        if i < len(s) and s[i] == '=':
            i += 1  # skip '='
            while i < len(s) and s[i] in (' ', '\t'):
                i += 1

            if i < len(s) and s[i] in ('"', "'"):
                quote = s[i]
                i += 1
                val_start = i
                while i < len(s) and s[i] != quote:
                    i += 1
                value = s[val_start:i]
                i += 1  # skip closing quote
                result.append(f'{name}="{value}"')
            else:
                # Unquoted value
                val_start = i
                while i < len(s) and s[i] not in (' ', '\t', '>', '<', '/'):
                    i += 1
                value = s[val_start:i]
                result.append(f'{name}="{value}"')
        else:
            # Bare attribute (e.g. controls, autoplay)
            result.append(name)

    return result


# ---------------------------------------------------------------------------
# Markdown → HTML
# ---------------------------------------------------------------------------

def _is_table_block(block):
    """Detect if a block represents a GitHub-Flavored Markdown table."""
    lines = [l.strip() for l in block.split("\n") if l.strip()]
    if len(lines) >= 2 and lines[0].startswith("|") and lines[0].endswith("|"):
        sep = lines[1].replace(" ", "").replace("-", "").replace("|", "").replace(":", "")
        return sep == ""
    return False


def _parse_table(block):
    """Convert GFM markdown table into sanitized HTML table wrapped in a scroll container."""
    lines = [l.strip() for l in block.split("\n") if l.strip()]
    if len(lines) < 2:
        return block

    def _split_row(line):
        raw = line.strip()
        if raw.startswith("|"):
            raw = raw[1:]
        if raw.endswith("|"):
            raw = raw[:-1]
        return [cell.strip() for cell in raw.split("|")]

    headers = _split_row(lines[0])
    data_rows = [_split_row(line) for line in lines[2:]]

    out = ['<div class="table-wrapper"><table class="markdown-table"><thead><tr>']
    for h in headers:
        out.append(f'<th>{_inline(h)}</th>')
    out.append('</tr></thead>')

    if data_rows:
        out.append('<tbody>')
        for row in data_rows:
            out.append('<tr>' + ''.join(f'<td>{_inline(cell)}</td>' for cell in row) + '</tr>')
        out.append('</tbody>')

    out.append('</table></div>')
    return ''.join(out)


def md_to_html(md_text):
    """Convert Markdown text to sanitized HTML.

    Supports:
    - Fenced code blocks with language hints
    - Headings (# to ######)
    - Horizontal rules (---, ***, ___)
    - GitHub-style callouts (> [!NOTE], > [!TIP], etc.)
    - Blockquotes (> text)
    - GFM Tables (| Col | Col |)
    - Raw HTML block elements (<figure>, <pre>, etc.)
    - Bullet and ordered lists
    - Bold, italic, inline code (with protected code tokens)
    - Links [text](url)
    - Images with lightbox support: ![alt](path)
    - Video links: ![video](path.mp4) or [video](path.mp4)
    """
    if not md_text:
        return ""

    # 1. Protect fenced code blocks
    code_blocks = []

    def _save_code(match):
        lang = match.group(1) or ""
        code = html.escape(match.group(2))
        code_blocks.append(f'<pre><code class="{lang}">{code}</code></pre>')
        return f'__CODE_BLOCK_{len(code_blocks) - 1}__'

    md_text = _RE_CODE_BLOCK.sub(_save_code, md_text)

    # 2. Normalize block separation for headings, horizontal rules, and tables
    # Ensure headings have blank lines around them
    md_text = re.sub(r'([^\n])\n(#{1,6}\s+[^\n]+)', r'\1\n\n\2', md_text)
    md_text = re.sub(r'^(#{1,6}\s+[^\n]+)\n([^\n])', r'\1\n\n\2', md_text, flags=re.MULTILINE)

    # Ensure horizontal rules (---, ***, ___) have blank lines around them
    md_text = re.sub(r'([^\n])\n([-*_]{3,})\s*$', r'\1\n\n\2', md_text, flags=re.MULTILINE)
    md_text = re.sub(r'^([-*_]{3,})\s*\n([^\n])', r'\1\n\n\2', md_text, flags=re.MULTILINE)

    # Ensure tables have blank lines around them
    md_text = re.sub(r'([^\n])\n(\|.+\|\s*)\n(\|[-:| ]+\|\s*)', r'\1\n\n\2\n\3', md_text)
    md_text = re.sub(r'(\|.+\|)\n([^\n|])', r'\1\n\n\2', md_text)

    # 3. Process blocks
    blocks = md_text.split("\n\n")
    processed = []
    in_list = None
    list_items = []

    def _close_list():
        nonlocal in_list, list_items
        tag = in_list
        html_out = f"<{tag}>\n" + "".join(
            f"  <li>{_inline(item)}</li>\n" for item in list_items
        ) + f"</{tag}>"
        list_items.clear()
        in_list = None
        return html_out

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # --- Headings (# to ######) ---
        m_heading = _RE_HEADING.match(block)
        if m_heading:
            if in_list:
                processed.append(_close_list())
            level = len(m_heading.group(1))
            heading_text = m_heading.group(2).strip()
            processed.append(f"<h{level}>{_inline(heading_text)}</h{level}>")

        # --- Horizontal Rule (---, ***, ___) ---
        elif _RE_HR.match(block):
            if in_list:
                processed.append(_close_list())
            processed.append("<hr />")

        # --- GitHub callouts ---
        elif block.startswith("> [!"):
            if in_list:
                processed.append(_close_list())
            lines = block.split("\n")
            header = lines[0].replace("> [!", "").replace("]", "").strip()
            content_lines = _strip_quote_prefix(lines[1:])
            content = " ".join(content_lines).strip()
            processed.append(
                f'<div class="blog-callout"><strong>{header.title()}:</strong> '
                f"{_inline(content)}</div>"
            )

        # --- Blockquotes ---
        elif block.startswith("> "):
            if in_list:
                processed.append(_close_list())
            content_lines = _strip_quote_prefix(block.split("\n"))
            content = " ".join(content_lines).strip()
            processed.append(f"<blockquote>{_inline(content)}</blockquote>")

        # --- GFM Tables ---
        elif _is_table_block(block):
            if in_list:
                processed.append(_close_list())
            processed.append(_parse_table(block))

        # --- Raw HTML Block elements (<figure>, <pre>, <div>, etc.) ---
        elif block.startswith(("<figure", "<pre", "<div", "<table", "<video", "__CODE_BLOCK_")):
            if in_list:
                processed.append(_close_list())
            processed.append(block)

        # --- Lists ---
        elif (block.startswith("- ") or block.startswith("* ")
              or _RE_ORDERED_LIST.match(block)):
            for line in block.split("\n"):
                line = line.strip()
                if not line:
                    continue
                if line.startswith("- ") or line.startswith("* "):
                    if in_list == 'ol':
                        processed.append(_close_list())
                    if not in_list:
                        in_list = 'ul'
                    list_items.append(line[2:])
                elif _RE_ORDERED_LIST.match(line):
                    if in_list == 'ul':
                        processed.append(_close_list())
                    if not in_list:
                        in_list = 'ol'
                    list_items.append(re.sub(r'^\d+\.\s', '', line))
                else:
                    if list_items:
                        list_items[-1] += " " + line
        else:
            # Paragraph — process images/video first, then inline formatting
            if in_list:
                processed.append(_close_list())
            content = _process_images(block)
            content = _inline(content)
            processed.append(f"<p>{content}</p>")

    if in_list:
        processed.append(_close_list())

    result = "\n\n".join(processed)

    # 4. Restore code blocks
    for i, code_html in enumerate(code_blocks):
        result = result.replace(f'__CODE_BLOCK_{i}__', code_html)

    # 5. Sanitize HTML
    result = _sanitize_html(result)

    return result


def _process_images(text):
    """Convert ![alt](src) markdown to HTML <img> or <video> media elements."""

    def _replace_img(m):
        alt = m.group(1)
        src = m.group(2)

        if _is_video_path(src):
            caption_html = f'<p class="media-caption">{alt}</p>' if alt else ''
            return f'<div class="media-video-container"><video controls playsinline preload="metadata" class="media-video"><source src="{src}">Your browser does not support video.</video>{caption_html}</div>'

        caption_html = f'<figcaption class="media-caption">{alt}</figcaption>' if alt else ''
        return f'<figure class="media-figure"><img lightbox src="{src}" alt="{alt}" loading="lazy" class="media-image" />{caption_html}</figure>'

    return _RE_IMAGE.sub(_replace_img, text)


def _inline(text):
    """Apply inline Markdown formatting with protected code spans and link handling."""
    inline_codes = []

    def _save_inline_code(m):
        code_content = html.escape(m.group(1))
        inline_codes.append(f'<code>{code_content}</code>')
        return f'__INLINE_CODE_{len(inline_codes) - 1}__'

    # 1. Protect inline code spans so asterisks/underscores inside are never mangled
    text = _RE_INLINE_CODE.sub(_save_inline_code, text)

    # 2. Markdown links [text](url)
    text = _RE_LINK.sub(r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>', text)

    # 3. Bold and Italic
    text = _RE_BOLD.sub(r'<strong>\1</strong>', text)
    text = _RE_ITALIC.sub(r'<em>\1</em>', text)

    # 4. Restore inline code spans
    for i, code_tag in enumerate(inline_codes):
        text = text.replace(f'__INLINE_CODE_{i}__', code_tag)

    return text


def _strip_quote_prefix(lines):
    """Remove leading '> ' from blockquote/callout lines."""
    result = []
    for line in lines:
        clean = line.strip()
        if clean.startswith("> "):
            result.append(clean[2:])
        elif clean == ">":
            result.append("")
        else:
            result.append(clean)
    return result


# ---------------------------------------------------------------------------
# Utilities (shared with manage_blogs.py)
# ---------------------------------------------------------------------------

_RE_SLUG_NON_ALNUM = re.compile(r'[^a-z0-9\s-]')
_RE_SLUG_MULTI_SEP = re.compile(r'[\s-]+')


def slugify(text):
    """Convert a title string into a URL-safe slug."""
    text = text.lower()
    text = _RE_SLUG_NON_ALNUM.sub('', text)
    text = _RE_SLUG_MULTI_SEP.sub('-', text)
    return text.strip('-')


def parse_front_matter(content):
    """Parse YAML-like front matter (--- delimited)."""
    meta = {"tags": []}
    if not content.startswith("---"):
        return meta, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return meta, content

    front_matter_str = parts[1]
    body_str = parts[2]

    lines = front_matter_str.split("\n")
    current_key = None

    for line in lines:
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        if not stripped:
            continue

        if indent > 0 and stripped.startswith("- "):
            val = stripped[2:].strip().strip('"\'')
            if current_key and isinstance(meta.get(current_key), list):
                meta[current_key].append(val)
        elif indent > 0 and ":" in stripped and current_key:
            ck, cv = stripped.split(":", 1)
            ck = ck.strip()
            cv = cv.strip().strip('"\'')
            if not isinstance(meta.get(current_key), dict):
                meta[current_key] = {}
            meta[current_key][ck] = cv
        elif ":" in stripped:
            key, val = stripped.split(":", 1)
            key = key.strip()
            val = val.strip().strip('"\'')

            if val.startswith("[") and val.endswith("]"):
                meta[key] = [item.strip().strip('"\'') for item in val[1:-1].split(",") if item.strip()]
                current_key = key
            elif not val:
                meta[key] = []
                current_key = key
            else:
                meta[key] = val
                current_key = key

    return meta, body_str.strip()


def calculate_read_time(text):
    """Estimate read time in minutes (200 WPM)."""
    words = len(text.split())
    minutes = max(1, round(words / 200))
    return f"{minutes} min read"
