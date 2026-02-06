"""HTML report materializer."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from checkup.materializers.base import Materializer, group_metrics_hierarchical
from checkup.metric import Metric


class HTMLMaterializer(Materializer):
    """Output metrics to an HTML file with hierarchical grouping.

    Generates a styled HTML report with metrics grouped by two levels of tags.
    Uses Bootstrap accordions for collapsible groups.

    Attributes:
        output_path: Path where the HTML file will be written
        group_tag_1: Tag name for level 1 grouping (e.g., "domain")
        group_tag_2: Tag name for level 2 grouping (e.g., "project")
    """

    output_path: Path
    group_tag_1: str
    group_tag_2: str

    def materialize(self, metrics: list[Metric], direct_metric_names: set[str]) -> None:
        """Generate and write HTML report to file."""
        filtered = self._filter_metrics(metrics, direct_metric_names)

        # Group metrics hierarchically
        grouped = group_metrics_hierarchical(
            filtered, self.group_tag_1, self.group_tag_2
        )

        # Generate HTML
        html = self._generate_html(grouped)

        # Write to file
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "w") as f:
            f.write(html)

    def _generate_html(self, grouped: dict) -> str:
        """Generate complete HTML document using Jinja2 template."""
        # Set up Jinja2 environment
        template_dir = Path(__file__).parent.parent / "templates"
        env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
        template = env.get_template("metrics_report.html")

        # Render template with data
        return template.render(grouped=grouped)
