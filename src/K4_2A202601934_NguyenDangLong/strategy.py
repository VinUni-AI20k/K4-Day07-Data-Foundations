"""Heading-aware strategy owned by Nguyen Dang Long."""

from .chunking import RecursiveChunker


class HeadingRecursiveChunker(RecursiveChunker):
    """Preserve Markdown headings while recursively splitting long sections."""

    def chunk(self, text: str) -> list[str]:
        sections = []
        heading_path: list[str] = []
        body = []
        for line in text.splitlines():
            if line.lstrip().startswith("#"):
                if body:
                    sections.extend(self._with_heading(heading_path, "\n".join(body)))
                    body = []
                heading = line.strip()
                level = len(heading) - len(heading.lstrip("#"))
                heading_path = heading_path[: max(0, level - 1)]
                heading_path.append(heading)
            else:
                body.append(line)
        if body:
            sections.extend(self._with_heading(heading_path, "\n".join(body)))
        return [part for part in sections if part]

    def _with_heading(self, heading_path: list[str], body: str) -> list[str]:
        heading = "\n".join(heading_path)
        chunks = super().chunk(body)
        return [f"{heading}\n{chunk}".strip() if heading else chunk for chunk in chunks]
