"""ScaleCut CLI — step-by-step project scaffolding for video production teams."""

import sys
from pathlib import Path
from datetime import date

import click
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from scalecut.models import ProjectConfig
from scalecut.templates import (
    PROJECT_TEMPLATES,
    ALL_PLATFORMS,
    ALL_FORMATS,
    STATUSES,
    PLATFORM_FORMATS,
)
from scalecut.folders import create_folders
from scalecut.checklist import write_csv, write_markdown
from scalecut.config_gen import write_config
from scalecut.readme_gen import write_readme
from scalecut.preview import show_preview, write_naming_preview
from scalecut.editor_instructions import write_editor_instructions
from scalecut.prompts_ai import write_prompts_ai
from scalecut.edit_plan import (
    make_placeholder_clips, write_edit_plan_csv, write_edit_plan_md,
    write_edit_plan_json, write_markers_csv,
)
from scalecut import __version__

console = Console()

STYLE = questionary.Style([
    ("qmark",       "fg:#00bfff bold"),
    ("question",    "bold"),
    ("answer",      "fg:#00ff87 bold"),
    ("pointer",     "fg:#00bfff bold"),
    ("highlighted", "fg:#00ff87 bold"),
    ("selected",    "fg:#888888"),
    ("separator",   "fg:#444444"),
    ("instruction", "fg:#555555 italic"),
])

TOTAL_STEPS = 5


# ── UI helpers ────────────────────────────────────────────────────────────────

def _ask(question_fn, **kwargs):
    """Wrap questionary prompts with clean Ctrl+C handling."""
    try:
        result = question_fn(style=STYLE, **kwargs).ask()
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelado.[/yellow]")
        sys.exit(0)
    if result is None:
        console.print("\n[yellow]Cancelado.[/yellow]")
        sys.exit(0)
    return result


def _banner() -> None:
    console.print()
    console.print(Panel(
        Text.from_markup(
            f"[bold cyan]ScaleCut[/bold cyan]  [dim]v{__version__}[/dim]\n"
            "[white]Workflow scaffolding para equipos de video[/white]\n\n"
            "[dim]Crea estructura, naming y checklists en segundos.[/dim]"
        ),
        box=box.DOUBLE_EDGE,
        border_style="cyan",
        padding=(1, 4),
    ))
    console.print()


def _step(n: int, title: str, subtitle: str = "") -> None:
    """Print a numbered step header."""
    console.print()
    label = f"  Paso {n} de {TOTAL_STEPS}  —  {title}  "
    console.rule(f"[bold cyan]{label}[/bold cyan]", style="cyan")
    if subtitle:
        console.print(f"  [dim]{subtitle}[/dim]")
    console.print()


def _recap(**fields) -> None:
    """Print a compact summary of the values just entered."""
    for label, value in fields.items():
        val = ", ".join(value) if isinstance(value, list) else str(value)
        console.print(f"  [dim]{label}:[/dim]  [bold green]{val}[/bold green]")
    console.print()


def _divider() -> None:
    console.print()


# ── Wizard ────────────────────────────────────────────────────────────────────

