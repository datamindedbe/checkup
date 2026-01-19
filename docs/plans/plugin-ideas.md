# Plugin Ideas for CheckUp

This document outlines potential plugins for the CheckUp framework. Each plugin follows the established pattern of providers (for data collection) and metrics (for measurement).

---

## 1. Airflow Plugin (`checkup-airflow`)

An Airflow governance plugin to measure DAG quality, scheduling patterns, and operational health.

### Provider

**`AirflowProvider`** - Connects to Airflow's metadata database or REST API to extract DAG and task information.

```python
class AirflowProvider(Provider):
    name: ClassVar[str] = "airflow"

    def __init__(
        self,
        airflow_home: str | None = None,      # For parsing DAG files directly
        api_url: str | None = None,           # For REST API access
        db_connection: str | None = None,     # For direct DB access
    ):
        ...
```

### Metrics

| Metric | Description | Unit | Why It Matters |
|--------|-------------|------|----------------|
| `airflow_dag_count` | Total number of DAGs | dags | Basic inventory |
| `airflow_dag_parsing_time` | Time to parse all DAGs | seconds | Long parsing times slow scheduler; should be < 30s |
| `airflow_dag_parsing_time_per_dag` | Average parsing time per DAG | seconds | Identifies slow DAGs |
| `airflow_slow_parsing_dags` | DAGs taking > N seconds to parse | dags | Diagnostic for optimization targets |
| `airflow_midnight_scheduled_dags` | DAGs scheduled at 00:00 UTC | dags | Midnight scheduling causes contention |
| `airflow_hourly_schedule_distribution` | Distribution of DAG schedules by hour | json | Identifies scheduling bottlenecks |
| `airflow_dags_without_owner` | DAGs missing owner field | dags | Governance: every DAG needs an owner |
| `airflow_dags_without_description` | DAGs missing description/doc_md | dags | Documentation coverage |
| `airflow_task_count` | Total tasks across all DAGs | tasks | Complexity indicator |
| `airflow_avg_tasks_per_dag` | Average tasks per DAG | tasks | DAG complexity |
| `airflow_dags_with_high_task_count` | DAGs with > N tasks | dags | Overly complex DAGs |
| `airflow_sensor_count` | Total sensor operators | sensors | Sensors consume worker slots |
| `airflow_sensors_without_timeout` | Sensors without explicit timeout | sensors | Risk of stuck tasks |
| `airflow_tasks_without_retries` | Tasks with retries=0 | tasks | No fault tolerance |
| `airflow_tasks_with_excessive_retries` | Tasks with retries > N | tasks | May indicate flaky tasks |
| `airflow_hardcoded_connections` | Tasks with hardcoded credentials | tasks | Security risk |
| `airflow_deprecated_operators` | Usage of deprecated operators | tasks | Technical debt |
| `airflow_pool_usage` | Pool utilization metrics | percent | Resource management |
| `airflow_variable_usage` | Count of Variable.get() calls in DAGs | calls | Performance (DB hits per parse) |

### Example Implementation

```python
class AirflowMidnightScheduledDagsMetric(AirflowMetric):
    name: ClassVar[str] = "airflow_midnight_scheduled_dags"
    description: ClassVar[str] = "DAGs scheduled exactly at midnight (00:00)"
    unit: ClassVar[str] = "dags"

    MIDNIGHT_PATTERNS = [
        "0 0 * * *",      # Cron: midnight daily
        "@daily",          # Preset: midnight
        "0 0 * * 0",      # Cron: midnight weekly
        "@weekly",         # Preset: midnight Sunday
    ]

    def calculate(self, context: Context, metrics: dict) -> None:
        dags = context["airflow"]["dags"]
        midnight_dags = [
            dag for dag in dags
            if dag.schedule_interval in self.MIDNIGHT_PATTERNS
        ]
        self.value = len(midnight_dags)
        self.diagnostic = ", ".join(d.dag_id for d in midnight_dags)
```

---

## 2. Great Expectations Plugin (`checkup-great-expectations`)

Measure data quality test coverage and validation health using Great Expectations.

### Provider

**`GreatExpectationsProvider`** - Loads expectations from a GX project context.

### Metrics

| Metric | Description | Unit |
|--------|-------------|------|
| `gx_expectation_suite_count` | Number of expectation suites | suites |
| `gx_total_expectations` | Total expectations defined | expectations |
| `gx_tables_with_expectations` | Data assets with at least one suite | tables |
| `gx_tables_without_expectations` | Data assets without any validation | tables |
| `gx_avg_expectations_per_suite` | Average expectations per suite | expectations |
| `gx_suites_without_descriptions` | Suites missing documentation | suites |
| `gx_checkpoint_count` | Number of configured checkpoints | checkpoints |
| `gx_recent_validation_pass_rate` | Pass rate of recent validations | percent |
| `gx_expectations_by_type` | Distribution by expectation type | json |

