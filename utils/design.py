import streamlit as st

LIGHT = {
    "bg": "#FAFBFF",
    "surface": "#FFFFFF",
    "border": "#EAECFF",
    "border_light": "#F0F1FF",
    "text_primary": "#020066",
    "text_secondary": "#3D3F8F",
    "text_muted": "#8386C8",
    "text_faint": "#ACB0F8",
    "accent": "#5450FF",
    "accent_bg": "#F0F1FF",
    "accent_btn": "#020066",
    "accent_hover": "#3500D8",
    "success": "#166534",
    "success_bg": "#EAFFF2",
    "success_border": "#86EFAC",
    "error": "#D93025",
    "error_bg": "#FFF0F0",
    "warning": "#E8901A",
    "warning_bg": "#FFF4E8",
    "chip_bg": "#F0F1FF",
    "chip_border": "#E0E2FF",
    "chip_text": "#3D3F8F",
    "shadow": "rgba(84,80,255,0.06)",
    "shadow_btn": "rgba(2,0,102,0.18)",
    "shadow_hover": "rgba(53,0,216,0.28)",
    "logo": "#020066",
    "dot": "#5450FF",
    "spinner": "#5450FF",
}

DARK = {
    "bg": "#0B0B18",
    "surface": "#14142A",
    "border": "#262650",
    "border_light": "#1C1C3A",
    "text_primary": "#E8EAFF",
    "text_secondary": "#B0B4F0",
    "text_muted": "#6870C8",
    "text_faint": "#4A50A8",
    "accent": "#7B78FF",
    "accent_bg": "#1A1A40",
    "accent_btn": "#5450FF",
    "accent_hover": "#9895FF",
    "success": "#4ADE80",
    "success_bg": "#0A2010",
    "success_border": "#166534",
    "error": "#F87171",
    "error_bg": "#2D0A0A",
    "warning": "#FCD34D",
    "warning_bg": "#2A1800",
    "chip_bg": "#1A1A40",
    "chip_border": "#2D2D60",
    "chip_text": "#B0B4F0",
    "shadow": "rgba(0,0,0,0.4)",
    "shadow_btn": "rgba(84,80,255,0.25)",
    "shadow_hover": "rgba(155,152,255,0.35)",
    "logo": "#9895FF",
    "dot": "#7B78FF",
    "spinner": "#7B78FF",
}


def get_theme() -> dict:
    return DARK if st.session_state.get("dark_mode", False) else LIGHT


def toggle_dark_mode():
    st.session_state.dark_mode = not st.session_state.get("dark_mode", False)


def inject_css():
    c = get_theme()
    st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Geologica:wght@300;400;600;700;900&family=Abhaya+Libre:wght@400;600&display=swap');

html, body, [class*="css"], .stApp {{
    font-family: 'Abhaya Libre', Georgia, serif !important;
    background-color: {c['bg']} !important;
}}
#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{ padding-top: 2rem !important; padding-bottom: 3rem !important; max-width: 800px !important; }}

