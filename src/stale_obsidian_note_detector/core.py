"""Domain logic and errors for stale-obsidian-note-detector."""

import re


class StaleDetectorError(Exception):
    """Base typed error for stale-obsidian-note-detector."""


class ProviderSetupError(StaleDetectorError):
    """Raised when provider resolution fails."""


class LLMRunError(StaleDetectorError):
    """Raised when the LLM analysis call fails."""


def count_links(content: str) -> int:
    """Simple regex count of wiki-style [[links]]."""
    return len(re.findall(r"\[\[.*?\]\]", content))
