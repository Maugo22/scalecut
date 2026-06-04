"""Preview export names and project summary without writing to disk."""

from rich.console import Console
from rich.table import Table
from rich import box
from scalecut.models import ProjectConfig
from scalecut.naming import generate_all_filenames
from scalecut.folders import build_folder_tree

console = Console()


def show_preview(config: ProjectConfig) -> None:
    """Print a full preview of what ScaleCut will generate."""
    deliverables = generate_all_filenames(config)

    console.print()
    console.rule("[bold cyan]ScaleCut — Project Preview[/bold cyan]")
    console.print()

    # Project summary
    info = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    info.add_column(style="bold cyan", no_wrap=True)
    info.add_column(style="white")
    info.add_row("Client",      config.client)
    info.add_row("Project",     config.project)
    info.add_row("Type",        config.project_type)
    info.add_row("Delivery",    config.delivery_date)
    info.add_row("Clips",       str(config.num_clips))
    info.add_row("Platforms",   ", ".join(config.platforms))
    info.add_row("Formats",     ", ".join(config.formats))
    info.add_row("Language",    config.language)
    info.add_row("Version",     f"V{config.version.zfill(2)}")
    info.add_row("Status",      config.initial_status)
    info.add_row("Output path", config.output_path)
    info.add_row("Deliverables", str(len(deliverables)))
    console.print(info)

    # Folder tree
    console.print("[bold cyan]Folder structure[/bold cyan]")
    root_name = config.folder_name()
    console.print(f"  [bold yellow]{root_name}/[/bold yellow]")
    for folder in build_folder_tree(config):
        console.print(f"    [dim]{folder}/[/dim]")
    console.print()

    # Filename preview (first 10)
    console.print("[bold cyan]Export name preview[/bold cyan] [dim](first 10)[/dim]")
    table = Table(box=box.SIMPLE_HEAD, show_lines=False)
    table.add_column("Clip",     style="bold", no_wrap=True)
    table.add_column("Platform", style="cyan")
    table.add_column("Format",   style="magenta")
    table.add_column("Status",   style="yellow")
    table.add_column("Filename", style="green")

    for d in deliverables[:10]:
        table.add_row(d["clip"], d["platform"], d["format"], d["status"], d["filename"])

    if len(deliverables) > 10:
        table.add_row("...", "...", "...", "...", f"... ({len(deliverables) - 10} more)")

    console.print(table)
    console.print()
