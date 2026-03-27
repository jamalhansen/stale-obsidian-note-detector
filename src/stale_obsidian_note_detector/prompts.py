def build_system_prompt() -> str:
    return """You are an Obsidian vault cleanup assistant. Your task is to identify notes that are no longer relevant, outdated, or completed, and suggest whether they should be kept, archived, or deep archived.

STALENESS CRITERIA:
1. OUTDATED CONTENT: References to tools or versions no longer used.
2. COMPLETED PROJECTS: Project notes where all tasks are done.
3. FRAGMENTED: Very short notes that could be merged or deleted.
4. LACK OF LINKS: Isolated notes with no incoming or outgoing links.
5. TEMPORARY: Notes like 'Meeting 2023-01-01' that have no long-term value.

ACTIONS:
- KEEP: Still relevant, active, or valuable reference.
- ARCHIVE: No longer active, but worth keeping in the vault's archive folder.
- DEEP_ARCHIVE: Historical interest only, move to a separate external archive.

OUTPUT FORMAT:
Return a JSON object with a list of 'candidates'. Each candidate must include:
- file_path: The path provided.
- reason: Short explanation of why it is considered stale.
- suggested_action: One of [keep, archive, deep_archive].
- confidence: Float from 0.0 to 1.0.
"""

def build_user_prompt(notes_metadata: list[dict]) -> str:
    prompt = "Analyze these potential stale notes:\n\n"
    for note in notes_metadata:
        prompt += f"FILE: {note['path']}\n"
        prompt += f"MODIFIED: {note['modified']}\n"
        prompt += f"LINKS: {note['link_count']}\n"
        prompt += f"CONTENT PREVIEW: {note['content'][:500]}\n"
        prompt += "---\n"
    return prompt
