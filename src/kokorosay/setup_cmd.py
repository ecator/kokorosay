"""Implementation of ``kokorosay --setup``: download the full UniDic dictionary."""

import subprocess
import sys


def unidic_download_command() -> list[str]:
    """Return the command that downloads UniDic into the current environment."""
    return [sys.executable, "-m", "unidic", "download"]


def run_setup() -> int:
    """Download the UniDic dictionary required by the Japanese G2P backend.

    Output of the child process goes straight to the terminal. Returns the
    process exit code for kokorosay: ``0`` on success, ``1`` on failure.
    """
    command = unidic_download_command()
    try:
        subprocess.check_call(command)
    except subprocess.CalledProcessError as exc:
        print(
            f"kokorosay: error: UniDic download failed (exit code {exc.returncode}).",
            file=sys.stderr,
        )
        return 1
    except OSError as exc:
        print(f"kokorosay: error: could not start UniDic download: {exc}", file=sys.stderr)
        return 1
    return 0
