"""Interactive dashboard: ``uv run streamlit run streamlit_app.py``."""

from __future__ import annotations

import asyncio

import altair as alt
import pydeck as pdk
import streamlit as st

from worldpop_analysis import REGIONS, BBox, WorldPopClient, WorldPopError, growth_table, summarize
from worldpop_analysis.cli import sample_years

st.set_page_config(page_title="WorldPop Explorer", page_icon="🌍", layout="wide")


@st.cache_data(show_spinner=False, ttl=24 * 3600)
def fetch_series(bbox: BBox, years: tuple[int, ...]) -> dict[int, float]:
    async def run() -> dict[int, float]:
        async with WorldPopClient() as wp:
            return await wp.population_series(bbox.to_geojson(), years)

    return asyncio.run(run())


with st.sidebar:
    st.header("Area of interest")
    choice = st.selectbox(
        "Region",
        [*REGIONS, "custom"],
        format_func=lambda k: "Custom bounding box" if k == "custom" else REGIONS[k].name,
    )
    if choice == "custom":
        raw = st.text_input("min_lon, min_lat, max_lon, max_lat", "-4.15, 5.20, -3.85, 5.45")
        try:
            bbox = BBox.parse(raw)
        except ValueError as exc:
            st.error(str(exc))
            st.stop()
        label = "Custom area"
    else:
        bbox, label = REGIONS[choice].bbox, f"{REGIONS[choice].name}, {REGIONS[choice].country}"

    start, end = st.slider("Years", 2000, 2020, (2000, 2020))
    step = st.select_slider("Sample every", [1, 2, 5], value=5, format_func=lambda s: f"{s} yr")
    st.caption("Data: WorldPop global 100 m unconstrained population counts (wpgppop).")

st.title("🌍 WorldPop Explorer")
st.markdown(f"Population dynamics for **{label}** · {bbox.area_km2():,.0f} km²")

lat, lon = bbox.center
st.pydeck_chart(
    pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=8),
        layers=[
            pdk.Layer(
                "PolygonLayer",
                data=[{"polygon": bbox.ring}],
                get_polygon="polygon",
                get_fill_color=[230, 120, 40, 60],
                get_line_color=[230, 120, 40],
                line_width_min_pixels=2,
            )
        ],
    ),
    height=320,
)

try:
    with st.spinner("Running zonal statistics on WorldPop servers…"):
        series = fetch_series(bbox, tuple(sample_years(start, end, step)))
except (WorldPopError, ValueError) as exc:
    st.error(f"Could not retrieve data: {exc}")
    st.stop()

summary = summarize(series)
table = growth_table(series, area_km2=bbox.area_km2())

c1, c2, c3, c4 = st.columns(4)
c1.metric(f"Population {summary.end_year}", f"{summary.end_population:,.0f}")
c2.metric(f"Change since {summary.start_year}", f"{summary.total_change_pct:+.1f}%")
c3.metric("CAGR", f"{summary.cagr:.2%}")
c4.metric(
    "Doubling time",
    "—" if summary.doubling_years == float("inf") else f"{summary.doubling_years:.0f} yrs",
)

left, right = st.columns(2)
with left:
    st.subheader("Population")
    st.altair_chart(
        alt.Chart(table)
        .mark_area(line=True, opacity=0.3)
        .encode(
            x=alt.X("year:O", title=None),
            y=alt.Y("population:Q", title="People"),
            tooltip=["year", alt.Tooltip("population:Q", format=",.0f")],
        ),
        use_container_width=True,
    )
with right:
    st.subheader("Annualised growth")
    st.altair_chart(
        alt.Chart(table.dropna(subset=["annual_growth_pct"]))
        .mark_bar()
        .encode(
            x=alt.X("year:O", title=None),
            y=alt.Y("annual_growth_pct:Q", title="% per year"),
            tooltip=["year", alt.Tooltip("annual_growth_pct:Q", format=".2f")],
        ),
        use_container_width=True,
    )

st.subheader("Data")
st.dataframe(table, hide_index=True, use_container_width=True)
st.download_button("Download CSV", table.to_csv(index=False), f"worldpop_{choice}.csv", "text/csv")
