import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Annotated, Optional

import typer
import frontmatter
from rich.console import Console
from rich.table import Table

from local_first_common.providers import PROVIDERS
from local_first_common.cli import (
    init_config_option,
    provider_option,
    model_option,
    dry_run_option,
    no_llm_option,
    verbose_option,
    debug_option,
    resolve_provider,
    resolve_dry_run,
)
from local_first_common.config import get_setting
from local_first_common.tracking import register_tool, timed_run

from .schema import StaleReport, StaleAction
from .prompts import build_system_prompt, build_user_prompt

TOOL_NAME = "stale-obsidian-note-detector"


class StaleDetectorError(Exception):
    """Base typed error for stale-obsidian-note-detector."""


class ProviderSetupError(StaleDetectorError):
    """Raised when provider resolution fails."""


class LLMRunError(StaleDetectorError):
    """Raised when the LLM analysis call fails."""
DEFAULTS = {"provider": "ollama", "model": "llama3"}
_TOOL = register_tool(TOOL_NAME)

console = Console()
app = typer.Typer(help="Finds signals of staleness and suggests cleanup actions.")

def count_links(content: str) -> int:
    """Simple regex count of wiki-style [[links]]."""
    return len(re.findall(r"\[\[.*?\]\]", content))

def display_report(report: StaleReport):
    """Rich display of stale note candidates."""
    if not report.candidates:
        console.print("[green]No stale notes found![/green]")
        return

    table = Table(title="Stale Note Candidates")
    table.add_column("File", style="cyan")
    table.add_column("Action", style="bold yellow")
    table.add_column("Confidence", style="dim")
    table.add_column("Reason")

    for c in report.candidates:
        if c.suggested_action == StaleAction.KEEP:
            continue
        table.add_row(
            os.path.basename(c.file_path),
            c.suggested_action.value.upper(),
            f"{c.confidence:.2f}",
            c.reason
        )
    console.print(table)

@app.command()
def analyze(
    months: int = typer.Option(6, "--months", help="Months of inactivity to flag."),
    limit: int = typer.Option(20, "--limit", "-l", help="Limit number of files to process."),
    provider: Annotated[str, provider_option(PROVIDERS)] = os.environ.get("MODEL_PROVIDER", "ollama"),
    model: Annotated[Optional[str], model_option()] = None,
    dry_run: Annotated[bool, dry_run_option()] = False,
    no_llm: Annotated[bool, no_llm_option()] = False,
    verbose: Annotated[bool, verbose_option()] = False,
    debug: Annotated[bool, debug_option()] = False,
    init_config: Annotated[bool, init_config_option(TOOL_NAME, DEFAULTS)] = False,
):
    """Analyze vault for stale notes."""
    dry_run = resolve_dry_run(dry_run, no_llm)

    vault_path_str = os.getenv("OBSIDIAN_VAULT_PATH")
    if not vault_path_str:
        console.print("[red]Error: OBSIDIAN_VAULT_PATH environment variable not set.[/red]")
        raise typer.Exit(1)
    
    vault_path = Path(vault_path_str)
    cutoff_date = datetime.now() - timedelta(days=30 * months)

    # 1. Heuristic filtering (modified date, link density)
    candidates_metadata = []
    for root, _, files in os.walk(vault_path):
        # Skip existing archive folders
        if "Archive" in root or "DeepArchive" in root or ".git" in root:
            continue
            
        for file in files:
            if file.endswith(".md"):
                file_path = Path(root) / file
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                if mtime < cutoff_date:
                    try:
                        post = frontmatter.load(file_path)
                        link_count = count_links(post.content)
                        
                        candidates_metadata.append({
                            "path": str(file_path.relative_to(vault_path)),
                            "modified": mtime.strftime("%Y-%m-%d"),
                            "link_count": link_count,
                            "content": post.content[:1000]
                        })
                    except Exception:
                        continue
                
                if len(candidates_metadata) >= limit:
                    break
        if len(candidates_metadata) >= limit:
            break

    if not candidates_metadata:
        console.print(f"[green]No notes found modified before {cutoff_date.date()}.[/green]")
        return

    # 2. LLM Review
    try:
        actual_provider = get_setting(TOOL_NAME, "provider", cli_val=provider, default="ollama")
        actual_model = get_setting(TOOL_NAME, "model", cli_val=model)
        llm = resolve_provider(PROVIDERS, actual_provider, actual_model, debug=debug, no_llm=no_llm)
    except StaleDetectorError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    system = build_system_prompt()
    user = build_user_prompt(candidates_metadata)

    try:
        with timed_run("stale-obsidian-note-detector", llm.model, source_location=str(vault_path)) as run:
            response = llm.complete(system, user, response_model=StaleReport)
            result = response
            run.item_count = len(candidates_metadata)
    except LLMRunError as e:
        console.print(f"[red]Error during LLM processing: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error during LLM processing: {e}[/red]")
        raise typer.Exit(1)

    display_report(result)

    if dry_run:
        console.print("\n[yellow][dry-run] Analysis complete. No files moved.[/yellow]")
    else:
        # Final confirmation before moving?
        console.print("\n[bold]Note:[/bold] File movement (archive/deep archive) requires 'apply' command (not implemented).")

if __name__ == "__main__":
    app()
