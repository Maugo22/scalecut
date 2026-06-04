"""ScaleCut — Streamlit web UI."""

import sys
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from scalecut import __version__
from scalecut.config_gen import write_config
from scalecut.checklist import write_csv, write_markdown
from scalecut.folders import build_folder_tree, create_folders
from scalecut.models import ProjectConfig
from scalecut.naming import generate_all_filenames
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
    initial_sidebar_state="expanded",
)

# ── Sidebar — template reference ──────────────────────────────────────────────

with st.sidebar:
    st.title("✂️ ScaleCut")
    st.caption(f"v{__version__}")
    st.divider()

    st.subheader("Plantillas disponibles")
    for name, info in PROJECT_TEMPLATES.items():
        with st.expander(name, expanded=False):
            st.write(info["description"])
            st.caption(f"🎯 {', '.join(info['suggested_platforms'])}")
            st.caption(f"📐 {', '.join(info['suggested_formats'])}")
            if info.get("notes"):
                st.info(info["notes"], icon="💡")

    st.divider()
    st.subheader("Reglas plataforma → formato")
    for platform, formats in PLATFORM_FORMATS.items():
        st.caption(f"**{platform}** → {', '.join(formats)}")

# ── Main area ─────────────────────────────────────────────────────────────────

st.header("Nuevo proyecto")

# ── Template picker (outside form → reactive) ─────────────────────────────────

project_type = st.selectbox(
    "Tipo de proyecto",
    options=list(PROJECT_TEMPLATES.keys()),
    help="Selecciona la plantilla que mejor describe tu proyecto.",
)
template = PROJECT_TEMPLATES[project_type]
st.caption(f"→ {template['description']}")
if template.get("notes"):
    st.caption(f"💡 {template['notes']}")

st.divider()

# ── Form ──────────────────────────────────────────────────────────────────────

with st.form("project_form", border=False):

    col_left, col_right = st.columns(2, gap="large")

    # ── Left column: project identity ─────────────────────────────────────────
    with col_left:
        st.markdown("#### Información del proyecto")

        client = st.text_input(
            "Cliente *",
            placeholder="Acme Studio",
            help="Nombre del cliente tal como aparecerá en los archivos.",
        )
        project_name = st.text_input(
            "Proyecto *",
            placeholder="Lanzamiento Q4",
        )
        delivery_date = st.date_input(
            "Fecha de entrega",
            value=date.today(),
        )
        num_clips = st.number_input(
            "Número de clips",
            min_value=1,
            max_value=200,
            value=int(template.get("typical_clips", 5)),
        )
        output_path = st.text_input(
            "Ruta de salida",
            value=str(Path.home() / "Desktop" / "ScaleCut_Projects"),
            help="Carpeta donde se creará el proyecto.",
        )

    # ── Right column: production scope ────────────────────────────────────────
    with col_right:
        st.markdown("#### Alcance de producción")

        platforms = st.multiselect(
            "Plataformas *",
            options=ALL_PLATFORMS,
            default=template.get("suggested_platforms", []),
            help="Selecciona todas las plataformas destino.",
        )

        # Hint: auto-detected formats
        auto_formats = sorted(
            {fmt for p in platforms for fmt in PLATFORM_FORMATS.get(p, [])}
        )
        if auto_formats:
            st.caption(f"📐 Formatos detectados para tus plataformas: **{', '.join(auto_formats)}**")

        formats = st.multiselect(
            "Formatos *",
            options=ALL_FORMATS,
            default=template.get("suggested_formats", ["9x16"]),
            help="Formatos de exportación a producir.",
        )

        if platforms and formats:
            total = int(num_clips) * len(platforms) * len(formats)
            st.success(
                f"**{int(num_clips)} clips × {len(platforms)} plataformas × "
                f"{len(formats)} formatos = {total} entregables**"
            )

        st.markdown("#### Versión e idioma")

        col_v, col_l = st.columns(2)
        with col_v:
            version = st.text_input("Versión inicial", value="01")
            language = st.selectbox("Idioma", ["ES", "EN", "PT", "FR", "DE", "Other"])
        with col_l:
            initial_status = st.selectbox("Estado inicial", STATUSES)

    st.divider()
    submitted = st.form_submit_button(
        "🚀  Generar proyecto",
        type="primary",
        use_container_width=True,
    )

# ── Validation & generation ───────────────────────────────────────────────────

