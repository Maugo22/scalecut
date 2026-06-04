"""ScaleCut — Streamlit web UI."""

from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from scalecut import __version__
from scalecut.checklist import write_csv, write_markdown
from scalecut.config_gen import write_config
from scalecut.demo import DEMO_PROJECT
from scalecut.editor_instructions import write_editor_instructions
from scalecut.folders import build_folder_tree, create_folders
from scalecut.models import ProjectConfig
from scalecut.naming import generate_all_filenames, sanitize
from scalecut.package import create_zip
from scalecut.preview import write_naming_preview
from scalecut.prompts_ai import write_prompts_ai
from scalecut.readme_gen import write_readme
from scalecut.templates import (
    ALL_FORMATS,
    ALL_PLATFORMS,
    PLATFORM_FORMATS,
    PROJECT_TEMPLATES,
    STATUSES,
)

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="ScaleCut",
    page_icon="✂️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

TEMPLATE_ICONS = {
    "Podcast Repurposing":              "🎙️",
    "Reels/Shorts para marca personal": "📱",
    "Campaña publicitaria":             "📢",
    "Curso online":                     "🎓",
    "Testimoniales":                    "💬",
    "UGC Content":                      "📲",
    "YouTube long-form + Shorts":       "▶️",
}

FOLDER_HINTS = {
    "01_Footage":      "footage bruto de cámara",
    "02_Audio":        "música, voz en off, SFX",
    "03_Graphics":     "motion graphics, overlays",
    "04_Project_Files":"archivos .prproj / .drp",
    "05_Sequences":    "secuencias de edición",
    "06_Subtitles":    "archivos .srt / .vtt",
    "07_Exports":      "exports finales por formato",
    "08_Delivery":     "entregables aprobados",
    "09_References":   "briefs y referencias",
    "10_Admin":        "checklists y config",
}

ADMIN_FILES = [
    "delivery_checklist.csv",
    "delivery_checklist.md",
    "naming_preview.md",
    "editor_instructions.md",
    "prompts_ai.md",
    "project_config.json",
    "README.md",
    "scalecut_package.zip",
]

# ── Session state keys ────────────────────────────────────────────────────────

K = dict(
    proj_type = "sc_proj_type",
    client    = "sc_client",
    project   = "sc_project",
    date      = "sc_date",
    clips     = "sc_clips",
    platforms = "sc_platforms",
    formats   = "sc_formats",
    version   = "sc_version",
    language  = "sc_language",
    status    = "sc_status",
    output    = "sc_output",
    prev_type = "sc_prev_type",
)