def run_wizard() -> ProjectConfig:
    _banner()

    # ─────────────────────────────────────────────────────────────────────────
    # Paso 1 — Información del proyecto
    # ─────────────────────────────────────────────────────────────────────────
    _step(1, "Información del proyecto",
          "Datos básicos de identidad del proyecto.")

    client = _ask(
        questionary.text,
        message="Nombre del cliente:",
        validate=lambda v: True if v.strip() else "No puede estar vacío.",
    )

    project = _ask(
        questionary.text,
        message="Nombre del proyecto:",
        validate=lambda v: True if v.strip() else "No puede estar vacío.",
    )

    project_type = _ask(
        questionary.select,
        message="Tipo de proyecto:",
        choices=list(PROJECT_TEMPLATES.keys()),
        instruction="(↑↓ navegar, Enter seleccionar)",
    )

    template = PROJECT_TEMPLATES[project_type]
    console.print(f"  [dim cyan]→ {template['description']}[/dim cyan]")
    _divider()

    delivery_date = _ask(
        questionary.text,
        message="Fecha de entrega (YYYY-MM-DD):",
        default=str(date.today()),
        validate=lambda v: (
            True if len(v) == 10 and v[4] == "-" and v[7] == "-"
            else "Usa el formato YYYY-MM-DD."
        ),
    )

    _recap(Cliente=client, Proyecto=project, Tipo=project_type, Entrega=delivery_date)

    # ─────────────────────────────────────────────────────────────────────────
    # Paso 2 — Alcance de producción
    # ─────────────────────────────────────────────────────────────────────────
    _step(2, "Alcance de producción",
          "Cuántos clips necesitas y en qué plataformas / formatos.")

    num_clips = _ask(
        questionary.text,
        message="Número de clips:",
        default=str(template.get("typical_clips", 5)),
        validate=lambda v: True if v.isdigit() and int(v) > 0 else "Ingresa un número positivo.",
    )

    suggested = template.get("suggested_platforms", [])
    console.print(f"  [dim]Sugeridas para este template: {', '.join(suggested)}[/dim]")

    platforms = _ask(
        questionary.checkbox,
        message="Plataformas:",
        choices=[questionary.Choice(p, checked=(p in suggested)) for p in ALL_PLATFORMS],
        instruction="(Espacio = seleccionar, Enter = confirmar)",
        validate=lambda v: True if v else "Selecciona al menos una plataforma.",
    )

    auto_formats = sorted({fmt for p in platforms for fmt in PLATFORM_FORMATS.get(p, [])})
    console.print(f"  [dim]Formatos detectados para tus plataformas: {', '.join(auto_formats)}[/dim]")

    formats = _ask(
        questionary.checkbox,
        message="Formatos a producir:",
        choices=[questionary.Choice(f, checked=(f in auto_formats)) for f in ALL_FORMATS],
        instruction="(Espacio = seleccionar, Enter = confirmar)",
        validate=lambda v: True if v else "Selecciona al menos un formato.",
    )

    total_deliverables = int(num_clips) * len(platforms) * len(formats)
    console.print(f"  [dim cyan]→ {int(num_clips)} clips × {len(platforms)} plataformas × {len(formats)} formatos = "
                  f"[bold]{total_deliverables} entregables[/bold][/dim cyan]")

    _recap(Clips=num_clips, Plataformas=platforms, Formatos=formats)

    # ─────────────────────────────────────────────────────────────────────────
    # Paso 3 — Versión e idioma
    # ─────────────────────────────────────────────────────────────────────────
    _step(3, "Versión e idioma",
          "Metadatos iniciales de todos los entregables.")

    version = _ask(
        questionary.text,
        message="Número de versión inicial (ej. 01):",
        default="01",
        validate=lambda v: True if v.isdigit() else "Solo números (ej. 01).",
    )

    language = _ask(
        questionary.select,
        message="Idioma del contenido:",
        choices=["ES", "EN", "PT", "FR", "DE", "Other"],
    )

    initial_status = _ask(
        questionary.select,
        message="Estado inicial de todos los entregables:",
        choices=STATUSES,
    )

    _recap(**{"Versión": f"V{version.zfill(2)}", "Idioma": language, "Estado": initial_status})

    # ─────────────────────────────────────────────────────────────────────────
    # Paso 4 — Destino
    # ─────────────────────────────────────────────────────────────────────────
    _step(4, "Destino",
          "Dónde se creará la carpeta raíz del proyecto.")

    default_output = str(Path.home() / "Desktop" / "ScaleCut_Projects")
    output_path = _ask(
        questionary.text,
        message="Ruta de salida:",
        default=default_output,
        instruction="(Enter para usar la ruta por defecto)",
    )

    _recap(**{"Ruta de salida": output_path.strip()})

    return ProjectConfig(
        client=client.strip(),
        project=project.strip(),
        project_type=project_type,
        delivery_date=delivery_date,
        num_clips=int(num_clips),
        platforms=platforms,
        formats=formats,
        version=version.zfill(2),
        language=language,
        initial_status=initial_status,
        output_path=output_path.strip(),
    )


# ── Scaffold ──────────────────────────────────────────────────────────────────

