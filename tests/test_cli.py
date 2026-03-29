from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
from stale_obsidian_note_detector.logic import app, display_report, count_links
from stale_obsidian_note_detector.schema import StaleReport, StaleCandidate, StaleAction

runner = CliRunner()

def test_count_links():
    assert count_links("No links") == 0
    assert count_links("One [[link]] here") == 1
    assert count_links("[[link1]] and [[link2]]") == 2

def test_display_report(capsys):
    report = StaleReport(
        candidates=[
            StaleCandidate(
                file_path="note1.md",
                reason="outdated",
                suggested_action=StaleAction.ARCHIVE,
                confidence=0.9
            )
        ]
    )
    display_report(report)
    captured = capsys.readouterr()
    assert "Stale Note Candidates" in captured.out
    assert "ARCHIVE" in captured.out
    assert "outdated" in captured.out

def test_display_report_empty(capsys):
    report = StaleReport(candidates=[])
    display_report(report)
    captured = capsys.readouterr()
    assert "No stale notes found!" in captured.out

@patch("stale_obsidian_note_detector.logic.resolve_provider")
@patch("stale_obsidian_note_detector.logic.timed_run")
@patch("os.getenv")
def test_analyze_command(mock_getenv, mock_timed_run, mock_resolve_provider, tmp_path):
    vault_path = tmp_path / "vault"
    vault_path.mkdir()
    note_path = vault_path / "stale.md"
    note_path.write_text("---\ntitle: Stale Note\n---\nOld content.")
    
    # Set mtime to 1 year ago
    import os
    import time
    past_time = time.time() - (365 * 24 * 60 * 60)
    os.utime(note_path, (past_time, past_time))
    
    mock_getenv.return_value = str(vault_path)
    
    mock_llm = MagicMock()
    mock_llm.model = "mock-model"
    mock_llm.complete.return_value = StaleReport(
        candidates=[
            StaleCandidate(
                file_path="stale.md",
                reason="very old",
                suggested_action=StaleAction.ARCHIVE,
                confidence=0.8
            )
        ]
    )
    mock_resolve_provider.return_value = mock_llm
    mock_timed_run.return_value.__enter__.return_value = MagicMock()
    
    result = runner.invoke(app, ["--no-llm", "--months", "6"])
    
    assert result.exit_code == 0
    assert "Stale Note Candidates" in result.stdout
    assert "ARCHIVE" in result.stdout
