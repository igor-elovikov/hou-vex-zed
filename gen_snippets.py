"""Generate Zed editor VEX snippets from Houdini's vex.zip help files."""

import json
import os
import re
import sys
import zipfile


def load_zip(path):
    z = zipfile.ZipFile(path)
    files = {}
    for name in z.namelist():
        try:
            files[name] = z.read(name).decode("utf-8")
        except Exception:
            pass
    return files


def extract_section_by_id(content, section_id):
    """Extract a named section (#id: xxx) from an include file."""
    # Sections are delimited by :tag:...\n    #id: xxx\n    content...
    # Find the block with matching #id
    pattern = re.compile(
        r"^(:(?:arg|null|varg)[^\n]*\n)"  # tag line
        r"(\s+#id:\s*" + re.escape(section_id) + r"\s*\n)"  # id line
        r"((?:\s{4,}[^\n]*\n|\s*\n)*)",  # indented body
        re.MULTILINE,
    )
    m = pattern.search(content)
    if m:
        tag_line = m.group(1).strip()  # e.g. :arg:geohandle:
        body = m.group(3)
        # Dedent body
        lines = body.split("\n")
        result = []
        for line in lines:
            # Remove first 4 spaces of indentation
            if line.startswith("    "):
                result.append(line[4:])
            else:
                result.append(line)
        # Prepend the tag line so it renders as "argname:" after markup stripping
        return tag_line + "\n" + "\n".join(result).strip()
    return None


def resolve_include(include_str, files):
    """Resolve :include directives.

    Formats:
      :include _common#geohandle_arg:
      :include _area_variadic:
      :include /vex/functions/agentsolvefbik#targetxforms:
      :include /vex/contexts/shading_contexts#lightmask:
    """
    # Remove trailing colon
    include_str = include_str.strip().rstrip(":")
    # Parse path and optional section
    parts = include_str.split("#", 1)
    path = parts[0]
    section_id = parts[1] if len(parts) > 1 else None

    # Resolve path to zip entry
    if path.startswith("/vex/"):
        # /vex/functions/foo -> functions/foo.txt
        zip_path = path[5:] + ".txt"  # strip /vex/
    elif path.startswith("_") or not "/" in path:
        # _common, _area_variadic -> functions/_common.txt
        zip_path = "functions/" + path + ".txt"
    else:
        zip_path = path + ".txt"

    content = files.get(zip_path)
    if content is None:
        return ""

    if section_id:
        result = extract_section_by_id(content, section_id)
        return result if result else ""
    else:
        # Include the whole file, skip the #type: include header
        lines = content.split("\n")
        body_lines = []
        in_header = True
        for line in lines:
            if in_header:
                if line.startswith("#") or line.strip() == "":
                    continue
                in_header = False
            body_lines.append(line)
        return "\n".join(body_lines).strip()


def process_includes(text, files):
    """Resolve all :include directives in text."""
    def replace_include(m):
        return resolve_include(m.group(1), files)

    return re.sub(r":include\s+(\S+?):", replace_include, text)