def scaffold(config: ProjectConfig) -> None:
    """Create all project files and folders, printing live progress."""
    console.print()
    console.rule("[bold cyan]  Creando proyecto...  [/bold cyan]", style="cyan")
    console.print()

    root = create_folders(config)
    folder_count = sum(1 for _ in root.rglob("*") if _.is_dir())
    console.print(f"  [bold green]✓[/bold green]  Carpetas               [dim]{folder_count} directorios → {root.name}[/dim]")

    row_count = config.num_clips * len(config.platforms) * len(config.formats)
    write_csv(config, root)
    console.print(f"  [bold green]✓[/bold green]  delivery_checklist.csv [dim]{row_count} entregables[/dim]")

    write_markdown(config, root)
    console.print(f"  [bold green]✓[/bold green]  delivery_checklist.md  [dim]checkboxes por clip[/dim]")

    write_naming_preview(config, root)
    console.print(f"  [bold green]✓[/bold green]  naming_preview.md      [dim]nombres por clip y plataforma[/dim]")

    write_editor_instructions(config, root)
    console.print(f"  [bold green]✓[/bold green]  editor_instructions.md [dim]workflow Premiere / Resolve[/dim]")

    write_prompts_ai(config, root)
    console.print(f"  [bold green]✓[/bold green]  prompts_ai.md          [dim]6 prompts listos para IA[/dim]")

    write_config(config, root)
    console.print(f"  [bold green]✓[/bold green]  project_config.json    [dim]resumen + {row_count} entregables[/dim]")

    write_readme(config, root)
    console.print(f"  [bold green]✓[/bold green]  README.md")

    ep_clips = make_placeholder_clips(config)
    write_edit_plan_csv(ep_clips, root)
    write_edit_plan_md(ep_clips, root, config)
    write_edit_plan_json(ep_clips, root, config)
    write_markers_csv(ep_clips, root)
    console.print(f"  [bold green]✓[/bold green]  edit_plan.*            [dim]plan vacío — rellena los timecodes[/dim]")
    console.print(f"  [bold green]✓[/bold green]  markers.csv            [dim]marcadores para Premiere / Resolve[/dim]")

    console.print()
    console.print(Panel(
        Text.from_markup(
            f"[bold green]Proyecto listo[/bold green]\n\n"
            f"[bold white]{root.name}[/bold white]\n"
            f"[dim]{root}[/dim]\n\n"
            f"[dim]Abre [bold]10_Admin/checklist.csv[/bold] para empezar a trackear."
        ),
        box=box.ROUNDED,
        border_style="green",
        padding=(1, 3),
    ))


# ── CLI commands ──────────────────────────────────────────────────────────────

