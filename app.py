"""ScaleCut — Streamlit web UI."""

from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from scalecut import __version__
from scalecut.checklist import write_csv, write_markdown
from scalecut.config_gen import write_config
from scalecut.edit_plan import (
    EditPlanClip, make_placeholder_clips,
    write_edit_plan_csv, write_edit_plan_md, write_edit_plan_json, write_markers_csv,
    validate_timecodes, calculate_duration, timecode_to_seconds,
)
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

# Dynamic filename example — updates live as the user fills the form
_c     = st.session_state.get(K["client"],    "").strip()
_p     = st.session_state.get(K["project"],   "").strip()
_d     = str(st.session_state.get(K["date"],  date.today())).replace("-", "")
_plats = st.session_state.get(K["platforms"], [])
_fmts  = st.session_state.get(K["formats"],   [])
_ver   = st.session_state.get(K["version"],   "01")

if _c and _p and _plats and _fmts:
    from scalecut.naming import platform_slug as _pslug
    _hero = (
        f"{sanitize(_c)}_{sanitize(_p)}_Clip01"
        f"_{_pslug(_plats[0])}_{_fmts[0]}"
        f"_{_d}_V{_ver.zfill(2)}.mp4"
    )
else:
    _hero = "CLIENTE_PROYECTO_Clip01_PLATAFORMA_FORMATO_FECHA_V01.mp4"

st.code(_hero, language=None)
st.divider()

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

# ── Edit Plan ─────────────────────────────────────────────────────────────────