if submitted:
    errors = []
    if not client.strip():
        errors.append("El nombre del cliente es obligatorio.")
    if not project_name.strip():
        errors.append("El nombre del proyecto es obligatorio.")
    if not platforms:
        errors.append("Selecciona al menos una plataforma.")
    if not formats:
        errors.append("Selecciona al menos un formato.")

    if errors:
        for err in errors:
            st.error(err)
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
    config: ProjectConfig = st.session_state["config"]
    root: Path            = st.session_state["root"]
    deliverables: list    = st.session_state["deliverables"]

    st.divider()
    st.success(f"✅  **{root.name}** creado correctamente")

    # ── Metrics ───────────────────────────────────────────────────────────────
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Clips",        config.num_clips)
    m2.metric("Plataformas",  len(config.platforms))
    m3.metric("Formatos",     len(config.formats))
    m4.metric("Entregables",  len(deliverables))
    m5.metric("Versión",      f"V{config.version.zfill(2)}")

    st.divider()

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_del, tab_folders, tab_naming, tab_files = st.tabs(
        ["📋 Entregables", "📁 Carpetas", "🏷️ Naming", "📄 Descargar archivos"]
    )

    # ── Tab: Deliverables ─────────────────────────────────────────────────────
    with tab_del:
        df = pd.DataFrame(deliverables)

        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            f_clip = st.multiselect(
                "Clip", sorted(df["clip"].unique()), key="f_clip"
            )
        with fc2:
            f_plat = st.multiselect(
                "Plataforma", sorted(df["platform"].unique()), key="f_plat"
            )
        with fc3:
            f_fmt = st.multiselect(
                "Formato", sorted(df["format"].unique()), key="f_fmt"
            )

        filtered = df.copy()
        if f_clip: filtered = filtered[filtered["clip"].isin(f_clip)]
        if f_plat: filtered = filtered[filtered["platform"].isin(f_plat)]
        if f_fmt:  filtered = filtered[filtered["format"].isin(f_fmt)]

        st.dataframe(
            filtered[["clip", "platform", "format", "status", "filename"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "clip":     st.column_config.TextColumn("Clip",      width="small"),
                "platform": st.column_config.TextColumn("Plataforma"),
                "format":   st.column_config.TextColumn("Formato",   width="small"),
                "status":   st.column_config.TextColumn("Estado"),
                "filename": st.column_config.TextColumn("Filename"),
            },
        )
        st.caption(
            f"Mostrando **{len(filtered)}** de **{len(deliverables)}** entregables"
        )

    # ── Tab: Folder structure ─────────────────────────────────────────────────
    with tab_folders:
        lines = [f"{root.name}/"]
        for folder in build_folder_tree(config):
            depth = folder.count("/")
            indent = "  " * (depth + 1)
            name   = folder.split("/")[-1]
            lines.append(f"{indent}{name}/")
        st.code("\n".join(lines), language=None)
        st.caption(f"📍 `{root}`")

    # ── Tab: Naming preview ───────────────────────────────────────────────────
    with tab_naming:
        from scalecut.naming import sanitize
        client_slug  = sanitize(config.client)
        project_slug = sanitize(config.project)
        date_slug    = config.delivery_date.replace("-", "")
        version_slug = f"V{config.version.zfill(2)}"

        st.markdown("**Patrón de naming**")
        st.code("CLIENT_PROJECT_ClipNN_PLATFORM_FORMAT_YYYYMMDD_VNN.mp4", language=None)

        tc1, tc2 = st.columns(2)
        with tc1:
            st.markdown("**Tokens del proyecto**")
            token_df = pd.DataFrame([
                {"Token": "CLIENT",   "Valor": client_slug},
                {"Token": "PROJECT",  "Valor": project_slug},
                {"Token": "Date",     "Valor": date_slug},
                {"Token": "Version",  "Valor": version_slug},
            ])
            st.dataframe(token_df, hide_index=True, use_container_width=True)
        with tc2:
            st.markdown("**Ejemplo**")
            example = (
                f"{client_slug}_{project_slug}_Clip01_INSTA_9x16"
                f"_{date_slug}_{version_slug}.mp4"
            )
            st.code(example, language=None)

    # ── Tab: Download files ───────────────────────────────────────────────────
    with tab_files:
        files = [
            (root / "10_Admin" / "delivery_checklist.csv",  "text/csv"),
            (root / "10_Admin" / "delivery_checklist.md",   "text/markdown"),
            (root / "10_Admin" / "naming_preview.md",       "text/markdown"),
            (root / "10_Admin" / "project_config.json",     "application/json"),
            (root / "README.md",                            "text/markdown"),
        ]

        dl1, dl2 = st.columns(2)
        for i, (path, mime) in enumerate(files):
            col = dl1 if i % 2 == 0 else dl2
            with col:
                st.download_button(
                    label=f"⬇  {path.name}",
                    data=path.read_bytes(),
                    file_name=path.name,
                    mime=mime,
                    use_container_width=True,
                    key=f"dl_{path.name}",
                )

        st.divider()
        st.info(f"📁 Proyecto completo en:\n\n`{root}`")