@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    """ScaleCut — video production workflow scaffolding."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(new)


@main.command()
def new():
    """Wizard paso a paso para crear un nuevo proyecto (modo por defecto)."""
    config = run_wizard()

    # ── Paso 5: preview + confirmación ───────────────────────────────────────
    _step(5, "Vista previa y confirmación",
          "Revisa los detalles antes de crear los archivos.")

    show_preview(config)

    confirmed = _ask(
        questionary.confirm,
        message="¿Crear este proyecto?",
        default=True,
    )

    if confirmed:
        scaffold(config)
    else:
        console.print()
        console.print("[yellow]  Cancelado. No se crearon archivos.[/yellow]")


@main.command()
@click.argument("output_path", default=".")
@click.option("--client",    required=True, help="Nombre del cliente.")
@click.option("--project",   required=True, help="Nombre del proyecto.")
@click.option("--type",      "project_type", required=True,
              type=click.Choice(list(PROJECT_TEMPLATES.keys())), help="Tipo de proyecto.")
@click.option("--date",      "delivery_date", default=str(date.today()), help="Fecha de entrega YYYY-MM-DD.")
@click.option("--clips",     default=5, type=int, help="Número de clips.")
@click.option("--platforms", default="Instagram Reels,TikTok", help="Plataformas separadas por coma.")
@click.option("--formats",   default="9x16", help="Formatos separados por coma.")
@click.option("--version",   default="01", help="Versión inicial.")
@click.option("--language",  default="ES", help="Idioma del contenido.")
@click.option("--status",    default="Not started", help="Estado inicial.")
def quick(output_path, client, project, project_type, delivery_date,
          clips, platforms, formats, version, language, status):
    """Crear proyecto sin wizard (todos los datos como flags)."""
    config = ProjectConfig(
        client=client,
        project=project,
        project_type=project_type,
        delivery_date=delivery_date,
        num_clips=clips,
        platforms=[p.strip() for p in platforms.split(",")],
        formats=[f.strip() for f in formats.split(",")],
        version=version.zfill(2),
        language=language,
        initial_status=status,
        output_path=output_path,
    )
    show_preview(config)
    scaffold(config)


@main.command(name="templates")
def list_templates():
    """Listar todas las plantillas disponibles."""
    table = Table(title="ScaleCut — Plantillas de proyecto", box=box.SIMPLE_HEAD)
    table.add_column("Plantilla",   style="bold cyan", no_wrap=True)
    table.add_column("Descripción", style="white")
    table.add_column("Plataformas", style="dim")
    table.add_column("Formatos",    style="magenta")
    for name, info in PROJECT_TEMPLATES.items():
        table.add_row(
            name,
            info["description"],
            ", ".join(info["suggested_platforms"]),
            ", ".join(info["suggested_formats"]),
        )
    console.print()
    console.print(table)


@main.command()
@click.argument("project_path", type=click.Path())
def report(project_path):
    """Resumen de progreso de un proyecto ScaleCut existente."""
    from scalecut.report import load_report, ReportError

    try:
        data = load_report(project_path)
    except ReportError as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}\n")
        sys.exit(1)

    # ── Header ─────────────────────────────────────────────────────────────
    console.print()
    console.print(Panel(
        Text.from_markup(
            f"[bold cyan]{data['client']}[/bold cyan]  [dim]—[/dim]  "
            f"[bold white]{data['project']}[/bold white]\n"
            f"[dim]{data['project_type']}  ·  Entrega: {data['delivery_date']}[/dim]"
        ),
        box=box.ROUNDED,
        border_style="cyan",
        padding=(0, 2),
        title="[bold]ScaleCut Report[/bold]",
        title_align="left",
    ))
    console.print()

    # ── Progress summary ────────────────────────────────────────────────────
    total = data["total"]
    delivered = data["status_counts"].get("Delivered", 0)
    pct_d = data["pct_delivered"]
    pct_a = data["pct_advanced"]

    summary = Table(box=box.SIMPLE_HEAD, show_header=False, padding=(0, 2))
    summary.add_column("Campo", style="dim", no_wrap=True)
    summary.add_column("Valor", style="bold white")
    summary.add_row("Total entregables", str(total))
    summary.add_row("Delivered", f"{delivered}  [dim]({pct_d}%)[/dim]")
    summary.add_row(
        "Approved + Exported + Delivered",
        f"{sum(data['status_counts'].get(s, 0) for s in ('Approved', 'Exported', 'Delivered'))}"
        f"  [dim]({pct_a}%)[/dim]",
    )
    summary.add_row("Plataformas", ", ".join(data["platforms"]))
    summary.add_row("Formatos", ", ".join(data["formats"]))
    console.print(summary)

    # ── Status breakdown ────────────────────────────────────────────────────
    from scalecut.templates import STATUSES

    status_table = Table(
        title="Estado de entregables",
        box=box.SIMPLE_HEAD,
        title_style="bold",
        padding=(0, 2),
    )
    status_table.add_column("Status", style="cyan", no_wrap=True)
    status_table.add_column("Cantidad", justify="right")
    status_table.add_column("Porcentaje", justify="right", style="dim")

    for status in STATUSES:
        count = data["status_counts"].get(status, 0)
        if count == 0:
            continue
        pct = round(count / total * 100, 1) if total else 0.0
        status_table.add_row(status, str(count), f"{pct}%")

    console.print(status_table)

    # ── Next action ─────────────────────────────────────────────────────────
    console.print(Panel(
        Text.from_markup(
            f"[bold yellow]Próxima acción:[/bold yellow]  {data['next_action']}"
        ),
        box=box.ROUNDED,
        border_style="yellow",
        padding=(0, 2),
    ))
    console.print()


@main.command(name="version")
def show_version():
    """Mostrar versión de ScaleCut."""
    console.print(f"ScaleCut v{__version__}")
