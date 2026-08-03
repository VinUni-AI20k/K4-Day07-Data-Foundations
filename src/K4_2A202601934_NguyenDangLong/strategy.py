"""Heading-aware strategy owned by Nguyen Dang Long."""

from .chunking import RecursiveChunker


class HeadingRecursiveChunker(RecursiveChunker):
    """Preserve Markdown headings while recursively splitting long sections."""

    def chunk(self, text: str) -> list[str]:
        sections = []
        current_heading = ""
        body = []
        for line in text.splitlines():
            if line.lstrip().startswith("#"):
                if body:
                    sections.extend(self._with_heading(current_heading, "\n".join(body)))
                    body = []
                current_heading = line.strip()
            else:
                body.append(line)
        if body:
            sections.extend(self._with_heading(current_heading, "\n".join(body)))
        return [part for part in sections if part]

    def _with_heading(self, heading: str, body: str) -> list[str]:
        chunks = super().chunk(body)
        return [f"{heading}\n{chunk}".strip() if heading else chunk for chunk in chunks]
