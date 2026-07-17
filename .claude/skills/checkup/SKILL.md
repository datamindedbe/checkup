---
name: checkup
description: Measure data product health with the checkup CLI. Use when the user wants to run checkup, add or configure metrics, check a project's health or governance, or author/edit a checkup.yaml.
---

# Using the checkup CLI

`checkup` runs **metrics** (from installed checkup plugins like git, dbt, python) against a project and **materializes** the results.

Work in this order: **discover** what's installed → **configure** → **run**. Two ways to configure, pick by longevity:

- **Ad-hoc** — pass everything as `checkup run` flags, no file. Best for a one-off check ("what's the git health of this repo?").
- **Persistent** — write a `checkup.yaml`. Best when the same metrics run repeatedly, get committed to the repo, or number more than a handful.

## Step 1: Discover what's available

The set of valid metric and provider types depends on which plugins are installed. Never guess them — read them:

```bash
checkup plugins          # installed plugins + the metrics/providers/materializers each adds
checkup schema           # writes checkup.schema.json — the authoritative list of valid types and their config keys
```

`checkup.schema.json` is generated from the *installed* plugins. Read it to see every valid `type`, which config keys each accepts, and which are required. Regenerate it after installing a plugin.

**Completion criterion:** you have the exact type names and config keys for the metrics the user wants, taken from `checkup plugins` / the schema — not invented.

## Step 2: Configure

### Ad-hoc — CLI flags

Pass providers, metrics, and tags directly. With no config file present, these flags *are* the whole config:

```bash
checkup run -p git -m git_days_since_last_update -m git_tracked_file_count:pattern=src/*
```

- `-p name[:k=v,...]` provider, `-m type[:k=v,...]` metric, `-t key=value` tag. Repeat each flag per item.
- Inline config is `type:key=value,key2=value2` (comma-separated).
- These flags **replace** the corresponding list — combine with `-c` to swap out one list while keeping the file's others.

### Persistent — checkup.yaml

Write the file yourself. Do **not** run `checkup init` or `checkup config` — they are interactive wizards that block waiting for keyboard input you cannot provide.

```yaml
# yaml-language-server: $schema=checkup.schema.json

tags:                              # free-form key=value, attached to every measurement
  project: my-data-product

providers:                         # data sources that enrich context
- name: git

metrics:                           # each entry: type + optional name + inline config keys
- type: git_days_since_last_update
- type: git_tracked_file_count
  pattern: src/*                   # config keys sit inline, as siblings of `type`
- type: git_tracked_file_count
  name: tests_exist                # `name` defaults to `type`; set it when a type repeats
  pattern: tests/*

materializer:                      # optional; defaults to console. One materializer.
  type: html
  output_path: report.html

# select / exclude: optional top-level output filters (see Selectors below)
```

Config keys are inline siblings of `type`/`name`, not nested under a `config:` key. Validate against `checkup.schema.json` before running.

**Completion criterion:** every metric the user asked for is present with a valid `type`, and repeated types have distinct `name`s.

## Step 3: Run

```bash
checkup run                        # auto-discovers ./checkup.yaml if present; else pass -p/-m flags
checkup run -c path/to/checkup.yaml
checkup run --dry-run              # calculate + print to console, materialize nothing (preview / no side effects)
checkup run -q                     # only materializer output on stdout (machine-readable; status→stderr)
```

Start with `--dry-run` to confirm metrics compute without errors, then run for real. Errors for individual metrics are reported inline and do not abort the run.

**Completion criterion:** the run reports no unexpected metric errors, and the intended output (console/file) is produced.

## Reference

Run `checkup --help` and `checkup run --help` for the command list and every flag.

- `checkup init` / `checkup config` are **interactive wizards** — they block on keyboard input you can't provide. Author/edit `checkup.yaml` directly instead.
- `-t` / `-p` / `-m` (tags / providers / metrics) **replace** the config's corresponding list, they don't merge into it.
- `--no-multiprocessing` runs metrics sequentially — use it when a crashing metric hides the traceback.

### Selectors (`-s`/`--select`, `--exclude`, or `select:`/`exclude:` in config)

Whitespace-separated atoms, each `[method:]pattern`, `*` wildcards. Methods: `name` (default), `tag`, `type`. Selection filters **output only** — every metric is still calculated, so dependencies stay satisfied.

```text
git_*                              # by name (default method)
type:git_tracked_file_count        # by metric type
tag:healthcheck name:python_*      # union of atoms
```

### Materializer types

`console` (default), `csv`, `html`, `markdown`, `sqlalchemy`. The set depends on installed plugins — `checkup.schema.json` lists what's available and the config keys each accepts.
