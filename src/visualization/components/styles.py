"""Custom CSS and styled components for the dashboard."""

import streamlit as st

CUSTOM_CSS = """
<style>
/* ===================================================================
   UPI Analytics Platform — Professional Design System v2
   Color-rich, formal, intuitive
   =================================================================== */

/* --- Reset & Foundation --- */
[data-testid="stSidebar"] { display: none; }

.main .block-container {
    padding-top: 0.75rem;
    padding-bottom: 2rem;
    max-width: 100%;
}

/* --- Dashboard Header Banner --- */
.dashboard-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 40%, #1e40af 70%, #4338ca 100%);
    color: white;
    padding: 1.75rem 2rem;
    border-radius: 12px;
    margin-bottom: 0.75rem;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.18), 0 2px 6px rgba(30, 64, 175, 0.12);
    position: relative;
    overflow: hidden;
}
.dashboard-header::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 60%;
    height: 200%;
    background: radial-gradient(ellipse, rgba(99, 102, 241, 0.12) 0%, transparent 70%);
    pointer-events: none;
}
.dashboard-title {
    font-size: 1.85rem;
    font-weight: 800;
    color: white;
    margin: 0 0 0.25rem 0;
    letter-spacing: -0.5px;
    line-height: 1.2;
    position: relative;
}
.dashboard-subtitle {
    font-size: 0.9rem;
    color: rgba(255, 255, 255, 0.8);
    margin: 0;
    font-weight: 400;
    line-height: 1.4;
    position: relative;
}
.header-badges {
    display: flex;
    gap: 0.5rem;
    margin-top: 0.85rem;
    flex-wrap: wrap;
    position: relative;
}
.header-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    background: rgba(255, 255, 255, 0.12);
    backdrop-filter: blur(8px);
    color: rgba(255, 255, 255, 0.92);
    padding: 0.35rem 0.85rem;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 500;
    border: 1px solid rgba(255, 255, 255, 0.15);
    transition: background 0.2s ease;
}
.header-badge:hover {
    background: rgba(255, 255, 255, 0.2);
}

/* --- Tab Navigation --- */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
    border-bottom: 2px solid #e2e8f0;
    padding: 0;
    border-radius: 0;
    overflow-x: auto;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 0;
    padding: 0.65rem 1rem;
    font-weight: 500;
    font-size: 0.8rem;
    color: #64748b;
    border-bottom: 2.5px solid transparent;
    margin-bottom: -2px;
    white-space: nowrap;
    transition: all 0.2s ease;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #1e3a5f;
    background: rgba(37, 99, 235, 0.04);
}
.stTabs [aria-selected="true"] {
    background-color: transparent !important;
    color: #1e40af !important;
    border-bottom-color: #2563eb !important;
    font-weight: 700;
}

/* --- KPI Metric Cards --- */
[data-testid="stMetricValue"] {
    font-size: 1.5rem;
    font-weight: 700;
    color: #0f172a;
}
[data-testid="stMetricLabel"] {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: #64748b;
}
[data-testid="stMetricDelta"] {
    font-size: 0.78rem;
}
div[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-top: 3px solid #2563eb;
    border-radius: 8px;
    padding: 0.85rem 1rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.1);
}

/* KPI color variants via nth-child */
div[data-testid="column"]:nth-child(2) div[data-testid="stMetric"] {
    border-top-color: #7c3aed;
}
div[data-testid="column"]:nth-child(3) div[data-testid="stMetric"] {
    border-top-color: #059669;
}
div[data-testid="column"]:nth-child(4) div[data-testid="stMetric"] {
    border-top-color: #d97706;
}
div[data-testid="column"]:nth-child(5) div[data-testid="stMetric"] {
    border-top-color: #dc2626;
}
div[data-testid="column"]:nth-child(6) div[data-testid="stMetric"] {
    border-top-color: #0891b2;
}

/* --- Insight Callout Boxes --- */
.insight-box {
    background: linear-gradient(135deg, #eff6ff 0%, #f0f4ff 100%);
    color: #1e3a5f;
    padding: 1rem 1.25rem;
    border-radius: 8px;
    margin: 0.75rem 0;
    line-height: 1.65;
    font-size: 0.9rem;
    border: 1px solid #bfdbfe;
    border-left: 4px solid #2563eb;
}
.insight-box b, .insight-box strong { color: #1e40af; }

.insight-warning {
    background: linear-gradient(135deg, #fffbeb 0%, #fef9e7 100%);
    color: #78350f;
    padding: 1rem 1.25rem;
    border-radius: 8px;
    margin: 0.75rem 0;
    line-height: 1.65;
    font-size: 0.9rem;
    border: 1px solid #fde68a;
    border-left: 4px solid #d97706;
}
.insight-warning b, .insight-warning strong { color: #92400e; }

.insight-success {
    background: linear-gradient(135deg, #ecfdf5 0%, #eefbf3 100%);
    color: #064e3b;
    padding: 1rem 1.25rem;
    border-radius: 8px;
    margin: 0.75rem 0;
    line-height: 1.65;
    font-size: 0.9rem;
    border: 1px solid #a7f3d0;
    border-left: 4px solid #059669;
}
.insight-success b, .insight-success strong { color: #065f46; }

/* --- Divider --- */
.gradient-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent 0%, #cbd5e1 20%, #94a3b8 50%, #cbd5e1 80%, transparent 100%);
    border: none;
    border-radius: 0;
    margin: 1.25rem 0;
}

/* --- Scale Metric Cards --- */
.scale-card {
    text-align: center;
    padding: 1.15rem 0.75rem;
    background: #ffffff;
    border-radius: 10px;
    border: 1px solid #e2e8f0;
    border-top: 3px solid #2563eb;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.scale-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(37, 99, 235, 0.1);
}
.scale-card h2 {
    font-size: 1.5rem;
    font-weight: 700;
    color: #0f172a;
    margin: 0 0 0.25rem 0;
}
.scale-card p {
    font-size: 0.72rem;
    color: #64748b;
    margin: 0;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    font-weight: 600;
}
/* Scale card color variants */
.scale-card.violet { border-top-color: #7c3aed; }
.scale-card.violet:hover { box-shadow: 0 6px 16px rgba(124, 58, 237, 0.1); }
.scale-card.emerald { border-top-color: #059669; }
.scale-card.emerald:hover { box-shadow: 0 6px 16px rgba(5, 150, 105, 0.1); }
.scale-card.amber { border-top-color: #d97706; }
.scale-card.amber:hover { box-shadow: 0 6px 16px rgba(217, 119, 6, 0.1); }
.scale-card.rose { border-top-color: #e11d48; }
.scale-card.rose:hover { box-shadow: 0 6px 16px rgba(225, 29, 72, 0.1); }
.scale-card.cyan { border-top-color: #0891b2; }
.scale-card.cyan:hover { box-shadow: 0 6px 16px rgba(8, 145, 178, 0.1); }

/* --- Hero Header (used in tab pages) --- */
.hero-title {
    font-size: 1.75rem;
    font-weight: 800;
    color: #0f172a;
    margin-bottom: 0.2rem;
    letter-spacing: -0.5px;
    line-height: 1.2;
}
.hero-subtitle {
    font-size: 0.92rem;
    color: #64748b;
    margin-top: 0;
    line-height: 1.5;
}

/* --- Page Header (tab-level title) --- */
.page-header {
    margin-bottom: 0.75rem;
    padding-bottom: 0.6rem;
    border-bottom: 2px solid #e2e8f0;
    position: relative;
}
.page-header::after {
    content: '';
    position: absolute;
    bottom: -2px;
    left: 0;
    width: 60px;
    height: 2px;
    background: linear-gradient(90deg, #2563eb, #7c3aed);
    border-radius: 1px;
}
.page-title {
    font-size: 1.35rem;
    font-weight: 800;
    color: #0f172a;
    margin: 0 0 0.15rem 0;
    letter-spacing: -0.3px;
}
.page-subtitle {
    font-size: 0.88rem;
    color: #64748b;
    margin: 0;
    font-weight: 400;
}

/* --- Section Headers --- */
.section-header {
    font-size: 1.05rem;
    font-weight: 700;
    color: #0f172a;
    border-bottom: none;
    border-left: 3px solid;
    border-image: linear-gradient(180deg, #2563eb, #7c3aed) 1;
    padding: 0.3rem 0 0.3rem 0.75rem;
    margin: 1.25rem 0 0.6rem 0;
    letter-spacing: -0.2px;
}

/* --- About / Info Cards --- */
.about-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 1.25rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    margin-bottom: 0.75rem;
    transition: all 0.2s ease;
    height: 100%;
    border-top: 3px solid #2563eb;
}
.about-card:hover {
    box-shadow: 0 6px 20px rgba(37, 99, 235, 0.08);
    transform: translateY(-2px);
}
.about-card.violet-card { border-top-color: #7c3aed; }
.about-card.violet-card:hover { box-shadow: 0 6px 20px rgba(124, 58, 237, 0.08); }
.about-card.emerald-card { border-top-color: #059669; }
.about-card.emerald-card:hover { box-shadow: 0 6px 20px rgba(5, 150, 105, 0.08); }
.about-card.amber-card { border-top-color: #d97706; }
.about-card.amber-card:hover { box-shadow: 0 6px 20px rgba(217, 119, 6, 0.08); }
.about-card h4 {
    color: #0f172a;
    margin: 0 0 0.5rem 0;
    font-size: 0.95rem;
    font-weight: 700;
}
.about-card p {
    margin: 0 0 0.4rem 0;
    font-size: 0.88rem;
    color: #475569;
    line-height: 1.55;
}
.about-card .about-card-link,
.about-card p:last-child a {
    font-size: 0.8rem;
    color: #2563eb;
    text-decoration: none;
    font-weight: 500;
}
.about-card .about-card-link a:hover,
.about-card p:last-child a:hover {
    text-decoration: underline;
}

/* --- Chart & Visualization Containers --- */
[data-testid="stPlotlyChart"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 0.75rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.03);
    margin-bottom: 0.5rem;
    transition: box-shadow 0.2s ease;
}
[data-testid="stPlotlyChart"]:hover {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.07);
}

[data-testid="stVegaLiteChart"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 0.75rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.03);
    margin-bottom: 0.5rem;
}

/* --- Data Tables --- */
.stDataFrame {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 0.5rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.03);
    overflow: hidden;
}

/* --- Expander --- */
[data-testid="stExpander"] {
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    overflow: hidden;
    transition: box-shadow 0.2s ease;
}
[data-testid="stExpander"]:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

/* --- Footer --- */
.footer-text {
    text-align: center;
    color: #94a3b8;
    font-size: 0.8rem;
    padding: 1.25rem 0 0.5rem 0;
    border-top: none;
    margin-top: 1.5rem;
    position: relative;
}
.footer-text::before {
    content: '';
    display: block;
    width: 80px;
    height: 2px;
    background: linear-gradient(90deg, #2563eb, #7c3aed);
    margin: 0 auto 1rem auto;
    border-radius: 1px;
}
.footer-text a {
    color: #2563eb;
    text-decoration: none;
    font-weight: 500;
}
.footer-text a:hover {
    text-decoration: underline;
    color: #7c3aed;
}

/* --- Form Labels --- */
[data-testid="stSelectbox"] label,
[data-testid="stMultiSelect"] label,
[data-testid="stSlider"] label,
[data-testid="stRadio"] label {
    font-size: 0.82rem;
    font-weight: 600;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}

/* --- Pipeline Visualization --- */
.pipeline-flow {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0;
    flex-wrap: wrap;
    margin: 1rem 0;
}
.pipeline-stage {
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 0.7rem 1.3rem;
    font-size: 0.85rem;
    font-weight: 600;
    color: #1e293b;
    text-align: center;
    transition: all 0.2s ease;
}
.pipeline-stage:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}
.pipeline-arrow {
    color: #94a3b8;
    font-size: 1.3rem;
    padding: 0 0.5rem;
}
.pipeline-stage.active {
    background: linear-gradient(135deg, #2563eb 0%, #4338ca 100%);
    color: white;
    border-color: #2563eb;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
}

/* --- Spinner --- */
[data-testid="stSpinner"] {
    color: #2563eb !important;
}

/* --- Scrollbar --- */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #f1f5f9; border-radius: 3px; }
::-webkit-scrollbar-thumb { background: #94a3b8; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #64748b; }
</style>
"""


def inject_custom_css():
    """Inject custom CSS into the Streamlit app."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_insight(text: str, variant: str = "default"):
    """Render a styled insight callout box."""
    css_class = {
        "default": "insight-box",
        "warning": "insight-warning",
        "success": "insight-success",
    }.get(variant, "insight-box")
    st.markdown(f'<div class="{css_class}">{text}</div>', unsafe_allow_html=True)


def render_divider():
    """Render a gradient divider line."""
    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)


def render_scale_card(value: str, label: str, color: str = ""):
    """Render a scale metric card with optional color variant."""
    cls = f"scale-card {color}" if color else "scale-card"
    st.markdown(
        f'<div class="{cls}"><h2>{value}</h2><p>{label}</p></div>',
        unsafe_allow_html=True,
    )


def render_section_header(text: str):
    """Render a styled section header with left accent."""
    st.markdown(f'<div class="section-header">{text}</div>', unsafe_allow_html=True)


def render_page_header(title: str, subtitle: str = ""):
    """Render a professional page-level header."""
    html = f'<div class="page-header"><h2 class="page-title">{title}</h2>'
    if subtitle:
        html += f'<p class="page-subtitle">{subtitle}</p>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)