def strip_houdini_markup(text):
    """Convert Houdini wiki markup to plain text."""
    # Remove code block markers {{{ and }}}
    text = re.sub(r"\{\{\{", "", text)
    text = re.sub(r"\}\}\}", "", text)
    # Remove #!vex directives
    text = re.sub(r"#!vex\s*\n?", "", text)

    # [Vex:funcname] -> funcname
    text = re.sub(r"\[Vex:(\w+)\]", r"\1", text)
    # [text|/path] -> text
    text = re.sub(r"\[([^|\]]+)\|[^\]]+\]", r"\1", text)
    # [/path/text] -> text (plain links)
    text = re.sub(r"\[/[^\]]+/([^\]/]+)\]", r"\1", text)
    # [Node:type] or similar
    text = re.sub(r"\[\w+:[^\]]+\]", "", text)

    # <<variable>> -> variable
    text = re.sub(r"<<(\w+)>>", r"\1", text)

    # :box:Title -> Title  (with or without text after)
    text = re.sub(r":box:\s*", "", text)
    # :tip:, :warning:, :note:, :col: labels
    text = re.sub(r":(tip|warning|note|col):\s*", "", text)

    # :arg:`name`, `name2`: or :arg:name: or :arg:name (no trailing colon)
    # or :arg: name (with space) or ::arg:name: or ::arg::name:
    text = re.sub(r":+arg:`([^`]+)`(?:,\s*`[^`]+`)*:?", r"\1:", text)
    text = re.sub(r":+arg::?\s*([^:\s]+):?", r"\1:", text)
    # :varg:`name`: or :varg:name:
    text = re.sub(r":+varg:`([^`]+)`:?", r"\1:", text)
    text = re.sub(r":+varg::?\s*([^:\s]+):?", r"\1:", text)
    # :returns: / :returnss: -> Returns:
    text = re.sub(r":returns+:", "Returns:", text)
    # :list: -> (remove)
    text = re.sub(r":list:\s*", "", text)

    # Remove #id: lines
    text = re.sub(r"^\s*#id:\s*\w+\s*$", "", text, flags=re.MULTILINE)
    # Remove #since: lines
    text = re.sub(r"^\s*#since:.*$", "", text, flags=re.MULTILINE)

    # Inline code `text` -> text
    text = re.sub(r"`([^`]*)`", r"\1", text)

    # _italic_ -> italic (only for _word_)
    text = re.sub(r"\b_([^_]+)_\b", r"\1", text)
    # *bold* -> bold
    text = re.sub(r"\*([^*]+)\*", r"\1", text)

    # NOTE: / TIP: / WARNING: blocks (standalone on a line)
    text = re.sub(r"^NOTE:\s*$", "NOTE:", text, flags=re.MULTILINE)
    text = re.sub(r"^TIP:\s*$", "TIP:", text, flags=re.MULTILINE)
    text = re.sub(r"^WARNING:\s*$", "WARNING:", text, flags=re.MULTILINE)

    # | table separator lines -> just the text
    # "value" | description  ->  value: description
    text = re.sub(r'^\s*"?([^"|]+)"?\s*\|\s*$', r"  \1:", text, flags=re.MULTILINE)

    # Clean up remaining : prefixed tags like :null:
    text = re.sub(r":null:\s*", "", text)

    # Bullet lists: * item -> - item
    text = re.sub(r"^(\s*)\*\s+", r"\1- ", text, flags=re.MULTILINE)

    return text


def _is_structural_line(line):
    """Return True if this line should NOT be joined with the previous one."""
    stripped = line.strip()
    if not stripped:
        return True  # blank line = paragraph break
    if stripped.startswith("USAGES:"):
        return True
    # Lines that are part of a USAGES block (signatures)
    # Heuristic: looks like a type + funcname(
    if re.match(r"^(int|float|void|string|vector|matrix|bsdf|<)\S*\s+\w+\(", stripped):
        return True
    # Also array return types like int[]
    if re.match(r"^\w+\[\]\s+\w+\(", stripped):
        return True
    # Label lines: "word:" at start (Returns:, NOTE:, name:, <geometry>:, etc.)
    if re.match(r"^[\w&`<>]+:", stripped) and not stripped.endswith(":."):
        return True
    # Bullet list items
    if stripped.startswith("- "):
        return True
    return False


def join_paragraph_lines(text):
    """Join continuation lines within paragraphs into single lines."""
    lines = text.split("\n")
    result = []
    for line in lines:
        if _is_structural_line(line):
            result.append(line)
        elif result and not _is_structural_line(result[-1]) and result[-1].strip():
            # Previous line is also a continuation line — join
            result[-1] = result[-1].rstrip() + " " + line.strip()
        else:
            result.append(line)
    return "\n".join(result)


