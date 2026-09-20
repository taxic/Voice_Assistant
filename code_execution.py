# code_execution.py
"""Python code writing/execution for the voice assistant.

This is NOT a real sandbox - no container, no seccomp, no resource limits
beyond a subprocess timeout. The trust model is "the user's own request on
their own machine". The actual safety gate is the propose-then-confirm
flow: voice recognition can mishear things, and the LLM agent loop can
chain several tool calls within a single turn before the user gets to say
anything else - so a system-prompt instruction alone ("ask before running")
isn't a real guarantee. CodeExecutor enforces a minimum real-world gap
between proposing code and confirming it, which a same-turn tool-chaining
round trip (LLM inference only, no TTS/STT) can't satisfy but a genuine
"user heard the question and answered" round trip always will.
"""
import os
import re
import subprocess
import sys
import time
from datetime import datetime

from config_manager import config

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "scripts")

_FILENAME_RE = re.compile(r"^[A-Za-z0-9_\-]+\.py$")


def _safe_path(filename: str) -> str:
    """Resolve a filename to a path inside SCRIPTS_DIR, rejecting anything
    that isn't a bare '<name>.py' - no folders, no '..', no absolute paths.
    Raises ValueError (caller turns this into a spoken error) on anything
    suspicious rather than silently sanitizing it."""
    if not _FILENAME_RE.match(filename):
        raise ValueError(
            "filenames must be a simple name ending in .py (letters, numbers, "
            "underscores, hyphens only) - no folders or special characters."
        )
    return os.path.join(SCRIPTS_DIR, filename)


class CodeExecutor:
    """Holds at most one pending (proposed-but-not-yet-confirmed) execution
    at a time. This assistant is single-user/single-session, so one slot is
    enough - no need to track multiple concurrent proposals."""

    def __init__(self):
        os.makedirs(SCRIPTS_DIR, exist_ok=True)
        self._pending = None  # {"code": str, "description": str, "proposed_at": float}

    def write_file(self, filename: str, code: str, description: str = "") -> str:
        """Save code to a script file. No confirmation needed - writing a
        file can't do anything on its own, unlike running one."""
        path = _safe_path(filename)
        header = f"# {description}\n\n" if description else ""
        with open(path, "w", encoding="utf-8") as f:
            f.write(header + code)
        return f"Saved to scripts/{filename}."

    def propose_run(self, description: str, code: str = None, filename: str = None) -> str:
        """Stage code to run, but don't run it yet. Exactly one of `code` or
        `filename` (a previously-saved script) must be given."""
        if bool(code) == bool(filename):
            raise ValueError(
                "I need either the code to run or the name of a saved script - not both, not neither."
            )

        if filename:
            path = _safe_path(filename)
            if not os.path.exists(path):
                raise ValueError(f"there's no saved script called '{filename}'.")
            with open(path, "r", encoding="utf-8") as f:
                code = f.read()

        self._pending = {"code": code, "description": description, "proposed_at": time.time()}

        preview = code if len(code) <= 300 else code[:300] + "..."
        return (
            f"Staged, not run yet: {description}\n"
            f"---\n{preview}\n---\n"
            "This needs an explicit yes from the user in a later reply before calling confirm_run - "
            "not in this same turn."
        )

    def confirm_run(self) -> str:
        """Actually execute the currently-staged code, subject to the
        min/max confirmation-gap window. Clears the pending slot regardless
        of outcome, so a stale or repeated confirmation can't re-run it."""
        if not self._pending:
            return "There's nothing staged to run - propose some code first."

        pending = self._pending
        self._pending = None

        elapsed = time.time() - pending["proposed_at"]
        min_gap = config.get('coding.min_confirm_gap_seconds', 3.0)
        max_gap = config.get('coding.max_confirm_gap_seconds', 300.0)

        if elapsed < min_gap:
            # A real confirmation requires the user to have heard the
            # proposal (TTS) and replied (STT) - that always takes longer
            # than this. Getting here this fast means the model chained
            # propose+confirm in one turn without the user actually saying
            # anything, which is exactly what this gate exists to block.
            return (
                "Not running that - it needs to be confirmed by the user in an actual "
                "reply, not called back-to-back in the same turn."
            )
        if elapsed > max_gap:
            return "That proposal's gone stale - propose the code again if you still want to run it."

        return self._execute(pending["code"])

    def _execute(self, code: str) -> str:
        timeout = config.get('coding.execution_timeout_seconds', 10)
        max_output = config.get('coding.max_output_length', 1500)

        tmp_path = os.path.join(SCRIPTS_DIR, f"_run_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.py")
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(code)

            result = subprocess.run(
                [sys.executable, tmp_path],
                capture_output=True, text=True, timeout=timeout, cwd=SCRIPTS_DIR,
            )

            output = result.stdout.strip()
            error = result.stderr.strip()

            parts = []
            if output:
                parts.append(f"Output: {output[:max_output]}")
            if error:
                parts.append(f"Errors: {error[:max_output]}")
            if not output and not error:
                parts.append("Ran with no output.")
            if result.returncode != 0:
                parts.append(f"(exited with code {result.returncode})")

            return "\n".join(parts)

        except subprocess.TimeoutExpired:
            return f"That took longer than {timeout} seconds, so I stopped it."
        except Exception as e:
            return f"Failed to run that: {e}"
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass


code_executor = CodeExecutor()
