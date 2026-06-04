"""ScaleCut — Streamlit web UI."""

from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from scalecut import __version__
from scalecut.checklist import write_csv, write_markdown
from scalecut.config_gen import write_config
from scalecut.folders import build_folder_tree, create_folders
from scalecut.models import ProjectConfig
from scalecut.naming import generate_all_filenames, sanitize
from scalecut.preview import write_naming_preview
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
    "Podcast Repurposing":            "🎙️",
    "Reels/Shorts para marca personal": "📱",
    "Campaña publicitaria":           "📢",
    "Curso online":                   "🎓",
    "Testimoniales":                  "💬",
    "UGC Content":                    "📲",
    "YouTube long-form + Shorts":     "▶️",
}

FOLDER_HINTS = {
    "01_Footage":      "archivos de cámara y capturas",
    "02_Audio":        "música, voz en off, SFX",
    "03_Graphics":     "motion graphics, overlays",
    "04_Project_Files":"archivos .prproj / .drp",
    "05_Sequences":    "secuencias de edición",
    "06_Subtitles":    "archivos .srt / .vtt",
    "07_Exports":      "exports por formato",
    "08_Delivery":     "entregables aprobados",
    "09_References":   "briefs y referencias del cliente",
    "10_Admin":        "checklists y config del proyecto",
}

# ── Sidebar — reference ───────────────────────────────────────────────────────

with st.sidebar:
    st.title("✂️ ScaleCut")
    st.caption(f"v{__version__}")
    st.divider()
    st.subheader("Referencia de plantillas")
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

# ── P0: Hero ──────────────────────────────────────────────────────────────────

st.markdown("# ✂️ ScaleCut")
st.markdown(
    "**De brief a carpetas, checklists y nombres de archivo en 10 segundos.** "
    "Estructura tu próximo proyecto de video sin perder tiempo en naming manual."
)
st.code(
    "NIKE_VERANO24_Clip01_INSTA_9x16_20241215_V01.mp4",
    language=None,
)
st.divider()

# ── P1: Template card ─────────────────────────────────────────────────────────

st.subheader("¿Qué tipo de proyecto es?")

project_type = st.selectbox(
    "Plantilla",
    options=list(PROJECT_TEMPLATES.keys()),
    format_func=lambda name: f"{TEMPLATE_ICONS.get(name, '📁')}  {name}",
    label_visibility="collapsed",
)
template = PROJECT_TEMPLATES[project_type]
icon = TEMPLATE_ICONS.get(project_type, "📁")

with st.container(border=True):
    col_icon, col_info = st.columns([1, 9])
    with col_icon:
        st.markdown(f"## {icon}")
    with col_info:
        st.markdown(f"**{project_type}**  \n{template['description']}")
        chips_plat = "  ".join([f"`{p}`" for p in template["suggested_platforms"]])
        chips_fmt  = "  ".join([f"`{f}`" for f in template["suggested_formats"]])
        st.markdown(f"🎯 {chips_plat}  &nbsp;&nbsp;  📐 {chips_fmt}")
        if template.get("notes"):
            st.caption(f"💡 {template['notes']}")

st.divider()

# ── Form ──────────────────────────────────────────────────────────────────────

st.subheader("Datos del proyecto")

col_left, col_right = st.columns(2, gap="large")

with col_left:
    client = st.text_input(
        "Cliente *",
        placeholder="Nike, Acme Studio, María García...",
    )
    project_name = st.text_input(
        "Proyecto *",
        placeholder="Campaña Verano, Lanzamiento Q4...",
    )
    delivery_date = st.date_input("Fecha de entrega", value=date.today())
    num_clips = st.number_input(
        "Número de clips",
        min_value=1,
        max_value=200,
        value=int(template.get("typical_clips", 5)),
    )

with col_right:
    platforms = st.multiselect(
        "Plataformas *",
        options=ALL_PLATFORMS,
        default=template.get("suggested_platforms", []),
        key=f"platforms_{project_type}",   # resets when template changes
    )

    # Live format hint
    auto_formats = sorted(
        {fmt for p in platforms for fmt in PLATFORM_FORMATS.get(p, [])}
    )
    if auto_formats:
        st.caption(f"📐 Formatos recomendados para tus plataformas: **{', '.join(auto_formats)}**")

    formats = st.multiselect(
        "Formatos *",
        options=ALL_FORMATS,
        default=template.get("suggested_formats", ["9x16"]),
        key=f"formats_{project_type}",
    )

    # Live deliverable count
    if client and project_name and platforms and formats:
        total_live = int(num_clips) * len(platforms) * len(formats)
        st.success(
            f"**{int(num_clips)} clips × {len(platforms)} plataformas × "
            f"{len(formats)} formatos = {total_live} entregables**"
        )
    elif platforms and formats:
        total_live = int(num_clips) * len(platforms) * len(formats)
        st.info(
            f"{int(num_clips)} × {len(platforms)} × {len(formats)} = **{total_live} entregables**"
        )

    col_v, col_l = st.columns(2)
    with col_v:
        version  = st.text_input("Versión", value="01")
        language = st.selectbox("Idioma", ["ES", "EN", "PT", "FR", "DE", "Other"])
    with col_l:
        initial_status = st.selectbox("Estado inicial", STATUSES)

# P0: output path hidden in advanced expander
with st.expander("⚙️ Configuración avanzada"):
    output_path = st.text_input(
        "Ruta de salida",
        value=str(Path.home() / "Desktop" / "ScaleCut_Projects"),
        help="Carpeta donde se creará el proyecto. Se crea automáticamente si no existe.",
    )
    st.caption("Puedes cambiarlo si quieres guardar el proyecto en otro lugar.")

