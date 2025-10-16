import streamlit as st
import pandas as pd
import pydeck as pdk
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

st.set_page_config(layout="wide")
st.title("⚡ GridMind AI — Site Analyzer (Step 3)")

# ---- Load data ----
df = pd.read_csv("data/gridmind_sample_tr.csv")
uploaded = st.sidebar.file_uploader("Upload CSV (same columns)", type=["csv"])
if uploaded:
    df = pd.read_csv(uploaded)

# ---- Weight sliders ----
st.sidebar.header("Scoring Weights")
w_solar = st.sidebar.slider("☀️ Solar Weight", 0.0, 1.0, 0.4)
w_wind = st.sidebar.slider("🌬️ Wind Weight", 0.0, 1.0, 0.3)
w_grid = st.sidebar.slider("🔌 Grid Distance Penalty", 0.0, 1.0, 0.15)
w_slope = st.sidebar.slider("🏔️ Slope Penalty", 0.0, 1.0, 0.15)

# Normalize helper
def norm(s): return (s - s.min()) / (s.max() - s.min() + 1e-9)

# Recalculate score dynamically
df["score"] = (
    w_solar*norm(df["ghi_kwh_m2_yr"]) +
    w_wind*norm(df["wind_speed_100m_ms"]) -
    w_grid*norm(df["grid_distance_km"]) -
    w_slope*norm(df["slope_deg"])
).round(3)

# ---- LCOE quick estimate ----
st.sidebar.header("💰 Cost Inputs")
capex = st.sidebar.number_input("CAPEX ($/kW)", 500, 2000, 900)
opex = st.sidebar.number_input("OPEX ($/kW/yr)", 5, 60, 20)
yield_avg = st.sidebar.number_input("Average Yield (kWh/kW/yr)", 1000, 2500, 1600)
lifetime = st.sidebar.number_input("Lifetime (years)", 10, 30, 20)

lcoe = round((capex + opex*lifetime)/(yield_avg*lifetime), 3)
st.sidebar.metric("Estimated LCOE ($/kWh)", lcoe)

# ---- Map + Table ----
col1, col2 = st.columns([2,1])
with col1:
    st.subheader("Map of Candidate Sites")
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position=["lon","lat"],
        get_radius=6000,
        pickable=True,
        get_fill_color="[255,(score*255).toFixed(0),120,180]",
    )
    view = pdk.ViewState(latitude=39, longitude=35, zoom=5)
    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view,
                             tooltip={"text":"Region: {region}\nScore: {score}"}))

with col2:
    st.subheader("Top 20 Sites")
    top = df.sort_values("score", ascending=False).head(20)
    st.dataframe(top[["region","lat","lon","score","ghi_kwh_m2_yr","wind_speed_100m_ms"]])

# ---- PDF generator ----
def make_pdf(data):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.drawString(40,750,"GridMind AI — Feasibility Summary")
    y = 720
    for i, row in data.iterrows():
        c.drawString(40, y, f"{row.region} | Score {row.score} | GHI {row.ghi_kwh_m2_yr} | Wind {row.wind_speed_100m_ms}")
        y -= 14
        if y < 60:
            c.showPage()
            y = 750
    c.save()
    buf.seek(0)
    return buf

if st.button("📄 Download Top 20 as PDF"):
    pdf_buf = make_pdf(top)
    st.download_button("Download PDF", pdf_buf, "gridmind_summary.pdf")

st.caption("Tip: Adjust weights & costs → instant new scoring + LCOE update.")
reportlab
