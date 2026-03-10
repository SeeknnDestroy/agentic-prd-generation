"""Unit tests for the CLI entrypoint."""

from unittest.mock import patch

from backend.main import cli


def test_cli_invokes_uvicorn_with_expected_arguments() -> None:
    """The console entrypoint should delegate to Uvicorn."""
    with patch("backend.main.uvicorn.run") as mock_run:
        exit_code = cli(["--host", "127.0.0.1", "--port", "9001", "--no-reload"])

    assert exit_code == 0
    mock_run.assert_called_once_with(
        "backend.main:app",
        host="127.0.0.1",
        port=9001,
        reload=False,
    )