---

## 3. SQLFluff Plugin (`checkup-sqlfluff`)

Measure SQL code quality and style compliance.

### Provider

**`SqlFluffProvider`** - Runs SQLFluff linting on SQL files or dbt models.

### Metrics

| Metric | Description | Unit |
|--------|-------------|------|
| `sqlfluff_total_violations` | Total linting violations | violations |
| `sqlfluff_files_with_violations` | Files with at least one violation | files |
| `sqlfluff_clean_files` | Files with zero violations | files |
| `sqlfluff_clean_file_percentage` | Percentage of clean files | percent |
| `sqlfluff_violations_by_rule` | Violation count per rule | json |
| `sqlfluff_critical_violations` | High-severity violations | violations |
| `sqlfluff_avg_violations_per_file` | Average violations per file | violations |
| `sqlfluff_unfixable_violations` | Violations that can't be auto-fixed | violations |

---

## 4. Data Catalog Plugin (`checkup-datacatalog`)

Measure metadata completeness in data catalogs (DataHub, Atlan, OpenMetadata, etc.).

### Provider

**`DataHubProvider`** / **`AtlanProvider`** - Connects to catalog APIs.

### Metrics

| Metric | Description | Unit |
|--------|-------------|------|
| `catalog_total_assets` | Total cataloged data assets | assets |
| `catalog_assets_with_owners` | Assets with assigned ownership | assets |
| `catalog_ownership_coverage` | Percentage with owners | percent |
| `catalog_assets_with_description` | Assets with descriptions | assets |
| `catalog_description_coverage` | Percentage with descriptions | percent |
| `catalog_assets_with_tags` | Assets with classification tags | assets |
| `catalog_glossary_term_coverage` | Assets linked to glossary terms | percent |
| `catalog_lineage_coverage` | Assets with upstream/downstream lineage | percent |
| `catalog_stale_assets` | Assets not updated in N days | assets |
| `catalog_orphan_assets` | Assets with no owner and no recent access | assets |
| `catalog_pii_tagged_assets` | Assets tagged as containing PII | assets |

---

## 5. Spark Plugin (`checkup-spark`)

Measure Spark application quality and configuration health.

### Provider

**`SparkHistoryProvider`** - Connects to Spark History Server REST API.

### Metrics

| Metric | Description | Unit |
|--------|-------------|------|
| `spark_total_applications` | Total Spark applications | apps |
| `spark_failed_applications` | Applications that failed | apps |
| `spark_success_rate` | Application success rate | percent |
| `spark_avg_duration` | Average application duration | seconds |
| `spark_jobs_with_skew` | Jobs with data skew detected | jobs |
| `spark_jobs_with_spill` | Jobs with disk spill | jobs |
| `spark_small_file_reads` | Jobs reading many small files | jobs |
| `spark_shuffle_heavy_jobs` | Jobs with excessive shuffle | jobs |
| `spark_underutilized_executors` | Jobs with low executor utilization | jobs |

---

## 6. Kafka Plugin (`checkup-kafka`)

Measure Kafka topic configuration and schema governance.

### Provider

**`KafkaAdminProvider`** - Connects to Kafka Admin API.
**`SchemaRegistryProvider`** - Connects to Schema Registry.

### Metrics

| Metric | Description | Unit |
|--------|-------------|------|
| `kafka_topic_count` | Total Kafka topics | topics |
| `kafka_topics_without_schema` | Topics without registered schema | topics |
| `kafka_schema_coverage` | Percentage of topics with schemas | percent |
| `kafka_topics_low_retention` | Topics with retention < N days | topics |
| `kafka_topics_high_partitions` | Topics with > N partitions | topics |
| `kafka_topics_without_cleanup_policy` | Topics without explicit cleanup | topics |
| `kafka_consumer_lag_alerts` | Consumer groups with high lag | groups |
| `kafka_inactive_topics` | Topics with no recent messages | topics |
| `kafka_schema_compatibility_violations` | Schemas not backward compatible | schemas |

---

## 7. Terraform Plugin (`checkup-terraform`)

Measure Infrastructure as Code quality and security.

### Provider

**`TerraformProvider`** - Parses Terraform files and state.

### Metrics

| Metric | Description | Unit |
|--------|-------------|------|
| `tf_resource_count` | Total managed resources | resources |
| `tf_module_count` | Number of modules used | modules |
| `tf_resources_without_tags` | Resources missing required tags | resources |
| `tf_hardcoded_secrets` | Resources with hardcoded secrets | resources |
| `tf_deprecated_resources` | Usage of deprecated resource types | resources |
| `tf_drift_detected` | Resources with state drift | resources |
| `tf_unencrypted_storage` | Storage without encryption | resources |
| `tf_public_access_resources` | Resources with public access | resources |
| `tf_resources_without_lifecycle` | Resources without lifecycle rules | resources |