def parse_vex_function(name, content, files):
    """Parse a VEX function help file and return (funcname, description) or None."""
    lines = content.split("\n")

    # Must start with = funcname =
    title_match = re.match(r"^=\s+(\w+)\s+=\s*$", lines[0])
    if not title_match:
        return None

    funcname = title_match.group(1)

    # Must have #type: vex
    if not re.search(r"^#type:\s*vex\s*$", content, re.MULTILINE):
        return None

    # Extract the brief description from """..."""
    brief = ""
    brief_match = re.search(r'"""(.+?)"""', content, re.DOTALL)
    if brief_match:
        brief = brief_match.group(1).strip()

    # Collect usage lines (handle <<var>> inside backticks, optional trailing colon)
    usages = []
    for m in re.finditer(r":usage:\s*`([^`]+)`:?", content):
        sig = m.group(1)
        # Clean <<var>> -> var in signatures
        sig = re.sub(r"<<(\w+)>>", r"\1", sig)
        usages.append(sig)

    # Extract body: everything after the header block until @examples or @related or @subtopics
    # Header = title + #key: value lines + """brief"""
    body_start = 0
    has_brief = '"""' in content
    if has_brief:
        past_brief = False
        for i, line in enumerate(lines):
            if '"""' in line and not past_brief:
                past_brief = True
                # Check if brief is single line """text"""
                if line.count('"""') == 2:
                    body_start = i + 1
                    break
                continue
            if past_brief and '"""' in line:
                body_start = i + 1
                break
    else:
        # No brief - body starts after header (#key: value lines)
        for i, line in enumerate(lines):
            if i == 0:
                continue  # skip title
            if line.startswith("#") or line.strip() == "":
                continue
            body_start = i
            break

    # Find where body ends (before @examples, @related, @subtopics)
    body_end = len(lines)
    for i in range(body_start, len(lines)):
        if re.match(r"^@(examples|related|subtopics)\b", lines[i]):
            body_end = i
            break

    body_text = "\n".join(lines[body_start:body_end])

    # Process includes in body
    body_text = process_includes(body_text, files)

    # Remove usage lines from body (we handle them separately)
    body_text = re.sub(r"^:usage:\s*`[^`]+`:?\s*$", "", body_text, flags=re.MULTILINE)

    # Strip markup
    body_text = strip_houdini_markup(body_text)
    brief = strip_houdini_markup(brief)

    # Build the description
    desc_parts = []
    if brief:
        desc_parts.append(brief)

    if usages:
        desc_parts.append("")
        desc_parts.append("USAGES:")
        for u in usages:
            desc_parts.append(u)

    # Add body if it has content
    body_cleaned = "\n".join(
        line for line in body_text.split("\n")
    ).strip()

    if body_cleaned:
        desc_parts.append("")
        desc_parts.append(body_cleaned)

    description = "\n".join(desc_parts)

    # Clean up excessive blank lines
    description = re.sub(r"\n{3,}", "\n\n", description)
    # Strip leading and trailing whitespace per line
    description = "\n".join(line.strip() for line in description.split("\n"))
    description = description.strip()

    # Join continuation lines within text paragraphs.
    # A blank line separates paragraphs. Lines within a paragraph that are
    # plain text (not USAGES entries, not labels like "Returns:", "NOTE:", etc.)
    # get joined with a space.
    description = join_paragraph_lines(description)

    return funcname, description


def main():
    hfs = os.environ.get("HFS")
    if not hfs:
        print("Error: $HFS environment variable not set", file=sys.stderr)
        sys.exit(1)

    zip_path = os.path.join(hfs, "houdini", "help", "vex.zip")
    if not os.path.exists(zip_path):
        print(f"Error: {zip_path} not found", file=sys.stderr)
        sys.exit(1)

    files = load_zip(zip_path)

    snippets = {}
    func_files = sorted(
        name for name in files
        if name.startswith("functions/")
        and name.endswith(".txt")
        and not name.startswith("functions/_")
    )

    for name in func_files:
        content = files[name]
        result = parse_vex_function(name, content, files)
        if result is None:
            continue
        funcname, description = result
        snippets[funcname] = {
            "body": [funcname + "($0)"],
            "description": description,
        }

    script_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(script_dir, "snippets", "vex.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with open(out_path, "w") as f:
        json.dump(snippets, f, indent=2, ensure_ascii=False)

    print(f"Generated {len(snippets)} snippets -> {out_path}")


if __name__ == "__main__":
    main()
