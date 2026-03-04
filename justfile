default:
    @just --list

# Run all tests
test:
    uv run pytest tests/ plugins/*/tests --ignore=plugins/checkup-dbt/tests/fixtures

# Run tests with coverage
test-cov:
    uv run pytest tests/ plugins/*/tests --ignore=plugins/checkup-dbt/tests/fixtures --cov=src/checkup --cov-report=xml --cov-report=term-missing

# Run linter
lint:
    uv run ruff check .

# Run formatter check
format-check:
    uv run ruff format --check .

# Format code
format:
    uv run ruff format .

# Install dev dependencies only
install-dev:
    uv sync --group dev

# Install all dependencies
install:
    uv sync --all-packages --group dev

# Bump version for a package (major, minor, patch)
bump package level:
    uv version --package {{ package }} --bump {{ level }}

# Bump patch version
bump-patch package:
    just bump {{ package }} patch

# Bump minor version
bump-minor package:
    just bump {{ package }} minor

# Bump major version
bump-major package:
    just bump {{ package }} major

# Verify given version matches pyproject.toml version
verify-version package version:
    #!/usr/bin/env bash
    set -e
    TOML_VERSION=$(uv version --short --package {{ package }})
    if [ "$TOML_VERSION" != "{{ version }}" ]; then
        echo "Error: Tag version ({{ version }}) does not match pyproject.toml version ($TOML_VERSION)"
        exit 1
    fi
    echo "Version verified: $TOML_VERSION"

# Tag and push to trigger CD release
tag package:
    #!/usr/bin/env bash
    set -e
    TAG="{{ package }}-v$(uv version --short --package {{ package }})"
    git tag -l "$TAG" | grep -q . && echo "Error: Tag $TAG already exists locally" && exit 1
    git ls-remote --tags origin "$TAG" | grep -q . && echo "Error: Tag $TAG already exists on remote" && exit 1
    echo "Creating tag: $TAG"
    git tag "$TAG" && git push origin "$TAG"

# Build a specific package
build package:
    uv build --package {{ package }}

# Publish built package to PyPI
publish:
    @test -n "${UV_PUBLISH_TOKEN:-}" || (echo "Error: UV_PUBLISH_TOKEN not set" && exit 1)
    uv publish

# Build and publish a package
release package version:
    #!/usr/bin/env bash
    set -e
    echo "Releasing {{ package }} version {{ version }}"

    just verify-version {{ package }} {{ version }}
    just test
    just build {{ package }}
    just publish

    echo "Successfully released {{ package }} version {{ version }}"

# Release checkup
release-checkup version:
    just release checkup {{ version }}

# Release checkup-git plugin
release-checkup-git version:
    just release checkup-git {{ version }}

# Release checkup-dbt plugin
release-checkup-dbt version:
    just release checkup-dbt {{ version }}

# Release checkup-python plugin
release-checkup-python version:
    just release checkup-python {{ version }}

# Release checkup-conveyor plugin
release-checkup-conveyor version:
    just release checkup-conveyor {{ version }}