with st.expander("📝 Edit Plan  —  timestamps, goals y hooks por clip", expanded=False):
    ep_enabled = st.toggle(
        "Activar generación de Edit Plan",
        value=False,
        key="ep_enabled",
        help="Genera edit_plan.csv / .md / .json y markers.csv con los datos de cada clip.",
    )

    if ep_enabled:
        ep_mode = st.radio(
            "Modo",
            ["Placeholder (vacío)", "Manual (ingresar datos ahora)"],
            horizontal=True,
            key="ep_mode",
        )

        if "Placeholder" in ep_mode:
            st.info(
                "Se generará un edit plan vacío con todos los entregables. "
                "Rellena los timecodes y datos creativos en `10_Admin/edit_plan.csv` "
                "después de generar el proyecto.",
                icon="ℹ️",
            )
            if platforms and formats:
                total_ep = int(num_clips) * len(platforms) * len(formats)
                st.caption(f"Se crearán **{total_ep} filas** — una por entregable.")

        else:  # Manual mode
            if int(num_clips) > 15:
                st.warning(
                    "El modo manual está optimizado para proyectos de hasta 15 clips. "
                    "Para proyectos grandes usa el modo Placeholder y rellena el CSV después.",
                    icon="⚠️",
                )

            st.caption(
                "Introduce los datos de cada clip. El mismo timecode y goal se aplica "
                "a todos los formatos de ese clip."
            )

            for clip_n in range(1, min(int(num_clips) + 1, 16)):
                clip_id = f"Clip{clip_n:02d}"
                with st.expander(f"📎 {clip_id}", expanded=(clip_n == 1)):
                    mc1, mc2, mc3 = st.columns(3)

                    with mc1:
                        st.markdown("**Timecodes**")
                        ep_start = st.text_input(
                            "Start TC",
                            placeholder="00:00:10:00",
                            key=f"ep_start_{clip_id}",
                        )
                        ep_end = st.text_input(
                            "End TC",
                            placeholder="00:01:25:00",
                            key=f"ep_end_{clip_id}",
                        )
                        if ep_start or ep_end:
                            valid, err = validate_timecodes(ep_start, ep_end)
                            if valid and ep_start and ep_end:
                                dur = calculate_duration(ep_start, ep_end)
                                if dur:
                                    secs = timecode_to_seconds(dur)
                                    st.caption(f"⏱ {dur}  (~{int(secs)}s)")
                            elif not valid:
                                st.error(err)

                    with mc2:
                        st.markdown("**Creatividad**")
                        st.text_input("Goal",   placeholder="brand awareness / engagement / conversion",
                                      key=f"ep_goal_{clip_id}")
                        st.text_input("Hook",   placeholder="Frase de apertura (máx 15 palabras)",
                                      key=f"ep_hook_{clip_id}")
                        st.text_input("Título", placeholder="Título sugerido",
                                      key=f"ep_title_{clip_id}")

                    with mc3:
                        st.markdown("**Copy**")
                        st.text_input("CTA",   placeholder="Call to action",
                                      key=f"ep_cta_{clip_id}")
                        st.text_area("Notas",  placeholder="Instrucciones para el editor",
                                     key=f"ep_notes_{clip_id}", height=130)

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

            # Edit Plan generation
            ep_clips = None
            if st.session_state.get("ep_enabled", False):
                ep_mode_val = st.session_state.get("ep_mode", "Placeholder (vacío)")
                if "Placeholder" in ep_mode_val:
                    ep_clips = make_placeholder_clips(config)
                    ep_json_mode = "placeholder"
                else:
                    from scalecut.naming import build_filename as _bfn
                    ep_clips = []
                    for clip_n in range(1, config.num_clips + 1):
                        clip_id = f"Clip{clip_n:02d}"
                        _start = st.session_state.get(f"ep_start_{clip_id}", "")
                        _end   = st.session_state.get(f"ep_end_{clip_id}", "")
                        _dur   = calculate_duration(_start, _end) if _start and _end else ""
                        _goal  = st.session_state.get(f"ep_goal_{clip_id}", "")
                        _hook  = st.session_state.get(f"ep_hook_{clip_id}", "")
                        _title = st.session_state.get(f"ep_title_{clip_id}", "")
                        _cta   = st.session_state.get(f"ep_cta_{clip_id}", "")
                        _notes = st.session_state.get(f"ep_notes_{clip_id}", "")
                        for platform in config.platforms:
                            for fmt in config.formats:
                                ep_clips.append(EditPlanClip(
                                    clip_id=clip_id,
                                    start_timecode=_start,
                                    end_timecode=_end,
                                    duration=_dur or "",
                                    platform=platform,
                                    format=fmt,
                                    goal=_goal,
                                    hook=_hook,
                                    title=_title,
                                    caption="",
                                    cta=_cta,
                                    notes=_notes,
                                    export_filename=_bfn(config, clip_n, platform, fmt),
                                    status=config.initial_status,
                                ))
                    ep_json_mode = "manual"

                write_edit_plan_csv(ep_clips, root)
                write_edit_plan_md(ep_clips, root, config)
                write_edit_plan_json(ep_clips, root, config, mode=ep_json_mode)
                write_markers_csv(ep_clips, root)

            zip_bytes = create_zip(root)

        st.session_state["config"]       = config
        st.session_state["root"]         = root
        st.session_state["deliverables"] = generate_all_filenames(config)
        st.session_state["zip_bytes"]    = zip_bytes
        st.session_state["ep_clips"]     = ep_clips

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

    # Tabs — Naming first (P1); Edit Plan tab visible only when generated
    ep_clips_result = st.session_state.get("ep_clips")
    tab_labels = ["🏷️ Naming", "📋 Entregables", "📁 Carpetas", "📄 Más archivos"]
    if ep_clips_result:
        tab_labels.append("📝 Edit Plan")
    tabs = st.tabs(tab_labels)
    tab_naming, tab_del, tab_folders, tab_files = tabs[0], tabs[1], tabs[2], tabs[3]
    tab_ep = tabs[4] if ep_clips_result else None

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

    # ── Edit Plan tab ─────────────────────────────────────────────────────────
    if tab_ep is not None and ep_clips_result:
        with tab_ep:
            ep_df = pd.DataFrame([
                {
                    "Clip":     c.clip_id,
                    "Start TC": c.start_timecode or "—",
                    "End TC":   c.end_timecode   or "—",
                    "Duración": c.duration        or "—",
                    "Platform": c.platform,
                    "Format":   c.format,
                    "Goal":     c.goal   or "—",
                    "Hook":     c.hook   or "—",
                    "Status":   c.status,
                    "Filename": c.export_filename,
                }
                for c in ep_clips_result
            ])

            efc1, efc2 = st.columns(2)
            with efc1:
                ef_clip = st.multiselect("Clip",       sorted(ep_df["Clip"].unique()),     key="ef_clip")
            with efc2:
                ef_plat = st.multiselect("Plataforma", sorted(ep_df["Platform"].unique()), key="ef_plat")

            ep_filtered = ep_df.copy()
            if ef_clip: ep_filtered = ep_filtered[ep_filtered["Clip"].isin(ef_clip)]
            if ef_plat: ep_filtered = ep_filtered[ep_filtered["Platform"].isin(ef_plat)]

            st.dataframe(ep_filtered, use_container_width=True, hide_index=True)
            st.caption(f"{len(ep_filtered)} filas · {len(ep_clips_result)} total")

            st.divider()
            st.markdown("**Descargar archivos del Edit Plan**")

            ep_files = [
                (root / "10_Admin" / "edit_plan.csv",  "text/csv",         "edit_plan.csv  — tracker completo (Google Sheets)"),
                (root / "10_Admin" / "edit_plan.md",   "text/markdown",    "edit_plan.md   — plan legible por clip"),
                (root / "10_Admin" / "edit_plan.json", "application/json", "edit_plan.json — para plugin Premiere / Resolve"),
                (root / "10_Admin" / "markers.csv",    "text/csv",         "markers.csv    — marcadores con color por plataforma"),
            ]
            for ep_path, ep_mime, ep_label in ep_files:
                if ep_path.exists():
                    epc, epb = st.columns([3, 1])
                    with epc:
                        st.markdown(f"`{ep_label}`")
                    with epb:
                        st.download_button(
                            label="⬇ Descargar",
                            data=ep_path.read_bytes(),
                            file_name=ep_path.name,
                            mime=ep_mime,
                            use_container_width=True,
                            key=f"dl_ep_{ep_path.name}",
                        )

            st.info(
                "**edit_plan.json** está diseñado para ser leído por un plugin de "
                "Premiere Pro o DaVinci Resolve en una fase futura. "
                "Contiene todos los timecodes, goals y filenames que el plugin "
                "necesita para crear secuencias y marcadores automáticamente.",
                icon="🔌",
            )
