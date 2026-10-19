import subprocess
import sys

import pytest

from kokorosay import cli, setup_cmd


@pytest.fixture
def check_call(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """Mock ``subprocess.check_call`` so UniDic is never actually downloaded."""
    calls: list[list[str]] = []

    def fake(cmd, *args, **kwargs):
        calls.append(list(cmd))
        return 0

    monkeypatch.setattr(subprocess, "check_call", fake)
    return calls


def test_setup_runs_unidic_download_with_sys_executable(check_call) -> None:
    assert cli.main(["--setup"]) == 0
    assert check_call == [[sys.executable, "-m", "unidic", "download"]]


def test_setup_child_failure_exits_1(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    def fake(cmd, *args, **kwargs):
        raise subprocess.CalledProcessError(3, cmd)

    monkeypatch.setattr(subprocess, "check_call", fake)
    assert cli.main(["--setup"]) == 1
    assert "UniDic download failed" in capsys.readouterr().err


def test_setup_cannot_start_child_exits_1(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    def fake(cmd, *args, **kwargs):
        raise FileNotFoundError("no such interpreter")

    monkeypatch.setattr(subprocess, "check_call", fake)
    assert setup_cmd.run_setup() == 1
    assert "could not start" in capsys.readouterr().err


@pytest.mark.parametrize(
    "argv",
    [
        ["--setup", "hello"],
        ["hello", "--setup"],
        ["--setup", "hello", "out.wav"],
        ["--setup", "--list-voices"],
        ["--setup", "-"],
    ],
)
def test_setup_combined_with_other_modes_is_usage_error(argv, check_call) -> None:
    with pytest.raises(SystemExit) as excinfo:
        cli.main(argv)
    assert excinfo.value.code == 2
    assert check_call == []


def test_setup_does_not_import_kokoro_or_torch(check_call) -> None:
    code = (
        "import sys, subprocess\n"
        "subprocess.check_call = lambda *a, **k: 0\n"
        "from kokorosay import cli\n"
        "rc = cli.main(['--setup'])\n"
        "assert rc == 0, rc\n"
        "assert 'kokoro' not in sys.modules\n"
        "assert 'torch' not in sys.modules\n"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
