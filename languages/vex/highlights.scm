; highlights.scm — Tree-sitter highlight queries for Houdini VEX

; ── Comments ──────────────────────────────────────────────

(comment) @comment

; ── Preprocessor ──────────────────────────────────────────

(preprocessor
  "#" @keyword.directive
  directive: (preprocessor_directive) @keyword.directive)

(preprocessor
  argument: (preprocessor_arg) @string)

; ── Literals ──────────────────────────────────────────────

(number_literal) @number

(string_literal) @string
(string_content) @string
(escape_sequence) @string.escape

; ── Types ─────────────────────────────────────────────────

(primitive_type) @type.builtin
(type_identifier) @type

; ── Keywords ──────────────────────────────────────────────

"function" @keyword.function
"struct" @keyword.type

"if" @keyword.conditional
"else" @keyword.conditional

"for" @keyword.repeat
"foreach" @keyword.repeat
"while" @keyword.repeat
"do" @keyword.repeat

"return" @keyword.return
"break" @keyword
"continue" @keyword

"export" @keyword.modifier
"const" @keyword.modifier

; ── Functions ─────────────────────────────────────────────

(function_declaration
  name: (identifier) @function)

(call_expression
  function: (identifier) @function.call)

(call_expression
  function: (member_expression
    member: (identifier) @function.method.call))

; ── Structs ───────────────────────────────────────────────

(struct_declaration
  name: (identifier) @type.definition)

(struct_field
  name: (identifier) @variable.special)

; ── Variables & parameters ────────────────────────────────

(variable_declarator
  name: (identifier) @variable)

(parameter_declarator
  name: (identifier) @variable.parameter)

; ── Member access ─────────────────────────────────────────

(member_expression
  member: (identifier) @variable.special)

; ── Geometry attributes (VEX-specific) ────────────────────

(attribute_access
  type_hint: (attribute_type_hint) @attribute)

(attribute_access
  "@" @attribute)

(attribute_access
  name: (identifier) @attribute)

; ── Operators ─────────────────────────────────────────────

[
  "="
  "+="
  "-="
  "*="
  "/="
  "%="
  "<<="
  ">>="
  "&="
  "|="
  "^="
] @operator

[
  "+"
  "-"
  "*"
  "/"
  "%"
] @operator

[
  "=="
  "!="
  "<"
  ">"
  "<="
  ">="
] @operator

[
  "&&"
  "||"
  "!"
] @operator

[
  "&"
  "|"
  "^"
  "~"
  "<<"
  ">>"
] @operator

[
  "++"
  "--"
] @operator

"?" @operator
":" @operator

; ── Punctuation ───────────────────────────────────────────

["(" ")"] @punctuation.bracket
["[" "]"] @punctuation.bracket
["{" "}"] @punctuation.bracket

";" @punctuation.delimiter
"," @punctuation.delimiter
"." @punctuation.delimiter
"->" @punctuation.delimiter