[data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"],
section[data-testid="stMain"] {{ background-color: {c['bg']} !important; }}
[data-testid="stSidebar"] {{ background-color: {c['surface']} !important; }}
[data-testid="stHeader"] {{ background-color: {c['bg']} !important; }}

.g-header {{
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 0 24px 0; margin-bottom: 8px; border-bottom: 1.5px solid {c['border']};
}}
.g-logo {{
    font-family: 'Geologica', sans-serif; font-weight: 900; font-size: 2rem;
    color: {c['logo']}; letter-spacing: -1.5px; line-height: 1;
}}
.g-logo-dot {{
    display: inline-block; width: 6px; height: 6px; background: {c['dot']};
    border-radius: 50%; margin-left: 3px; vertical-align: super;
}}
.g-header-right {{ text-align: right; }}
.g-header-title {{
    font-family: 'Geologica', sans-serif; font-weight: 600; font-size: 0.85rem;
    color: {c['text_primary']}; letter-spacing: 0.02em;
}}
.g-header-sub {{
    font-family: 'Abhaya Libre', serif; font-size: 0.78rem; color: {c['text_faint']}; margin-top: 1px;
}}

.g-section-label {{
    font-family: 'Geologica', sans-serif; font-weight: 600; font-size: 0.72rem;
    letter-spacing: 0.12em; text-transform: uppercase; color: {c['text_faint']};
    margin-bottom: 10px; margin-top: 24px;
}}

[data-testid="stTextInput"] label, [data-testid="stNumberInput"] label,
[data-testid="stSelectbox"] label, [data-testid="stDateInput"] label,
[data-testid="stTimeInput"] label, [data-testid="stRadio"] label,
[data-testid="stRadio"] span {{ color: {c['text_secondary']} !important; }}

[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input {{
    background-color: {c['surface']} !important;
    color: {c['text_secondary']} !important;
    border-color: {c['border']} !important;
}}
[data-testid="stSelectbox"] [data-baseweb="select"] > div {{
    background-color: {c['surface']} !important;
    border-color: {c['border']} !important;
    color: {c['text_secondary']} !important;
}}
[data-testid="stDateInput"] input, [data-testid="stTimeInput"] input {{
    background-color: {c['surface']} !important;
    color: {c['text_secondary']} !important;
    border-color: {c['border']} !important;
}}

.stButton > button {{
    background: {c['accent_btn']} !important; color: white !important;
    border: none !important; border-radius: 10px !important;
    font-family: 'Geologica', sans-serif !important; font-weight: 700 !important;
    font-size: 0.85rem !important; letter-spacing: 0.03em !important;
    padding: 10px 24px !important; width: 100% !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 8px {c['shadow_btn']} !important;
}}
.stButton > button:hover {{
    background: {c['accent_hover']} !important;
    box-shadow: 0 4px 16px {c['shadow_hover']} !important;
    transform: translateY(-1px) !important;
}}

.theme-toggle .stButton > button {{
    background: transparent !important;
    border: 1px solid {c['border']} !important;
    border-radius: 50% !important;
    width: 38px !important; height: 38px !important;
    padding: 0 !important; font-size: 1.1rem !important;
    box-shadow: none !important; color: {c['text_secondary']} !important;
    min-height: 0 !important;
}}
.theme-toggle .stButton > button:hover {{
    background: {c['accent_bg']} !important;
    transform: none !important; box-shadow: none !important;
}}

.stDownloadButton > button {{
    background: {c['accent_btn']} !important; color: white !important;
    border: none !important; border-radius: 10px !important;
    font-family: 'Geologica', sans-serif !important; font-weight: 700 !important;
    font-size: 0.85rem !important; padding: 10px 24px !important; width: 100% !important;
    box-shadow: 0 2px 8px {c['shadow_btn']} !important; transition: all 0.2s ease !important;
}}
.stDownloadButton > button:hover {{
    background: {c['accent_hover']} !important; transform: translateY(-1px) !important;
}}

[data-testid="stExpander"] {{
    background: {c['surface']} !important; border: 1px solid {c['border']} !important;
    border-radius: 14px !important; overflow: hidden !important; margin-top: 16px !important;
    box-shadow: 0 2px 16px {c['shadow']} !important;
}}
[data-testid="stExpander"] summary {{
    font-family: 'Geologica', sans-serif !important; font-weight: 700 !important;
    color: {c['text_primary']} !important; font-size: 0.88rem !important; padding: 14px 20px !important;
}}
[data-testid="stExpander"] > div > div {{ background: {c['surface']} !important; }}

hr[data-testid="stDivider"] {{ border-color: {c['border']} !important; margin: 20px 0 !important; }}

[data-testid="stFileUploaderDropzone"] {{
    background: {c['surface']} !important; border: 1.5px dashed {c['border']} !important;
    border-radius: 12px !important; transition: border-color 0.2s !important;
}}
[data-testid="stFileUploaderDropzone"]:hover {{ border-color: {c['accent']} !important; }}
[data-testid="stFileUploaderDropzone"] p {{ color: {c['text_muted']} !important; }}

[data-testid="stDataFrame"] {{
    border-radius: 10px !important; overflow: hidden !important;
    border: 1px solid {c['border']} !important;
}}

.stSuccess {{
    background: {c['accent_bg']} !important; color: {c['text_primary']} !important;
    border-left: 3px solid {c['accent']} !important; border-radius: 8px !important;
}}
.stWarning {{
    background: {c['warning_bg']} !important;
    border-left: 3px solid {c['warning']} !important; border-radius: 8px !important;
}}
.stSpinner > div > div {{ border-top-color: {c['spinner']} !important; }}

.g-addr-chip {{
    background: {c['chip_bg']}; border-radius: 8px; padding: 8px 12px;
    font-family: 'Abhaya Libre', serif; font-size: 0.88rem; color: {c['chip_text']};
    margin-top: 4px; display: flex; align-items: flex-start; gap: 6px;
    border: 1px solid {c['chip_border']};
}}
.g-km-badge {{
    display: inline-flex; align-items: center; gap: 6px;
    background: {c['success_bg']}; border: 1px solid {c['success_border']};
    border-radius: 8px; padding: 8px 14px;
    font-family: 'Geologica', sans-serif; font-weight: 700;
    font-size: 0.88rem; color: {c['success']}; margin-top: 4px;
}}
.g-result-price {{
    font-family: 'Geologica', sans-serif; font-weight: 900; font-size: 2.6rem;
    letter-spacing: -1px; line-height: 1.1; color: {c['text_primary']};
}}
.g-result-price.red {{ color: {c['error']}; }}
.g-result-label {{
    font-family: 'Geologica', sans-serif; font-weight: 600; font-size: 0.72rem;
    letter-spacing: 0.12em; text-transform: uppercase; color: {c['text_faint']}; margin-bottom: 4px;
}}
.g-margin-ok {{ font-family: 'Geologica', sans-serif; font-weight: 700; font-size: 1.1rem; color: {c['success']}; }}
.g-margin-warn {{ font-family: 'Geologica', sans-serif; font-weight: 700; font-size: 1.1rem; color: {c['error']}; }}
.g-breakdown-row {{
    display: flex; justify-content: space-between; padding: 6px 0;
    border-bottom: 1px solid {c['border_light']};
    font-family: 'Abhaya Libre', serif; font-size: 0.95rem; color: {c['text_secondary']};
}}
.g-breakdown-row:last-child {{ border-bottom: none; }}
.g-breakdown-label {{ color: {c['text_muted']}; }}
.g-breakdown-value {{ font-weight: 600; color: {c['text_primary']}; }}
.g-breakdown-value.negative {{ color: {c['error']}; }}
.g-badge-type {{
    font-family: 'Geologica', sans-serif; font-weight: 700; font-size: 0.68rem;
    letter-spacing: 0.06em; padding: 4px 12px; border-radius: 20px;
    display: inline-block; margin-bottom: 16px;
}}
.badge-fds {{ background: {c['error_bg']}; color: {c['error']}; }}
.badge-semana {{ background: {c['accent_bg']}; color: {c['accent']}; }}
.g-link-btn {{
    display: inline-flex; align-items: center; gap: 6px;
    background: {c['accent_bg']}; border: 1px solid {c['border']};
    border-radius: 8px; padding: 8px 14px;
    font-family: 'Geologica', sans-serif; font-weight: 600;
    font-size: 0.78rem; color: {c['accent']}; text-decoration: none; transition: all 0.15s;
}}
.g-link-btn:hover {{ background: {c['border']}; }}
.g-empty {{ text-align: center; padding: 48px 24px; color: {c['border']}; }}
.g-empty-icon {{ font-size: 2.8rem; margin-bottom: 12px; opacity: 0.7; }}
.g-empty-title {{ font-family: 'Geologica', sans-serif; font-weight: 600; font-size: 1rem; color: {c['text_muted']}; margin-bottom: 4px; }}
.g-empty-sub {{ font-size: 0.82rem; color: {c['border']}; }}
.g-card {{
    background: {c['surface']}; border: 1px solid {c['border']};
    border-radius: 14px; padding: 20px 24px; margin-top: 20px;
    box-shadow: 0 2px 16px {c['shadow']};
}}
.g-card-name {{
    font-family: 'Geologica', sans-serif; font-weight: 700; font-size: 0.9rem;
    color: {c['text_primary']}; white-space: nowrap; overflow: hidden;
    text-overflow: ellipsis; max-width: 320px;
}}
.g-badge {{
    font-family: 'Geologica', sans-serif; font-weight: 700; font-size: 0.68rem;
    background: {c['accent_bg']}; color: {c['accent']}; padding: 3px 10px; border-radius: 20px;
}}
.g-badge-warn {{ background: {c['warning_bg']}; color: {c['warning']}; }}
.g-footer {{
    text-align: center; margin-top: 48px; padding-top: 20px; border-top: 1px solid {c['border']};
    font-family: 'Geologica', sans-serif; font-size: 0.72rem; font-weight: 600;
    letter-spacing: 0.12em; text-transform: uppercase; color: {c['border']};
}}
</style>""", unsafe_allow_html=True)


def render_header(title: str, subtitle: str, page_key: str = ""):
    dark = st.session_state.get("dark_mode", False)
    icon = "☀️" if dark else "🌙"
    col_h, col_t = st.columns([12, 1])
    with col_h:
        st.markdown(f"""
        <div class="g-header">
            <div class="g-logo">Gooden<span class="g-logo-dot"></span></div>
            <div class="g-header-right">
                <div class="g-header-title">{title}</div>
                <div class="g-header-sub">Gooden Tool Kit · {subtitle}</div>
            </div>
        </div>""", unsafe_allow_html=True)
    with col_t:
        st.markdown('<div class="theme-toggle" style="margin-top:10px">', unsafe_allow_html=True)
        if st.button(icon, key=f"_theme_{page_key}", help="Alternar tema claro / escuro"):
            toggle_dark_mode()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