st.divider()

generate = st.button("✂️ Generar proyecto", type="primary", use_container_width=True)

# ── Validation & generation ───────────────────────────────────────────────────

if generate:
    errors = []
    if not client.strip():      errors.append("El nombre del cliente es obligatorio.")
    if not project_name.strip():errors.append("El nombre del proyecto es obligatorio.")
    if not platforms:           errors.append("Selecciona al menos una plataforma.")
    if not formats:             errors.append("Selecciona al menos un formato.")

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
        with st.spinner("Generando estructura y archivos..."):
            root = create_folders(config)
            write_csv(config, root)
            write_markdown(config, root)
            write_naming_preview(config, root)
            write_config(config, root)
            write_readme(config, root)

        st.session_state["config"]       = config
        st.session_state["root"]         = root
        st.session_state["deliverables"] = generate_all_filenames(config)

# ── Results ───────────────────────────────────────────────────────────────────

if "config" in st.session_state:
    config      = st.session_state["config"]
    root        = st.session_state["root"]
    deliverables = st.session_state["deliverables"]

    st.divider()

    # Success banner
    st.success(f"✅  **{root.name}** creado correctamente  —  `{root}`")

    # P0: CSV download immediately visible, no tab navigation needed
    csv_bytes = (root / "10_Admin" / "delivery_checklist.csv").read_bytes()
    st.download_button(
        label="⬇  Descargar delivery_checklist.csv",
        data=csv_bytes,
        file_name="delivery_checklist.csv",
        mime="text/csv",
        type="primary",
        use_container_width=True,
        key="dl_csv_top",
    )

    st.divider()

    # Metrics — total deliverables highlighted
    total = len(deliverables)
    mc1, mc2, mc3, mc4, mc5 = st.columns(5)
    mc1.metric("Total entregables",  total, help="clips × plataformas × formatos")
    mc2.metric("Clips",              config.num_clips)
    mc3.metric("Plataformas",        len(config.platforms))
    mc4.metric("Formatos",           len(config.formats))
    mc5.metric("Versión",            f"V{config.version.zfill(2)}")

    st.divider()

    # P1: tabs reordered — Naming first
    tab_naming, tab_del, tab_folders, tab_files = st.tabs(
        ["🏷️ Naming", "📋 Entregables", "📁 Carpetas", "📄 Más archivos"]
    )

    # ── Tab: Naming (first) ───────────────────────────────────────────────────
    with tab_naming:
        client_slug  = sanitize(config.client)
        project_slug = sanitize(config.project)
        date_slug    = config.delivery_date.replace("-", "")
        version_slug = f"V{config.version.zfill(2)}"

        st.markdown("**Patrón de naming**")
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
            example = f"{client_slug}_{project_slug}_Clip01_INSTA_9x16_{date_slug}_{version_slug}.mp4"
            st.code(example, language=None)
            st.caption("El nombre completo de cada archivo sigue exactamente este patrón.")

    # ── Tab: Entregables ──────────────────────────────────────────────────────
    with tab_del:
        df = pd.DataFrame(deliverables)

        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            f_clip = st.multiselect("Clip",        sorted(df["clip"].unique()),     key="f_clip")
        with fc2:
            f_plat = st.multiselect("Plataforma",  sorted(df["platform"].unique()), key="f_plat")
        with fc3:
            f_fmt  = st.multiselect("Formato",     sorted(df["format"].unique()),   key="f_fmt")

        filtered = df.copy()
        if f_clip: filtered = filtered[filtered["clip"].isin(f_clip)]
        if f_plat: filtered = filtered[filtered["platform"].isin(f_plat)]
        if f_fmt:  filtered = filtered[filtered["format"].isin(f_fmt)]

        # P1: hide status column — not useful when all rows are identical
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

    # ── Tab: Folder structure ─────────────────────────────────────────────────
    with tab_folders:
        lines = [f"{root.name}/"]
        for folder in build_folder_tree(config):
            depth  = folder.count("/")
            indent = "  " * (depth + 1)
            name   = folder.split("/")[-1]
            hint   = FOLDER_HINTS.get(name, "")
            hint_str = f"   ← {hint}" if hint else ""
            lines.append(f"{indent}{name}/{hint_str}")
        st.code("\n".join(lines), language=None)
        st.caption(f"📍 `{root}`")

    # ── Tab: More files ───────────────────────────────────────────────────────
    with tab_files:
        st.markdown("**Archivos adicionales del proyecto**")

        other_files = [
            (root / "10_Admin" / "delivery_checklist.md",  "text/markdown",      "Checklist con checkboxes por clip (Markdown)"),
            (root / "10_Admin" / "naming_preview.md",      "text/markdown",      "Todos los filenames por clip y plataforma"),
            (root / "10_Admin" / "project_config.json",    "application/json",   "Datos completos del proyecto (JSON)"),
            (root / "README.md",                           "text/markdown",      "Briefing del proyecto con estructura y workflow"),
        ]

        for path, mime, description in other_files:
            col_desc, col_btn = st.columns([3, 1])
            with col_desc:
                st.markdown(f"**`{path.name}`** — {description}")
            with col_btn:
                st.download_button(
                    label="⬇ Descargar",
                    data=path.read_bytes(),
                    file_name=path.name,
                    mime=mime,
                    use_container_width=True,
                    key=f"dl_{path.name}",
                )
