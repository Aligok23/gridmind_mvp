import streamlit as st, pandas as pd, pydeck as pdk

st.set_page_config(layout="wide")
st.title("⚡ GridMind AI — Map (Step 2)")

# 1) Load the sample CSV you just uploaded
df = pd.read_csv("data/gridmind_sample_tr.csv")

# 2) (Optional) Let you upload your own CSV with the same columns
uploaded = st.sidebar.file_uploader("Upload CSV (same columns as sample)", type=["csv"])
if uploaded:
    df = pd.read_csv(uploaded)

# 3) Simple filters to try
ghi_min = st.sidebar.slider("Min GHI (kWh/m²/yr)", 1200, 2300, 1600, 10)
wind_min = st.sidebar.slider("Min Wind @100m (m/s)", 3, 11, 6)
df = df[(df.ghi_kwh_m2_yr >= ghi_min) & (df.wind_speed_100m_ms >= wind_min)]

# 4) Map
layer = pdk.Layer(
    "ScatterplotLayer",
    data=df,
    get_position=["lon","lat"],
    get_radius=6000,
    pickable=True,
    get_fill_color="[255,(score*255).toFixed(0),120,160]",
)
view = pdk.ViewState(latitude=39, longitude=35, zoom=5)
st.pydeck_chart(
    pdk.Deck(layers=[layer], initial_view_state=view,
             tooltip={"text":"Score: {score}\nGHI: {ghi_kwh_m2_yr}\nWind: {wind_speed_100m_ms}"})
)

# 5) Top 20 table
st.subheader("Top 20 by score")
st.dataframe(
    df.sort_values("score", ascending=False).head(20)[
        ["region","lat","lon","score","ghi_kwh_m2_yr","wind_speed_100m_ms"]
    ]
)
