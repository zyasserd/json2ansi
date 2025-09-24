import json
import json5
import sys
from pathlib import Path
import jsonref
from jsonschema import Draft7Validator, validators
from rich.console import Console
from rich.table import Table, Column
from rich.text import Text
from rich.padding import Padding
from rich.markdown import Markdown
from rich import box


MIN_COLUMN_WIDTH = 3
DEFAULT_CONTEXT_WIDTH = 80

SCHEMA_FILE = Path("schema.json")
SCHEMA = json.loads(SCHEMA_FILE.read_text())

console = Console()

# --- Extend validator to set defaults ---
def extend_with_default(validator_class):
    validate_props = validator_class.VALIDATORS["properties"]

    def set_defaults(validator, properties, instance, schema):
        for prop, subschema in properties.items():
            if "default" in subschema:
                # Only set default if key is missing
                instance.setdefault(prop, subschema["default"])

        # Continue validation as normal
        for error in validate_props(validator, properties, instance, schema):
            yield error

    return validators.extend(
        validator_class, {"properties": set_defaults},
    )

DefaultValidatingDraft7Validator = extend_with_default(Draft7Validator)

def load_json5_with_refs(path: str):
    """
    Load a JSON/JSON5 file and expand $ref references.

    Uses json5 to allow trailing commas and other JSON5 features,
    then normalizes to strict JSON for jsonref.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json5.load(f)

    json_str = json.dumps(data)

    # expands $ref
    return jsonref.loads(json_str, jsonschema=True)

def load_and_validate(file_path: str):
    """Load JSON, expand $ref, validate against schema, apply defaults."""
    data = load_json5_with_refs(file_path)

    validator = DefaultValidatingDraft7Validator(SCHEMA)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    if errors:
        for error in errors:
            print(f"Validation error at {list(error.path)}: {error.message}")
        sys.exit(1)
    return data

def style_to_rich(style_obj):
    """Convert style dict into Rich style string."""
    fg = style_obj.get("fg") or None
    bg = style_obj.get("bg") or None
    parts = []
    if fg: parts.append(f"{fg}")
    if bg: parts.append(f"on {bg}")
    if style_obj.get("bold"): parts.append("bold")
    if style_obj.get("italic"): parts.append("italic")
    if style_obj.get("underline"): parts.append("underline")
    if style_obj.get("link"):
        parts.append(f"link {style_obj['link']}")
    return " ".join(parts)

def combine_styles(styles):
    """
    Combine a list of style dicts into one, with later dicts overriding earlier ones.
    """
    result = {}
    for style in styles:
        result.update(style)
    return result

def render_text(node, column_width):
    """Render styled text or command node to Rich Text (no overflow here)."""
    match node:
        case {"type": "text", "value": val, **rest}:
            txt = Text(val)
            # TODO: add markdown support
            styles = rest.get("styles", [])
            if styles:
                combined = combine_styles(styles)
                txt.stylize(style_to_rich(combined))

        case {"type": "repeat", "value": val, **rest}:
            # Fill logic is done at table level via width
            txt = Text(val * column_width)

            styles = rest.get("styles", [])
            if styles:
                combined = combine_styles(styles)
                txt.stylize(style_to_rich(combined))

        case list() if all(seg.get("type") == "text" for seg in node):
            # textArray: merge styled segments
            txt = Text()
            for seg in node:
                seg_txt = render_text(seg, column_width)
                txt.append(seg_txt)

        case _:
            raise ValueError(f"Unknown text type")

    return txt


def calc_dynamic_width(rows, col_idx):
    max_len = MIN_COLUMN_WIDTH
    for row in rows:
        cell = row[col_idx]
        match cell:
            case {"type": "text", "value": val}:
                max_len = max(max_len, len(str(val)))
            case {"type": "repeat", "value": val}:
                max_len = max(max_len, len(str(val)))
            case list() if all(isinstance(seg, dict) and seg.get("type") == "text" for seg in cell):
                val = "".join(seg["value"] for seg in cell)
                max_len = max(max_len, len(val))
            case _:
                raise ValueError(f"Unknown cell type for dynamic width: {cell}")
    return max_len


def compute_column_widths(columns, rows, context_width, indent):
    """Compute column widths for a table given columns, rows, context width, and indent."""
    effective_width = max(context_width - indent, MIN_COLUMN_WIDTH)
    num_cols = len(columns)
    total_separators = num_cols - 1

    # Pass 1: Set fixed and dynamic widths, flex stays None
    col_widths = [None] * num_cols
    flex_indices = []
    flex_weights = []
    for i, col in enumerate(columns):
        size = col["size"]
        match size:
            case {"mode": "fixed", "value": v} if v > 0:
                col_widths[i] = max(v, MIN_COLUMN_WIDTH)
            case {"mode": "fixed", "value": 0}:
                col_widths[i] = max(calc_dynamic_width(rows, i), MIN_COLUMN_WIDTH)
            case {"mode": "flex", "value": w}:
                flex_indices.append(i)
                flex_weights.append(w)
            case _:
                raise ValueError(f"Unknown or invalid size spec: {size}")

    # Pass 2: Compute flex widths
    used_width = sum(w for w in col_widths if w is not None) + total_separators
    remaining = effective_width - used_width
    if flex_indices:
        total_weight = sum(flex_weights)
        for idx, i in enumerate(flex_indices):
            w = int(remaining * (flex_weights[idx] / total_weight))
            col_widths[i] = max(w, MIN_COLUMN_WIDTH)
    used_width = sum(col_widths) + total_separators

    # Error if table cannot fit
    if used_width > effective_width:
        raise ValueError(f"Table width {used_width} exceeds context width {effective_width}")
    
    return col_widths


def render_table(node, indent=0, context_width=DEFAULT_CONTEXT_WIDTH):
    """Render a table node to a Rich Table, aware of context width and column sizing."""
    columns = node["columns"]
    rows = node["rows"]
    col_widths = compute_column_widths(columns, rows, context_width, indent)


    table = Table(
        padding=(0, 1, 0, 0),
        collapse_padding=True,
        pad_edge=False,
        expand=False,
        box=None,
        show_edge=False,
        show_header=False,
        show_footer=False,
    )
    # TODO: can you change the padding character?

    # Configure columns
    for i, col in enumerate(columns):
        justify = {"l": "left", "c": "center", "r": "right"}[col["align"]]
        no_wrap = col["overflow"] == "truncate"

        table.add_column(
            justify=justify,
            width=col_widths[i],
            no_wrap=no_wrap,
            overflow="ellipsis",
        )

    # Add rows
    for row in rows:
        cells = []
        for col_index, cell in enumerate(row):
            cells.append(render_text(cell, col_widths[col_index]))
        table.add_row(*cells)

    console.print(
        Padding(table, (0, 0, 0, indent)),
        justify={"l": "left", "c": "center", "r": "right"}[node["properties"]["align"]],
        width=context_width
    )


def render_scaffold(node, indent=0, context_width=None):
    if node["type"] == "indent":
        child_indent = indent + node["indent"]
        for child in node["content"]:
            render_scaffold(child, indent=child_indent, context_width=context_width)

    elif node["type"] == "table":
        render_table(node, indent=indent, context_width=context_width)

def render_document(doc, context_width=None):
    for node in doc["content"]:
        render_scaffold(node, indent=0, context_width=context_width)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Render JSON to ANSI table")
    parser.add_argument("json_file", help="Path to JSON file")
    parser.add_argument("--width", type=int, default=DEFAULT_CONTEXT_WIDTH, help="Global context width")
    args = parser.parse_args()

    doc = load_and_validate(args.json_file)
    print("-"*DEFAULT_CONTEXT_WIDTH)
    render_document(doc, context_width=args.width)
