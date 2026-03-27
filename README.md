# Stale Obsidian Note Detector

Finds signals of staleness—outdated content, missing links, references to completed projects—and suggests cleanup actions.

## Features
- **Heuristic Filtering**: Flags notes modified months ago with low link density.
- **LLM Review**: Deeply analyzes content to differentiate between high-value references and stale candidates.
- **Categorization**: Suggests 'KEEP', 'ARCHIVE', or 'DEEP_ARCHIVE'.
- **Safe Mode**: Always runs in analysis mode first to prevent accidental data loss.

## Installation
```bash
uv sync
```

## Usage
```bash
export OBSIDIAN_VAULT_PATH="/path/to/your/vault"
uv run stale-note-detector analyze -m 12 -l 50
```

Standard flags supported: `--dry-run`, `--no-llm`, `--provider`, `--model`.
