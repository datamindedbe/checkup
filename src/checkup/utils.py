import os
import sys
from collections.abc import Iterator
from contextlib import contextmanager


@contextmanager
def suppress_subprocess_output() -> Iterator[None]:
    """
    Suppress stdout/stderr from subprocesses while preserving Python output.

    This redirects the underlying file descriptors to /dev/null, which affects
    subprocess output but not Python's print/logging which use the Python-level
    sys.stdout/sys.stderr objects.
    """

    original_stdout_fd = sys.stdout.fileno()
    original_stderr_fd = sys.stderr.fileno()
    saved_stdout_fd = os.dup(original_stdout_fd)
    saved_stderr_fd = os.dup(original_stderr_fd)

    try:
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, original_stdout_fd)
        os.dup2(devnull, original_stderr_fd)
        os.close(devnull)
        yield
    finally:
        os.dup2(saved_stdout_fd, original_stdout_fd)
        os.dup2(saved_stderr_fd, original_stderr_fd)
        os.close(saved_stdout_fd)
        os.close(saved_stderr_fd)