def _init_state():
    defaults = {
        K["proj_type"]: list(PROJECT_TEMPLATES.keys())[0],
        K["client"]:    "",
        K["project"]:   "",
        K["date"]:      date.today(),
        K["clips"]:     5,
        K["platforms"]: PROJECT_TEMPLATES[list(PROJECT_TEMPLATES.keys())[0]]["suggested_platforms"],
        K["formats"]:   PROJECT_TEMPLATES[list(PROJECT_TEMPLATES.keys())[0]]["suggested_formats"],
        K["version"]:   "01",
        K["language"]:  "ES",
        K["status"]:    "Not started",
        K["output"]:    str(Path.home() / "Desktop" / "ScaleCut_Projects"),
        K["prev_type"]: list(PROJECT_TEMPLATES.keys())[0],
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

_init_state()

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("✂️ ScaleCut")
    st.caption(f"v{__version__}")
    st.divider()
    st.subheader("Plantillas")
    for name, info in PROJECT_TEMPLATES.items():
        icon = TEMPLATE_ICONS.get(name, "📁")
        with st.expander(f"{icon} {name}"):
            st.write(info["description"])
            st.caption("**Plataformas:** " + ", ".join(info["suggested_platforms"]))
            st.caption("**Formatos:** " + ", ".join(info["suggested_formats"]))
            if info.get("notes"):
                st.info(info["notes"], icon="💡")
    st.divider()
    st.subheader("Plataforma → formato")
    for platform, fmts in PLATFORM_FORMATS.items():
        st.caption(f"**{platform}** → {', '.join(fmts)}")

# ── Hero ──────────────────────────────────────────────────────────────────────

st.markdown("# ✂️ ScaleCut")
st.markdown(
    "**De brief a carpetas, checklists y nombres de archivo en 10 segundos.** "
    "Estructura tu próximo proyecto de video sin perder tiempo en naming manual."
)
st.code("NIKE_VERANO24_Clip01_INSTA_9x16_20241215_V01.mp4", language=None)
st.divider()

# ── Demo button ───────────────────────────────────────────────────────────────

col_demo, col_spacer = st.columns([2, 5])
with col_demo:
    if st.button("🎬 Cargar proyecto demo", use_container_width=True):
        st.session_state[K["proj_type"]] = DEMO_PROJECT["project_type"]
        st.session_state[K["client"]]    = DEMO_PROJECT["client"]
        st.session_state[K["project"]]   = DEMO_PROJECT["project"]
        st.session_state[K["date"]]      = date.fromisoformat(DEMO_PROJECT["delivery_date"])
        st.session_state[K["clips"]]     = DEMO_PROJECT["num_clips"]
        st.session_state[K["platforms"]] = list(DEMO_PROJECT["platforms"])
        st.session_state[K["formats"]]   = list(DEMO_PROJECT["formats"])
        st.session_state[K["version"]]   = DEMO_PROJECT["version"]
        st.session_state[K["language"]]  = DEMO_PROJECT["language"]
        st.session_state[K["status"]]    = DEMO_PROJECT["initial_status"]
        st.session_state[K["prev_type"]] = DEMO_PROJECT["project_type"]
        st.rerun()
with col_spacer:
    st.caption("Carga el caso Acme Studio / Podcast Leadership con un clic. Puedes editar todos los campos después.")

# ── Template card ─────────────────────────────────────────────────────────────

st.subheader("¿Qué tipo de proyecto es?")

template_options = list(PROJECT_TEMPLATES.keys())
project_type = st.selectbox(
    "Plantilla",
    options=template_options,
    index=template_options.index(st.session_state[K["proj_type"]]),
    format_func=lambda n: f"{TEMPLATE_ICONS.get(n, '📁')}  {n}",
    key=K["proj_type"],
    label_visibility="collapsed",
)
template = PROJECT_TEMPLATES[project_type]

# Auto-reset platforms/formats when template changes
if st.session_state[K["prev_type"]] != project_type:
    st.session_state[K["platforms"]] = list(template["suggested_platforms"])
    st.session_state[K["formats"]]   = list(template["suggested_formats"])
    st.session_state[K["prev_type"]] = project_type
    st.rerun()

icon = TEMPLATE_ICONS.get(project_type, "📁")
with st.container(border=True):
    ci, ct = st.columns([1, 9])
    with ci:
        st.markdown(f"## {icon}")
    with ct:
        st.markdown(f"**{project_type}**  \n{template['description']}")
        chips_plat = "  ".join([f"`{p}`" for p in template["suggested_platforms"]])
        chips_fmt  = "  ".join([f"`{f}`" for f in template["suggested_formats"]])
        st.markdown(f"🎯 {chips_plat}  &nbsp;&nbsp;  📐 {chips_fmt}")
        if template.get("notes"):
            st.caption(f"💡 {template['notes']}")

st.divider()

# ── Form inputs (outside st.form for live reactivity) ─────────────────────────

st.subheader("Datos del proyecto")

col_left, col_right = st.columns(2, gap="large")

with col_left:
    client = st.text_input(
        "Cliente *",
        placeholder="Nike, Acme Studio, María García…",
        key=K["client"],
    )
    project_name = st.text_input(
        "Proyecto *",
        placeholder="Campaña Verano, Podcast Leadership…",
        key=K["project"],
    )
    delivery_date = st.date_input("Fecha de entrega", key=K["date"])
    num_clips = st.number_input(
        "Número de clips",
        min_value=1,
        max_value=200,
        key=K["clips"],
    )

with col_right:
    platforms = st.multiselect(
        "Plataformas *",
        options=ALL_PLATFORMS,
        key=K["platforms"],
    )

    auto_formats = sorted(
        {fmt for p in platforms for fmt in PLATFORM_FORMATS.get(p, [])}
    )
    if auto_formats:
        st.caption(f"📐 Recomendados para tus plataformas: **{', '.join(auto_formats)}**")

    formats = st.multiselect(
        "Formatos *",
        options=ALL_FORMATS,
        key=K["formats"],
    )

    if platforms and formats:
        total_live = int(num_clips) * len(platforms) * len(formats)
        st.success(
            f"**{int(num_clips)} clips × {len(platforms)} plataformas × "
            f"{len(formats)} formatos = {total_live} entregables**"
        )

    cv, cl = st.columns(2)
    with cv:
        version  = st.text_input("Versión", key=K["version"])
        language = st.selectbox("Idioma", ["ES", "EN", "PT", "FR", "DE", "Other"], key=K["language"])
    with cl:
        initial_status = st.selectbox("Estado inicial", STATUSES, key=K["status"])

with st.expander("⚙️ Configuración avanzada"):
    output_path = st.text_input(
        "Ruta de salida",
        key=K["output"],
        help="Carpeta donde se creará el proyecto. Se crea automáticamente si no existe.",
    )
    st.caption("Puedes cambiarlo si quieres guardar el proyecto en otro lugar.")

st.divider()

# ── Executive summary ─────────────────────────────────────────────────────────

_can_preview = bool(client and project_name and platforms and formats)

if _can_preview:
    total_est     = int(num_clips) * len(platforms) * len(formats)
    client_slug   = sanitize(client)
    project_slug  = sanitize(project_name)
    date_slug     = str(delivery_date).replace("-", "")
    folder_name   = f"{client_slug}_{project_slug}_{date_slug}"
    estimated_path = Path(output_path) / folder_name

    with st.container(border=True):
        st.markdown("### 📋 Resumen ejecutivo")
        es1, es2 = st.columns(2)

        with es1:
            st.markdown(f"**Total de entregables:** {total_est}")
            st.markdown(f"**Clips:** {int(num_clips)}")
            st.markdown(f"**Plataformas:** {', '.join(platforms)}")
            st.markdown(f"**Formatos:** {', '.join(formats)}")
            st.markdown(f"**Fecha de entrega:** {delivery_date}")
            st.markdown(f"**Ruta estimada del proyecto:**")
            st.code(str(estimated_path), language=None)

        with es2:
            st.markdown("**Archivos que se generarán:**")
            for f in ADMIN_FILES:
                st.markdown(f"  ✓ `{f}`")

    st.divider()

generate = st.button("✂️ Generar proyecto", type="primary", use_container_width=True)

# ── Validation & generation ───────────────────────────────────────────────────

if generate:
    errors = []
    if not client.strip():       errors.append("El nombre del cliente es obligatorio.")
    if not project_name.strip(): errors.append("El nombre del proyecto es obligatorio.")
    if not platforms:            errors.append("Selecciona al menos una plataforma.")
    if not formats:              errors.append("Selecciona al menos un formato.")

    if errors:
        for e in errors:
            st.error(e)
    else:
        config = ProjectConfig(
            client=client.strip(),
            project=project_name.strip(),
            project_type=project_type,
            delivery_date=str(delivery_date),
            num_clips=int(num_clips),
            platforms=platforms,
            formats=formats,
            version=version.zfill(2),
            language=language,
            initial_status=initial_status,
            output_path=output_path.strip(),
        )
        with st.spinner("Generando estructura y archivos…"):
            root = create_folders(config)
            write_csv(config, root)
            write_markdown(config, root)
            write_naming_preview(config, root)
            write_editor_instructions(config, root)
            write_prompts_ai(config, root)
            write_config(config, root)
            write_readme(config, root)
            zip_bytes = create_zip(root)

        st.session_state["config"]       = config
        st.session_state["root"]         = root
        st.session_state["deliverables"] = generate_all_filenames(config)
        st.session_state["zip_bytes"]    = zip_bytes

# ── Results ───────────────────────────────────────────────────────────────────

if "config" in st.session_state:
    config      = st.session_state["config"]
    root        = st.session_state["root"]
    deliverables = st.session_state["deliverables"]
    zip_bytes   = st.session_state["zip_bytes"]
    total       = len(deliverables)
    zip_name    = f"{root.name}_scalecut.zip"

    st.divider()
    st.success(f"✅  **{root.name}** creado correctamente  —  `{root}`")

    rc1, rc2 = st.columns([3, 2])
    with rc1:
        # P0: CSV immediately visible
        st.download_button(
            label="⬇  Descargar delivery_checklist.csv",
            data=(root / "10_Admin" / "delivery_checklist.csv").read_bytes(),
            file_name="delivery_checklist.csv",
            mime="text/csv",
            type="primary",
            use_container_width=True,
            key="dl_csv_top",
        )
    with rc2:
        # ZIP download — main CTA alongside CSV
        st.download_button(
            label="📦  Descargar paquete ZIP completo",
            data=zip_bytes,
            file_name=zip_name,
            mime="application/zip",
            use_container_width=True,
            key="dl_zip_top",
        )

    st.divider()

    # Metrics
    mc1, mc2, mc3, mc4, mc5 = st.columns(5)
    mc1.metric("Total entregables", total, help="clips × plataformas × formatos")
    mc2.metric("Clips",             config.num_clips)
    mc3.metric("Plataformas",       len(config.platforms))
    mc4.metric("Formatos",          len(config.formats))
    mc5.metric("Versión",           f"V{config.version.zfill(2)}")

    st.divider()

    # Tabs — Naming first (P1)
    tab_naming, tab_del, tab_folders, tab_files = st.tabs(
        ["🏷️ Naming", "📋 Entregables", "📁 Carpetas", "📄 Más archivos"]
    )

    # ── Naming ────────────────────────────────────────────────────────────────
    with tab_naming:
        client_slug  = sanitize(config.client)
        project_slug = sanitize(config.project)
        date_slug    = config.delivery_date.replace("-", "")
        version_slug = f"V{config.version.zfill(2)}"

        st.markdown("**Patrón**")
        st.code("CLIENT_PROJECT_ClipNN_PLATFORM_FORMAT_YYYYMMDD_VNN.mp4", language=None)
        nc1, nc2 = st.columns(2)
        with nc1:
            st.markdown("**Tokens de este proyecto**")
            st.dataframe(
                pd.DataFrame([
                    {"Token": "CLIENT",  "Valor": client_slug},
                    {"Token": "PROJECT", "Valor": project_slug},
                    {"Token": "Date",    "Valor": date_slug},
                    {"Token": "Version", "Valor": version_slug},
                ]),
                hide_index=True,
                use_container_width=True,
            )
        with nc2:
            st.markdown("**Ejemplo real**")
            from scalecut.naming import build_filename
            example = build_filename(config, 1, config.platforms[0], config.formats[0])
            st.code(example, language=None)
            st.caption("Todos los archivos siguen exactamente este patrón.")

    # ── Entregables ───────────────────────────────────────────────────────────
    with tab_del:
        df = pd.DataFrame(deliverables)
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            f_clip = st.multiselect("Clip",       sorted(df["clip"].unique()),     key="f_clip")
        with fc2:
            f_plat = st.multiselect("Plataforma", sorted(df["platform"].unique()), key="f_plat")
        with fc3:
            f_fmt  = st.multiselect("Formato",    sorted(df["format"].unique()),   key="f_fmt")

        filtered = df.copy()
        if f_clip: filtered = filtered[filtered["clip"].isin(f_clip)]
        if f_plat: filtered = filtered[filtered["platform"].isin(f_plat)]
        if f_fmt:  filtered = filtered[filtered["format"].isin(f_fmt)]

        st.dataframe(
            filtered[["clip", "platform", "format", "filename"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "clip":     st.column_config.TextColumn("Clip",       width="small"),
                "platform": st.column_config.TextColumn("Plataforma", width="medium"),
                "format":   st.column_config.TextColumn("Formato",    width="small"),
                "filename": st.column_config.TextColumn("Filename"),
            },
        )
        st.caption(f"Mostrando **{len(filtered)}** de **{total}** entregables")

    # ── Carpetas ──────────────────────────────────────────────────────────────
    with tab_folders:
        lines = [f"{root.name}/"]
        for folder in build_folder_tree(config):
            depth  = folder.count("/")
            indent = "  " * (depth + 1)
            name   = folder.split("/")[-1]
            hint   = FOLDER_HINTS.get(name, "")
            lines.append(f"{indent}{name}/" + (f"   ← {hint}" if hint else ""))
        st.code("\n".join(lines), language=None)
        st.caption(f"📍 `{root}`")

    # ── Más archivos ──────────────────────────────────────────────────────────
    with tab_files:
        other_files = [
            (root / "10_Admin" / "delivery_checklist.md",   "text/markdown",    "Checklist con checkboxes por clip"),
            (root / "10_Admin" / "naming_preview.md",       "text/markdown",    "Todos los filenames por clip y plataforma"),
            (root / "10_Admin" / "editor_instructions.md",  "text/markdown",    "Instrucciones completas para Premiere / Resolve"),
            (root / "10_Admin" / "prompts_ai.md",           "text/markdown",    "6 prompts de IA listos para usar"),
            (root / "10_Admin" / "project_config.json",     "application/json", "Datos completos del proyecto (JSON)"),
            (root / "README.md",                            "text/markdown",    "Briefing del proyecto"),
        ]

        for path, mime, description in other_files:
            dc, db = st.columns([3, 1])
            with dc:
                st.markdown(f"**`{path.name}`** — {description}")
            with db:
                st.download_button(
                    label="⬇ Descargar",
                    data=path.read_bytes(),
                    file_name=path.name,
                    mime=mime,
                    use_container_width=True,
                    key=f"dl_{path.name}",
                )

        st.divider()
        st.download_button(
            label="📦  Descargar paquete ZIP completo",
            data=zip_bytes,
            file_name=zip_name,
            mime="application/zip",
            type="primary",
            use_container_width=True,
            key="dl_zip_bottom",
        )
