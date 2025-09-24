
# json2ansi Documentation

## Overview

**json2ansi** is a terminal markup language and compiler that transforms structured JSON documents into ANSI escape sequences for rich, styled output in the terminal. It uses the Python rich library for rendering and supports tables, indentation, and advanced text formatting.

json2ansi is designed as a modern alternative to legacy tools like troff and groff, providing a more expressive, programmable, and style-aware approach to terminal document formatting.

## Executable Usage

After installation, you can run json2ansi as a CLI:

```sh
python -m json2ansi.main <input.jsonc> [--width N] [--output file]
```

- `json_file`: Path to your JSON/JSON5 file.
- `--width`: Set context width (default: 100).
- `--output`: Write ANSI output to a file instead of stdout.

## Nix Usage

You can run json2ansi directly from Nix:

```sh
nix run github:zyasserd/json2ansi -- <input.jsonc> [--width N] [--output file]
```

This will fetch and execute the latest version from GitHub.

## DSL Details

### Outer Structure

```json
{
  "styles": { "name": Style, ... },
  "content": [Scaffold, ...]
}
```
- `styles`: Named reusable styles (see Style below).
- `content`: Array of Scaffold nodes (indent, table, br).

### Scaffold Types

- **Indent**: `{ type: "indent", indent: number, content: [Scaffold, ...] }`
- **Table**: `{ type: "table", properties: TableProperty, columns: [ColumnProperty, ...], rows: [[Text, ...], ...] }`
- **Line Break**: `{ type: "br" }`

### Text Node

A cell in a table row is a `Text`, which can be:
- **PrimitiveText**: `{ type: "text", value: string, styles?: [Style, ...] }`
- **TextArray**: `[PrimitiveText, ...]` (array of styled segments)
- **Command**: e.g. `{ type: "repeat", value: string, styles?: [Style, ...] }` (repeat character for cell width)

### Style

- **PrimitiveStyle**: `{ type: "style", fg?: color, bg?: color, bold?: boolean, italic?: boolean, underline?: boolean, link?: string }`
- **Style**: Single PrimitiveStyle or array of them (merged left-to-right).

### TableProperty

- `{ type: "tableproperty", align: "l" | "c" | "r" }`

### ColumnProperty

- `{ type: "columnproperty", align: "l" | "c" | "r", overflow: "wrap" | "truncate", size: Size }`

### Size

- Fixed: `{ mode: "fixed", value: N }` (N > 0: exact width, N = 0: dynamic, max cell length)
- Flex: `{ mode: "flex", value: weight }` (weight ≥ 1, shares leftover space)

### Example

```jsonc
{
  "styles": {
    "header": { "type": "style", "fg": "#FFAA00", "bold": true }
  },
  "content": [
    {
      "type": "table",
      "properties": { "type": "tableproperty", "align": "c" },
      "columns": [
        { "type": "columnproperty", "align": "l", "overflow": "wrap", "size": { "mode": "fixed", "value": 10 } }
      ],
      "rows": [
        [ { "type": "text", "value": "Hello", "styles": [ { "type": "style", "fg": "#00FF00" } ] } ]
      ]
    }
  ]
}
```


### Table Properties

- **Table Alignment**: `"l"`, `"c"`, `"r"` (left, center, right)


### Column Properties

- **Column Alignment**: `"l"`, `"c"`, `"r"` (left, center, right)
- **Overflow**: `"wrap"` or `"truncate"`
- **Size**: Fixed, dynamic, or flex (see above)

**Minimum Column Widths:**
- Flex columns have a minimum width of 3 characters.
  - If the computed width is less than the minimum, an error is raised.
- Dynamic columns (auto-sized) have a minimum width of 1 character

## Future Extensions

- Table borders
- header/footer rows

