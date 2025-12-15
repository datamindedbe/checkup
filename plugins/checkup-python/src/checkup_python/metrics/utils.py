def parse_semantic_version(version: str) -> tuple[int, ...]:
    """
    Parse version string into tuple of integers for comparison.
    """

    parts = version.split(".")
    return tuple(int(part) for part in parts if part.isdigit())
