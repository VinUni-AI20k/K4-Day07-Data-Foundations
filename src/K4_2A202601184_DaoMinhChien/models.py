from dataclasses import dataclass, field


@dataclass
class Document:
    """A text document with a unique identifier and optional metadata."""

    id: str
    content: str
    metadata: dict = field(default_factory=dict)
