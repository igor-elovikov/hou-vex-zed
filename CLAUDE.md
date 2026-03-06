# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Zed editor extension providing language support for Houdini VEX. Includes a Tree-sitter grammar (git submodule), syntax highlighting, bracket/indent rules, and auto-generated code snippets for built-in VEX functions.

Snippet generation requires a Houdini installation (`$HFS` env var):

```bash
python3 gen_snippets.py     # regenerates snippets/vex.json from $HFS/houdini/help/vex.zip
```

## Architecture

- **`extension.toml`** — Zed extension manifest
- **`grammars/vex/`** — Tree-sitter grammar submodule; `src/grammar.json` defines the parser rules, `grammar.js` is generated output
- **`languages/vex/`** — Zed language config:
  - `config.toml` — file extensions (`.vex`, `.vfl`), comment styles, autoclose settings
  - `highlights.scm` — Tree-sitter highlight queries (includes regex matching all VEX builtins)
  - `brackets.scm` / `indents.scm` — bracket matching and indentation rules
- **`snippets/vex.json`** — Auto-generated from Houdini help; do not edit manually
- **`gen_snippets.py`** — Parses Houdini's help zip to produce snippets with full function signatures and docs

## Key VEX Language Details

VEX has several unusual syntactic features encoded in the grammar:
- Optional `function` keyword on declarations
- Parameter groups sharing types: `func(int x, y)` with semicolon-separated groups
- Geometry attribute access with type hints: `f@mass`, `v@P`, `i@id`
- Both cast styles: `(float)x` and `float(x)`
- `foreach` with optional index variable
