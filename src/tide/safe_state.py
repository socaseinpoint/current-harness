"""tide.safe_state — the shared safe writer of state files.

Directory 0700, file 0600 (``fchmod``), opened with ``O_NOFOLLOW`` (a planted
symlink cannot redirect the write elsewhere), no shared ``*.tmp`` — a temp file
with a unique name, ``os.replace`` on top. Any failure is raised as ``OSError``:
the caller decides whether to swallow it (a log must not break the bridge).
"""

from __future__ import annotations

import os
import stat
import tempfile
from pathlib import Path

_DIR_MODE = 0o700
_FILE_MODE = 0o600
MAX_BYTES = 1024 * 1024  # 1 MB, then rotation to <file>.1


def _ensure_dir(d: Path) -> None:
    """Create a 0700 directory. An existing one is narrowed to 0700 only if it is ours (``st_uid`` == current
    user) and not a symlink; someone else's directory (``/tmp``, another user's ``~``) is left alone."""
    d = Path(d)
    d.mkdir(parents=True, exist_ok=True, mode=_DIR_MODE)
    try:
        st = os.lstat(str(d))
    except OSError:
        return
    if stat.S_ISDIR(st.st_mode) and st.st_uid == os.getuid() and stat.S_IMODE(st.st_mode) != _DIR_MODE:
        os.chmod(str(d), _DIR_MODE)


def append_private(path: Path, line: str) -> None:
    """Append a line: O_APPEND|O_NOFOLLOW, 0600, a single ``os.write`` record (the line is never split)."""
    path = Path(path)
    _ensure_dir(path.parent)
    if path.is_symlink():
        raise OSError("symlink instead of a file: {0}".format(path))
    data = (line if line.endswith("\n") else line + "\n").encode("utf-8")
    try:  # rotation: the file reached the limit -> .1 (the old .1 is overwritten)
        if os.lstat(str(path)).st_size >= MAX_BYTES:
            rotated = str(path) + ".1"
            if os.path.islink(rotated):
                os.unlink(rotated)
            os.replace(str(path), rotated)
            os.chmod(rotated, _FILE_MODE)
    except OSError:
        pass
    fd = os.open(str(path), os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW, _FILE_MODE)
    try:
        os.fchmod(fd, _FILE_MODE)
        view = memoryview(data)
        while view:
            view = view[os.write(fd, view):]
    finally:
        os.close(fd)


def write_private(path: Path, text: str) -> None:
    """Replace the file whole: a unique tmp in the same directory (O_EXCL|O_NOFOLLOW, 0600) + ``os.replace``."""
    path = Path(path)
    _ensure_dir(path.parent)
    if path.is_symlink():
        raise OSError("symlink instead of a file: {0}".format(path))
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        os.fchmod(fd, _FILE_MODE)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, str(path))
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


__all__ = ["append_private", "write_private"]