---

## 8. Cost/FinOps Plugin (`checkup-finops`)

Measure cloud cost governance and efficiency.

### Provider

**`AWSCostProvider`** / **`GCPBillingProvider`** / **`SnowflakeCostProvider`**

### Metrics

| Metric | Description | Unit |
|--------|-------------|------|
| `finops_total_monthly_cost` | Total monthly spend | dollars |
| `finops_cost_by_service` | Cost breakdown by service | json |
| `finops_cost_trend` | Month-over-month cost change | percent |
| `finops_untagged_resources_cost` | Cost of resources without tags | dollars |
| `finops_idle_resources` | Resources with no recent usage | resources |
| `finops_idle_resources_cost` | Estimated cost of idle resources | dollars |
| `finops_oversized_resources` | Resources with low utilization | resources |
| `finops_reserved_capacity_coverage` | Workloads covered by reservations | percent |
| `finops_spot_instance_usage` | Workloads using spot/preemptible | percent |

---

## 9. Delta Lake / Iceberg Plugin (`checkup-lakehouse`)

Measure lakehouse table health and maintenance.

### Provider

**`DeltaLakeProvider`** / **`IcebergProvider`** - Reads table metadata.

### Metrics

| Metric | Description | Unit |
|--------|-------------|------|
| `lakehouse_table_count` | Total managed tables | tables |
| `lakehouse_tables_needing_vacuum` | Tables with many old files | tables |
| `lakehouse_tables_needing_optimize` | Tables with many small files | tables |
| `lakehouse_avg_file_size` | Average file size | bytes |
| `lakehouse_small_file_tables` | Tables with avg file < threshold | tables |
| `lakehouse_schema_evolution_count` | Schema changes in period | changes |
| `lakehouse_tables_without_zorder` | Tables without Z-ordering | tables |
| `lakehouse_partition_count` | Average partitions per table | partitions |
| `lakehouse_over_partitioned_tables` | Tables with too many partitions | tables |

---

## 10. CI/CD Plugin (`checkup-cicd`)

Measure CI/CD pipeline health (GitHub Actions, GitLab CI, etc.).

### Provider

**`GitHubActionsProvider`** / **`GitLabCIProvider`**

### Metrics

| Metric | Description | Unit |
|--------|-------------|------|
| `cicd_workflow_count` | Total CI/CD workflows | workflows |
| `cicd_avg_build_time` | Average pipeline duration | seconds |
| `cicd_success_rate` | Pipeline success rate | percent |
| `cicd_flaky_tests` | Tests that fail intermittently | tests |
| `cicd_workflows_without_timeout` | Workflows without timeout set | workflows |
| `cicd_workflows_using_latest_tag` | Workflows using `:latest` images | workflows |
| `cicd_hardcoded_secrets` | Workflows with inline secrets | workflows |
| `cicd_missing_required_checks` | PRs merged without required checks | prs |
| `cicd_avg_time_to_merge` | Average PR merge time | hours |

---

## Implementation Priority

Based on common data platform needs:

| Priority | Plugin | Rationale |
|----------|--------|-----------|
| 1 | `checkup-airflow` | Core orchestration tool, scheduling issues are common |
| 2 | `checkup-sqlfluff` | SQL quality directly impacts dbt projects |
| 3 | `checkup-great-expectations` | Data quality is fundamental to data governance |
| 4 | `checkup-datacatalog` | Metadata management is increasingly important |
| 5 | `checkup-lakehouse` | Delta/Iceberg maintenance affects performance |
| 6 | `checkup-cicd` | CI/CD health impacts development velocity |
| 7 | `checkup-finops` | Cost governance is always relevant |
| 8 | `checkup-spark` | Useful for Spark-heavy environments |
| 9 | `checkup-kafka` | Useful for streaming architectures |
| 10 | `checkup-terraform` | IaC governance for platform teams |

---

## Cross-Plugin Metrics

Some powerful metrics can combine data from multiple plugins:

| Metric | Plugins | Description |
|--------|---------|-------------|
| `dbt_model_to_airflow_task_ratio` | dbt + airflow | Ensure DAGs don't run too many models per task |
| `dbt_model_gx_coverage` | dbt + great-expectations | dbt models with GX expectations |
| `catalog_dbt_sync` | dbt + datacatalog | dbt models missing from catalog |
| `cost_per_dbt_model` | dbt + finops | Estimated cost per model |
| `cicd_dbt_test_coverage` | dbt + cicd | dbt tests running in CI |
