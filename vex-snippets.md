# VEX Snippets Generation

## Source

`$HFS/houdini/help/vex.zip` — Houdini's built-in VEX help archive.

The `functions/` directory contains one `.txt` file per function in Houdini wiki markup format.

## Filtering

A file is a VEX function if:
- First line is `= funcname =`
- Has `#type: vex` attribute

Files starting with `_` are include files (e.g. `_common.txt`, `_area_variadic.txt`), not functions.

## Include resolution

Files use `:include` directives in two forms:
- `:include _common#geohandle_arg:` — section by `#id:` from `functions/_common.txt`
- `:include /vex/functions/agentsolvefbik#targetxforms:` — absolute path within the zip (strip `/vex/`, add `.txt`)
- `:include _area_variadic:` — whole file (skip `#type: include` header)

Sections inside include files are delimited by `:arg:` / `:null:` / `:varg:` tags followed by `#id: name` lines, with indented body below. When resolved, the tag line is preserved (e.g. `:arg:geohandle:`) so it renders as an argument label (`geohandle:`) after markup stripping.

## Markup stripping

Houdini wiki markup converted to plain text:
- `[Vex:funcname]` → `funcname`
- `[text|/path]` → `text`
- `<<variable>>` → `variable`
- `:arg:name:` / `:arg:\`name\`:` / `::arg::name:` → `name:`
- `:box:`, `:tip:`, `:warning:`, `:note:` — removed
- `:returns:` → `Returns:`
- `{{{ }}}` code blocks and `#!vex` — removed
- `` `inline code` `` — backticks removed
- `#id:`, `#since:` lines — removed
- `* item` → `- item`

## Usage signatures

Lines like `:usage: \`int foo(float x)\`` are collected separately and formatted as:

```
USAGES:
int foo(float x)
int foo(float x, float y)
```

Some usages have `<<var>>` or a trailing colon after the backtick — both are handled.

## Paragraph joining

After markup stripping, continuation lines within text paragraphs are joined into single lines. Blank lines still separate paragraphs. Structural lines are never joined:
- USAGES header and signature lines
- Label lines (`Returns:`, `NOTE:`, `name:`, etc.)
- Bullet list items (`- ...`)
- Blank lines

This is done by `join_paragraph_lines()` / `_is_structural_line()`.

## Output

`snippets/vex.json` — one entry per function:

```json
"funcname": {
  "body": ["funcname($0)"],
  "description": "brief\n\nUSAGES:\nsig1\nsig2\n\nbody text..."
}
```

Description is: brief (`"""..."""`), then USAGES block, then body text (everything between brief and `@examples`/`@related`/`@subtopics`). Functions without a brief (like `max`) start body from after the header.

## Running

```
python3 gen_snippets.py
```

Requires `$HFS` to be set. Outputs to `snippets/vex.json`.
