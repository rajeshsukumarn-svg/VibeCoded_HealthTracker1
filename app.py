import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date
from database import (
    init_db, seed_demo_data, get_patients, add_patient, delete_patient,
    add_vitals, get_vitals, get_latest_vitals,
    add_medication, get_medications, toggle_medication,
    log_medication_taken, get_med_logs_today,
)

st.set_page_config(
    page_title="HealthTrack",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* ── Global ── */
[data-testid="stAppViewContainer"] { background: #0f1117; color: #e8eaf6; }
[data-testid="stSidebar"] { background: #161b27 !important; border-right: 1px solid #252d3d; }
[data-testid="stHeader"] { background: #0f1117 !important; }
[data-testid="stToolbar"] { background: #0f1117 !important; }
header[data-testid="stHeader"] { background: #0f1117 !important; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
.stMainBlockContainer { background: #0f1117; }
[data-testid="stMain"] { background: #0f1117; }
section[data-testid="stSidebar"] + div { background: #0f1117; }

/* Sidebar radio buttons */
[data-testid="stSidebar"] .stRadio label {
    color: #c5cae9 !important;
    font-size: 15px !important;
    font-weight: 500 !important;
}
[data-testid="stSidebar"] .stRadio label:hover {
    color: #ffffff !important;
}
[data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p {
    color: #c5cae9 !important;
    font-size: 15px !important;
}
[data-testid="stSidebar"] div[role="radiogroup"] label div p {
    color: #c5cae9 !important;
    font-size: 15px !important;
}
/* Radio circle color */
[data-testid="stSidebar"] input[type="radio"] + div {
    border-color: #7986cb !important;
    background: transparent !important;
}
[data-testid="stSidebar"] input[type="radio"]:checked + div {
    background: #7986cb !important;
    border-color: #7986cb !important;
}

/* ── Metric cards ── */
.metric-card {
    background: linear-gradient(135deg, #1a2035 0%, #1e2a45 100%);
    border: 1px solid #2d3a5a;
    border-radius: 16px;
    padding: 20px 24px;
    margin-bottom: 12px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}
.metric-label { font-size: 12px; color: #7986cb; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
.metric-value { font-size: 32px; font-weight: 700; color: #e8eaf6; line-height: 1; }
.metric-unit  { font-size: 14px; color: #9fa8da; margin-left: 4px; }
.metric-delta { font-size: 12px; margin-top: 6px; }
.delta-good { color: #69f0ae; }
.delta-warn { color: #ffd740; }
.delta-bad  { color: #ff5252; }

/* ── Status badge ── */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: .5px;
}
.badge-normal  { background: #1b5e20; color: #69f0ae; }
.badge-warn    { background: #f57f17; color: #fff9c4; }
.badge-high    { background: #b71c1c; color: #ffcdd2; }

/* ── Section header ── */
.section-header {
    font-size: 18px;
    font-weight: 700;
    color: #7986cb;
    border-bottom: 2px solid #2d3a5a;
    padding-bottom: 8px;
    margin-bottom: 20px;
}

/* ── Med card ── */
.med-card {
    background: #1a2035;
    border: 1px solid #2d3a5a;
    border-left: 4px solid #7986cb;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
}
.med-name { font-size: 16px; font-weight: 600; color: #e8eaf6; }
.med-detail { font-size: 13px; color: #9fa8da; margin-top: 3px; }

/* ── Streamlit overrides ── */
.stSelectbox label, .stNumberInput label, .stTextInput label,
.stDateInput label, .stTextArea label { color: #9fa8da !important; font-size: 13px !important; }
div[data-testid="stForm"] { background: #1a2035; border: 1px solid #2d3a5a; border-radius: 12px; padding: 20px; }
.stButton > button {
    background: linear-gradient(135deg, #3949ab, #5c6bc0) !important;
    color: white !important; border: none !important;
    border-radius: 8px !important; font-weight: 600 !important;
    padding: 8px 20px !important;
}
.stButton > button:hover { opacity: .85 !important; }
div[data-testid="stMetric"] { background: #1a2035; border: 1px solid #2d3a5a; border-radius: 12px; padding: 16px; }
div[data-testid="stMetric"] label,
div[data-testid="stMetricLabel"] p { color: #9fa8da !important; font-size: 12px !important; }
div[data-testid="stMetricValue"] > div { color: #e8eaf6 !important; font-size: 28px !important; font-weight: 700 !important; }
div[data-testid="stMetricDelta"] { color: #9fa8da !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { background: #1a2035; border-radius: 8px; gap: 4px; }
.stTabs [data-baseweb="tab"] { color: #9fa8da !important; background: transparent !important; border-radius: 6px !important; }
.stTabs [aria-selected="true"] { color: #e8eaf6 !important; background: #2d3a5a !important; }

/* ── Dataframe / table text ── */
[data-testid="stDataFrame"] { color: #e8eaf6; }
.stDataFrame td, .stDataFrame th { color: #e8eaf6 !important; }

/* ── General text ── */
p, li, span, div { color: inherit; }
.stMarkdown p { color: #c5cae9; }
[data-testid="stText"] { color: #c5cae9 !important; }
[data-testid="stCaptionContainer"] p { color: #7986cb !important; font-size: 12px !important; }
</style>
""", unsafe_allow_html=True)


# ── Init ──────────────────────────────────────────────────────────────────────
init_db()
seed_demo_data()


# ── Helpers ───────────────────────────────────────────────────────────────────
def bp_status(sys, dia):
    if sys is None:
        return "", ""
    if sys < 120 and dia < 80:
        return "Normal", "badge-normal"
    if sys < 130 and dia < 80:
        return "Elevated", "badge-warn"
    if sys < 140 or dia < 90:
        return "High Stage 1", "badge-warn"
    return "High Stage 2", "badge-high"


def glucose_status(g):
    if g is None:
        return "", ""
    if g < 100:
        return "Normal", "badge-normal"
    if g < 126:
        return "Pre-diabetic", "badge-warn"
    return "High", "badge-high"


def spo2_status(s):
    if s is None:
        return "", ""
    if s >= 95:
        return "Normal", "badge-normal"
    if s >= 90:
        return "Low", "badge-warn"
    return "Critical", "badge-high"


def make_trend_chart(df, y_col, title, color, ref_low=None, ref_high=None):
    fig = go.Figure()
    if ref_low is not None and ref_high is not None:
        fig.add_hrect(y0=ref_low, y1=ref_high, fillcolor="rgba(105,240,174,0.06)",
                      line_width=0, annotation_text="Normal range",
                      annotation_position="top left",
                      annotation_font_color="#69f0ae", annotation_font_size=10)
    fig.add_trace(go.Scatter(
        x=df["recorded_at"], y=df[y_col],
        mode="lines+markers",
        line=dict(color=color, width=2.5),
        marker=dict(size=6, color=color),
        fill="tozeroy",
        fillcolor="rgba(100,100,200,0.08)",
        name=title,
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=15, color="#9fa8da")),
        paper_bgcolor="#1a2035", plot_bgcolor="#1a2035",
        font=dict(color="#9fa8da", size=12),
        xaxis=dict(gridcolor="#252d3d", showgrid=True, title=""),
        yaxis=dict(gridcolor="#252d3d", showgrid=True),
        margin=dict(l=10, r=10, t=40, b=10),
        height=260,
        showlegend=False,
    )
    return fig


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏥 HealthTrack")
    st.markdown("---")

    patients = get_patients()
    search_q = st.text_input("🔍 Search patient", placeholder="Type name…", key="patient_search",
                             label_visibility="collapsed")
    filtered_pts = [p for p in patients if search_q.lower() in p["name"].lower()] if search_q else patients
    if not filtered_pts:
        st.caption("No patients match")
        filtered_pts = patients  # fall back so app doesn't crash

    sel_name = st.selectbox(
        "👤 Patient", [p["name"] for p in filtered_pts],
        label_visibility="collapsed", key="patient_select"
    )
    selected = next(p for p in patients if p["name"] == sel_name)
    pid = selected["id"]

    st.markdown(f"""
    <div style="background:#1e2a45;border-radius:10px;padding:12px;margin-top:8px;font-size:13px;color:#9fa8da;">
        <b style="color:#e8eaf6">{selected['name']}</b><br>
        Age: {selected['age']} &nbsp;|&nbsp; {selected['gender']}<br>
        Blood Type: <span style="color:#ef9a9a">{selected['blood_type']}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    PAGES = ["Dashboard", "Log Vitals", "Medications", "Trends", "Patients"]
    if "nav_index" not in st.session_state:
        st.session_state.nav_index = 0

    page = st.radio("Navigation", PAGES,
                    index=st.session_state.nav_index,
                    label_visibility="collapsed", key="nav_radio")
    st.session_state.nav_index = PAGES.index(page)

    st.markdown("---")
    if st.button("➕ Add New Patient", use_container_width=True):
        st.session_state.nav_index = PAGES.index("Patients")
        st.session_state.patients_tab = "Add Patient"
        st.rerun()
    st.markdown("<div style='color:#4a5568;font-size:11px;text-align:center;margin-top:8px'>HealthTrack v1.0 · Prototype</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "Dashboard":
    st.markdown(f"<h2 style='color:#e8eaf6;margin-bottom:4px'>Good {('Morning' if datetime.now().hour < 12 else 'Afternoon' if datetime.now().hour < 17 else 'Evening')}, {selected['name'].split()[0]} 👋</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#7986cb'>{datetime.now().strftime('%A, %B %d %Y')}</p>", unsafe_allow_html=True)
    st.markdown("---")

    latest = get_latest_vitals(pid)

    # ── Vital cards row ──
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        bp_s = f"{latest['systolic']}/{latest['diastolic']}" if latest and latest["systolic"] else "—"
        bp_lbl, bp_cls = bp_status(latest["systolic"] if latest else None, latest["diastolic"] if latest else None)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Blood Pressure</div>
            <div class="metric-value">{bp_s} <span class="metric-unit">mmHg</span></div>
            {"<span class='badge " + bp_cls + "'>" + bp_lbl + "</span>" if bp_lbl else ""}
        </div>""", unsafe_allow_html=True)

    with col2:
        hr = f"{latest['heart_rate']}" if latest and latest["heart_rate"] else "—"
        hr_ok = latest and latest["heart_rate"] and 60 <= latest["heart_rate"] <= 100
        hr_cls = "badge-normal" if hr_ok else "badge-warn"
        hr_lbl = "Normal" if hr_ok else ("High" if (latest and latest["heart_rate"] and latest["heart_rate"] > 100) else ("Low" if (latest and latest["heart_rate"]) else ""))
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Heart Rate</div>
            <div class="metric-value">{hr} <span class="metric-unit">bpm</span></div>
            {"<span class='badge " + hr_cls + "'>" + hr_lbl + "</span>" if hr_lbl else ""}
        </div>""", unsafe_allow_html=True)

    with col3:
        gluc = f"{latest['glucose']:.0f}" if latest and latest["glucose"] else "—"
        g_lbl, g_cls = glucose_status(latest["glucose"] if latest else None)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Blood Glucose</div>
            <div class="metric-value">{gluc} <span class="metric-unit">mg/dL</span></div>
            {"<span class='badge " + g_cls + "'>" + g_lbl + "</span>" if g_lbl else ""}
        </div>""", unsafe_allow_html=True)

    with col4:
        spo2 = f"{latest['spo2']}" if latest and latest["spo2"] else "—"
        s_lbl, s_cls = spo2_status(latest["spo2"] if latest else None)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">SpO₂</div>
            <div class="metric-value">{spo2} <span class="metric-unit">%</span></div>
            {"<span class='badge " + s_cls + "'>" + s_lbl + "</span>" if s_lbl else ""}
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Mini trends + meds ──
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown("<div class='section-header'>Recent Vitals (7 days)</div>", unsafe_allow_html=True)
        rows = get_vitals(pid, limit=7)
        if rows:
            df = pd.DataFrame([dict(r) for r in rows])
            df["recorded_at"] = pd.to_datetime(df["recorded_at"])
            df = df.sort_values("recorded_at")

            fig = go.Figure()
            if df["systolic"].notna().any():
                fig.add_trace(go.Scatter(x=df["recorded_at"], y=df["systolic"], name="Systolic",
                                         line=dict(color="#ef5350", width=2), mode="lines+markers"))
                fig.add_trace(go.Scatter(x=df["recorded_at"], y=df["diastolic"], name="Diastolic",
                                         line=dict(color="#42a5f5", width=2), mode="lines+markers"))
            fig.update_layout(
                paper_bgcolor="#1a2035", plot_bgcolor="#1a2035",
                font=dict(color="#9fa8da"), height=220,
                xaxis=dict(gridcolor="#252d3d"), yaxis=dict(gridcolor="#252d3d"),
                margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(bgcolor="#1a2035", bordercolor="#2d3a5a"),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No vitals recorded yet. Log your first reading!")

    with col_right:
        st.markdown("<div class='section-header'>Today's Medications</div>", unsafe_allow_html=True)
        meds = get_medications(pid)
        today_logs = get_med_logs_today(pid)
        taken_ids = {log["medication_id"] for log in today_logs if log["taken"]}

        if not meds:
            st.info("No active medications.")
        for m in meds:
            taken = m["id"] in taken_ids
            icon = "✅" if taken else "⏰"
            st.markdown(f"""
            <div class="med-card" style="border-left-color:{'#69f0ae' if taken else '#ffd740'}">
                <div class="med-name">{icon} {m['name']}</div>
                <div class="med-detail">{m['dosage']} · {m['frequency']}</div>
            </div>""", unsafe_allow_html=True)
            if not taken:
                if st.button(f"Mark taken", key=f"take_{m['id']}"):
                    log_medication_taken(m["id"], pid)
                    st.rerun()

    # ── Recent logs table ──
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>Recent Readings</div>", unsafe_allow_html=True)
    rows = get_vitals(pid, limit=10)
    if rows:
        df = pd.DataFrame([dict(r) for r in rows])
        df = df[["recorded_at", "systolic", "diastolic", "heart_rate", "glucose", "weight", "temperature", "spo2"]]
        df.columns = ["Date/Time", "Systolic", "Diastolic", "Heart Rate", "Glucose", "Weight (kg)", "Temp (°C)", "SpO₂ (%)"]
        df["Date/Time"] = pd.to_datetime(df["Date/Time"]).dt.strftime("%b %d, %H:%M")
        st.dataframe(df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: LOG VITALS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Log Vitals":
    st.markdown("<h2 style='color:#e8eaf6'>📊 Log Vitals</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#7986cb'>Recording for: <b>{selected['name']}</b></p>", unsafe_allow_html=True)
    st.markdown("---")

    with st.form("vitals_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Blood Pressure**")
            bp_col1, bp_col2 = st.columns(2)
            with bp_col1:
                systolic = st.number_input("Systolic (mmHg)", 60, 250, value=None, placeholder="e.g. 120")
            with bp_col2:
                diastolic = st.number_input("Diastolic (mmHg)", 40, 150, value=None, placeholder="e.g. 80")

            heart_rate = st.number_input("Heart Rate (bpm)", 30, 220, value=None, placeholder="e.g. 72")
            glucose = st.number_input("Blood Glucose (mg/dL)", 30.0, 600.0, value=None, placeholder="e.g. 110")

        with col2:
            weight = st.number_input("Weight (kg)", 20.0, 300.0, value=None, placeholder="e.g. 72.5")
            temperature = st.number_input("Temperature (°C)", 34.0, 42.0, value=None, placeholder="e.g. 36.6")
            spo2 = st.number_input("SpO₂ (%)", 70, 100, value=None, placeholder="e.g. 98")
            recorded_at = st.date_input("Date", value=date.today())

        notes = st.text_area("Notes (optional)", placeholder="Any symptoms, context, or observations...")

        submitted = st.form_submit_button("💾 Save Reading", use_container_width=True)
        if submitted:
            ts = datetime.combine(recorded_at, datetime.now().time()).strftime("%Y-%m-%d %H:%M:%S")
            add_vitals(pid, systolic, diastolic, heart_rate, glucose, weight, temperature, spo2, notes, ts)
            st.success("✅ Vitals saved successfully!")
            st.balloons()

    # Reference ranges
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>Reference Ranges</div>", unsafe_allow_html=True)
    ref_data = {
        "Metric": ["Blood Pressure", "Heart Rate", "Blood Glucose (Fasting)", "SpO₂", "Temperature"],
        "Normal Range": ["<120/80 mmHg", "60–100 bpm", "70–99 mg/dL", "≥95%", "36.1–37.2 °C"],
        "Borderline": ["120–139/80–89", "50–59 or 101–110", "100–125 mg/dL", "90–94%", "37.3–38.0 °C"],
        "Concerning": [">140/90 mmHg", "<50 or >110 bpm", "≥126 mg/dL", "<90%", ">38.0 °C"],
    }
    st.dataframe(pd.DataFrame(ref_data), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: MEDICATIONS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Medications":
    st.markdown("<h2 style='color:#e8eaf6'>💊 Medications</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#7986cb'>Managing for: <b>{selected['name']}</b></p>", unsafe_allow_html=True)
    st.markdown("---")

    tab1, tab2 = st.tabs(["Active Medications", "Add Medication"])

    with tab1:
        meds = get_medications(pid, active_only=False)
        if not meds:
            st.info("No medications added yet.")
        else:
            today_logs = get_med_logs_today(pid)
            taken_ids = {log["medication_id"] for log in today_logs if log["taken"]}

            for m in meds:
                is_active = bool(m["active"])
                taken_today = m["id"] in taken_ids
                col1, col2, col3 = st.columns([4, 1, 1])
                with col1:
                    st.markdown(f"""
                    <div class="med-card" style="opacity:{'1' if is_active else '0.5'}">
                        <div class="med-name">{'✅' if taken_today else '💊'} {m['name']}
                            {'<span style="color:#69f0ae;font-size:12px;margin-left:8px">● Active</span>' if is_active else '<span style="color:#546e7a;font-size:12px;margin-left:8px">● Inactive</span>'}
                        </div>
                        <div class="med-detail">
                            {m['dosage']} · {m['frequency']}<br>
                            {'From: ' + m['start_date'] + (' → ' + m['end_date'] if m['end_date'] else '') if m['start_date'] else ''}
                            {'<br>' + m['notes'] if m['notes'] else ''}
                        </div>
                    </div>""", unsafe_allow_html=True)
                with col2:
                    if is_active and not taken_today:
                        if st.button("✓ Taken", key=f"taken_{m['id']}"):
                            log_medication_taken(m["id"], pid)
                            st.rerun()
                with col3:
                    label = "Deactivate" if is_active else "Activate"
                    if st.button(label, key=f"toggle_{m['id']}"):
                        toggle_medication(m["id"], 0 if is_active else 1)
                        st.rerun()

    with tab2:
        with st.form("med_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                med_name = st.text_input("Medication Name *", placeholder="e.g. Metformin")
                dosage = st.text_input("Dosage", placeholder="e.g. 500mg")
                frequency = st.selectbox("Frequency", ["Once daily", "Twice daily", "Three times daily",
                                                         "Every 4 hours", "Every 6 hours", "As needed", "Weekly"])
            with col2:
                start_date = st.date_input("Start Date", value=date.today())
                end_date = st.date_input("End Date (optional)", value=None)
                med_notes = st.text_input("Instructions", placeholder="e.g. Take with food")

            if st.form_submit_button("➕ Add Medication", use_container_width=True):
                if med_name:
                    add_medication(pid, med_name, dosage, frequency,
                                   str(start_date), str(end_date) if end_date else None, med_notes)
                    st.success(f"✅ {med_name} added!")
                    st.rerun()
                else:
                    st.error("Medication name is required.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: TRENDS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Trends":
    st.markdown("<h2 style='color:#e8eaf6'>📈 Health Trends</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#7986cb'>Analysis for: <b>{selected['name']}</b></p>", unsafe_allow_html=True)
    st.markdown("---")

    rows = get_vitals(pid, limit=90)
    if not rows:
        st.info("No vitals data yet. Start logging to see trends.")
    else:
        df = pd.DataFrame([dict(r) for r in rows])
        df["recorded_at"] = pd.to_datetime(df["recorded_at"])
        df = df.sort_values("recorded_at")

        period = st.select_slider("Time Range", options=["7 days", "14 days", "30 days", "90 days"], value="30 days")
        days = int(period.split()[0])
        cutoff = df["recorded_at"].max() - pd.Timedelta(days=days)
        df = df[df["recorded_at"] >= cutoff]

        col1, col2 = st.columns(2)

        with col1:
            if df["systolic"].notna().any():
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df["recorded_at"], y=df["systolic"], name="Systolic",
                                         line=dict(color="#ef5350", width=2.5), mode="lines+markers", marker=dict(size=5)))
                fig.add_trace(go.Scatter(x=df["recorded_at"], y=df["diastolic"], name="Diastolic",
                                         line=dict(color="#42a5f5", width=2.5), mode="lines+markers", marker=dict(size=5)))
                fig.add_hrect(y0=0, y1=120, fillcolor="rgba(105,240,174,0.05)", line_width=0)
                fig.update_layout(title="Blood Pressure", paper_bgcolor="#1a2035", plot_bgcolor="#1a2035",
                                   font=dict(color="#9fa8da"), height=270, margin=dict(l=10,r=10,t=40,b=10),
                                   xaxis=dict(gridcolor="#252d3d"), yaxis=dict(gridcolor="#252d3d"),
                                   legend=dict(bgcolor="#1a2035"))
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            if df["heart_rate"].notna().any():
                st.plotly_chart(
                    make_trend_chart(df, "heart_rate", "Heart Rate (bpm)", "#ab47bc", 60, 100),
                    use_container_width=True
                )

        col3, col4 = st.columns(2)

        with col3:
            if df["glucose"].notna().any():
                st.plotly_chart(
                    make_trend_chart(df, "glucose", "Blood Glucose (mg/dL)", "#ffa726", 70, 99),
                    use_container_width=True
                )

        with col4:
            if df["weight"].notna().any():
                st.plotly_chart(
                    make_trend_chart(df, "weight", "Weight (kg)", "#26c6da"),
                    use_container_width=True
                )

        if df["spo2"].notna().any():
            col5, col6 = st.columns(2)
            with col5:
                st.plotly_chart(
                    make_trend_chart(df, "spo2", "SpO₂ (%)", "#66bb6a", 95, 100),
                    use_container_width=True
                )
            with col6:
                if df["temperature"].notna().any():
                    st.plotly_chart(
                        make_trend_chart(df, "temperature", "Temperature (°C)", "#ec407a", 36.1, 37.2),
                        use_container_width=True
                    )

        # Stats summary
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='section-header'>Statistics Summary</div>", unsafe_allow_html=True)
        cols_to_show = ["systolic", "diastolic", "heart_rate", "glucose", "weight", "temperature", "spo2"]
        cols_present = [c for c in cols_to_show if c in df.columns and df[c].notna().any()]
        if cols_present:
            stats = df[cols_present].describe().round(1).T.reset_index()
            stats.columns = ["Metric", "Count", "Mean", "Std Dev", "Min", "25%", "Median", "75%", "Max"]
            stats["Metric"] = stats["Metric"].str.replace("_", " ").str.title()
            st.dataframe(stats, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: PATIENTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Patients":
    st.markdown("<h2 style='color:#e8eaf6'>👥 Patient Profiles</h2>", unsafe_allow_html=True)
    st.markdown("---")

    PATIENT_TABS = ["All Patients", "Add Patient"]
    if "patients_tab" not in st.session_state:
        st.session_state.patients_tab = "All Patients"

    pt_col1, pt_col2 = st.columns([1, 3])
    with pt_col1:
        patients_view = st.radio(
            "View",
            PATIENT_TABS,
            index=PATIENT_TABS.index(st.session_state.patients_tab),
            label_visibility="collapsed",
            horizontal=True,
            key="patients_tab_radio",
        )
        st.session_state.patients_tab = patients_view

    if patients_view == "All Patients":
        patients = get_patients()
        search_pts = st.text_input("🔍 Search", placeholder="Filter by name…", key="patients_page_search",
                                   label_visibility="collapsed")
        if search_pts:
            patients = [p for p in patients if search_pts.lower() in p["name"].lower()]
        if not patients:
            st.info("No patients match that search.")
        for p in patients:
            latest = get_latest_vitals(p["id"])
            col1, col2, col3 = st.columns([4, 2, 1])
            with col1:
                bp_str = f"{latest['systolic']}/{latest['diastolic']} mmHg" if latest and latest["systolic"] else "No readings"
                bp_lbl, bp_cls = bp_status(latest["systolic"] if latest else None, latest["diastolic"] if latest else None)
                st.markdown(f"""
                <div class="med-card">
                    <div class="med-name">👤 {p['name']}</div>
                    <div class="med-detail">
                        Age: {p['age']} · {p['gender']} · Blood Type: {p['blood_type']}<br>
                        Latest BP: {bp_str}
                        {"&nbsp;<span class='badge " + bp_cls + "'>" + bp_lbl + "</span>" if bp_lbl else ""}
                    </div>
                </div>""", unsafe_allow_html=True)
            with col2:
                meds = get_medications(p["id"])
                st.metric("Medications", len(meds))
            with col3:
                vitals_count = len(get_vitals(p["id"]))
                st.metric("Readings", vitals_count)

    else:  # Add Patient
        with st.form("add_patient_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                p_name = st.text_input("Full Name *", placeholder="e.g. John Doe")
                p_age = st.number_input("Age", 1, 120, value=30)
            with col2:
                p_gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                p_blood = st.selectbox("Blood Type", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-", "Unknown"])

            if st.form_submit_button("➕ Add Patient", use_container_width=True):
                if p_name:
                    add_patient(p_name, p_age, p_gender, p_blood)
                    st.success(f"✅ {p_name} added!")
                    st.session_state.patients_tab = "All Patients"
                    st.rerun()
                else:
                    st.error("Name is required.")
