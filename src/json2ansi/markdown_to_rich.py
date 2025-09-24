import re
from typing import List, Optional
from dataclasses import dataclass
from rich.text import Text

@dataclass
class Token:
    """Represents a piece of text with an optional Rich style."""
    text: str
    style: Optional[str] = None

class MarkdownParser:
    """
    Parses inline Markdown syntax into Rich Text objects.
    
    Supports:
        - Bold: **text**
        - Italic: *text*
        - Bold + Italic: ***text***
        - Strikethrough: ~~text~~
        - Underline: __text__
        - Links: [text](url)
        - Nested italic inside bold
    """

    # Patterns in order of precedence
    PATTERNS = [
        (re.compile(r'\*\*\*(.+?)\*\*\*'), 'bold italic'),  # ***bold+italic***
        (re.compile(r'\*\*(.+?)\*\*'), 'bold'),            # **bold**
        (re.compile(r'\*(.+?)\*'), 'italic'),              # *italic*
        (re.compile(r'~~(.+?)~~'), 'strike'),              # ~~strike~~
        (re.compile(r'__(.+?)__'), 'underline'),           # __underline__
        (re.compile(r'\[(.+?)\]\((.+?)\)'), 'link'),       # [text](url)
    ]

    def parse_inline(self, md: str) -> List[Token]:
        """
        Parse inline Markdown into a list of Tokens.

        Args:
            md (str): Markdown string.

        Returns:
            List[Token]: List of Token objects with text and style.
        """
        if not md:
            return []

        # Find first match among all patterns
        first_match = None
        first_style = None
        for pattern, style in self.PATTERNS:
            match = pattern.search(md)
            if match and (first_match is None or match.start() < first_match.start()):
                first_match = match
                first_style = style

        if not first_match:
            return [Token(md)]

        tokens: List[Token] = []
        start, end = first_match.span()
        if start > 0:
            tokens.extend(self.parse_inline(md[:start]))

        inner_text = first_match.group(1)

        # Handle special cases
        if first_style == 'bold':
            tokens.extend(self.handle_bold(inner_text))
        elif first_style == 'link':
            tokens.extend(self.handle_link(inner_text, first_match.group(2)))
        else:
            inner_tokens = self.parse_inline(inner_text)
            for t in inner_tokens:
                t.style = first_style if t.style is None else f'{t.style} {first_style}'
            tokens.extend(inner_tokens)

        if end < len(md):
            tokens.extend(self.parse_inline(md[end:]))

        return tokens

    def handle_bold(self, inner_text: str) -> List[Token]:
        """
        Handle bold text and nested italic inside it.

        Args:
            inner_text (str): Text inside bold markers.

        Returns:
            List[Token]: Tokens with bold (and nested italic) styles applied.
        """
        tokens: List[Token] = []
        pos = 0
        for m in re.finditer(r'\*(.+?)\*', inner_text):
            s, e = m.span()
            if s > pos:
                tokens.append(Token(inner_text[pos:s], style='bold'))
            tokens.append(Token(m.group(1), style='bold italic'))
            pos = e
        if pos < len(inner_text):
            tokens.append(Token(inner_text[pos:], style='bold'))
        return tokens

    def handle_link(self, inner_text: str, url: str) -> List[Token]:
        """
        Handle link text, possibly with inner styles.

        Args:
            inner_text (str): Link display text.
            url (str): URL for the link.

        Returns:
            List[Token]: Tokens with link styles applied.
        """
        inner_tokens = self.parse_inline(inner_text)
        for t in inner_tokens:
            t.style = f'{t.style + " " if t.style else ""}link {url}'
        return inner_tokens

    def tokens_to_rich(self, tokens: List[Token]) -> Text:
        """
        Convert a list of Tokens into a Rich Text object.

        Args:
            tokens (List[Token]): Tokens to convert.

        Returns:
            Text: Rich Text object.
        """
        t = Text()
        for tok in tokens:
            t.append(tok.text, style=tok.style)
        return t



parser = MarkdownParser()

def md_to_rich_text(md_text: str) -> Text:
    """
    Convert a Markdown string to a Rich Text object.

    Args:
        md_text (str): Markdown string.

    Returns:
        Text: Rich Text object.
    """
    tokens = parser.parse_inline(md_text)
    return parser.tokens_to_rich(tokens)


