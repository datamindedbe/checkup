import sys
from io import StringIO

from checkup.materializers import Materializer


def capture_output(materializer: Materializer, measurements, direct) -> str:
    """
    Capture the stdout a materializer produces, restoring stdout afterwards.
    """

    captured_output = StringIO()
    sys.stdout = captured_output
    try:
        materializer.materialize(measurements, direct)
    finally:
        sys.stdout = sys.__stdout__
    return captured_output.getvalue()
