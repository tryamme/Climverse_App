import streamlit as st
import streamlit_shadcn_ui as ui
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import os
from PIL import Image

# Paths
APP_DIR = os.path.dirname(os.path.abspath(__file__))
SHAPEFILE_PATH = os.path.join(APP_DIR, "Assets", "Polygons", "SHP", "climverse_Year1.shp")
LOGO_PATH = os.path.join(APP_DIR, "Assets", "Logo", "Tellus Logo.png")

logo_image = Image.open(LOGO_PATH)

# Streamlit config
st.set_page_config(
    page_title="Climverse App",
    page_icon=logo_image,
    layout="wide"
)

st.sidebar.title("Climverse App")
st.sidebar.info("Demo to visualize project area with Streamlit, GeoPandas & Folium")

st.title("Project Area Visualization")

# Load data
try:
    gdf = gpd.read_file(SHAPEFILE_PATH)
    if gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)
    if 'Area_ha' in gdf.columns:
        gdf['Area_ha'] = pd.to_numeric(gdf['Area_ha'], errors='coerce')
except Exception as e:
    st.error(f"Error loading shapefile: {e}")
    st.stop()

# Filters
st.write("Filter the data using the dropdowns below:")
filtered_gdf = gdf.copy()
filter_cols = st.columns(3)

with filter_cols[0]:
    if 'GP_Name' in gdf.columns:
        names = ["All"] + sorted(gdf['GP_Name'].unique())
        sel_name = st.selectbox("GP Name", names)
        if sel_name != "All":
            filtered_gdf = filtered_gdf[gdf['GP_Name'] == sel_name]
    if 'Block' in filtered_gdf.columns:
        blocks = ["All"] + sorted(filtered_gdf['Block'].unique())
        sel_block = st.selectbox("Block", blocks)
        if sel_block != "All":
            filtered_gdf = filtered_gdf[filtered_gdf['Block'] == sel_block]

with filter_cols[1]:
    if 'Parcel_Id' in filtered_gdf.columns:
        pids = ["All"] + sorted(filtered_gdf['Parcel_Id'].unique())
        sel_pid = st.selectbox("Parcel ID", pids)
        if sel_pid != "All":
            filtered_gdf = filtered_gdf[filtered_gdf['Parcel_Id'] == sel_pid]

with filter_cols[2]:
    if 'Area_ha' in filtered_gdf.columns:
        areas = ["All"] + sorted(filtered_gdf['Area_ha'].astype(float).unique())
        sel_area = st.selectbox("Area (ha)", areas)
        if sel_area != "All":
            filtered_gdf = filtered_gdf[filtered_gdf['Area_ha'] == sel_area]
    if 'Year' in filtered_gdf.columns:
        years = ["All"] + sorted(filtered_gdf['Year'].unique())
        sel_year = st.selectbox("Year", years)
        if sel_year != "All":
            filtered_gdf = filtered_gdf[filtered_gdf['Year'] == sel_year]

st.info(f"Displaying **{len(filtered_gdf)}** of **{len(gdf)}** parcels based on your selection.")

# Map setup
if filtered_gdf.empty:
    st.warning("No data to display.")
    st.stop()

center = [filtered_gdf.unary_union.centroid.y, filtered_gdf.unary_union.centroid.x]
zoom = 14 if len(filtered_gdf) > 0 else 10

m = folium.Map(location=center, zoom_start=zoom, tiles="CartoDB positron")
folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr='Google',
    name='Google Satellite Hybrid',
    overlay=False,
    control=True
).add_to(m)

folium.GeoJson(
    filtered_gdf,
    style_function=lambda x: {
        'fillColor': '#228B22',
        'color': '#E6DB0C',
        'weight': 2,
        'fillOpacity': 0.2
    }
).add_to(m)

# Layout: Map + Dashboard (combine old col2 and col3 into tabs)
map_col, dash_col1, dash_tabs_col = st.columns([2, 1, 1.5])

# Map Column
with map_col:
    st_folium(m, use_container_width=True, height=500)
    with st.expander("View Selected Data", expanded=False):
        cols = [c for c in ['GP_Name', 'Block', 'District', 'Area_ha'] if c in filtered_gdf.columns]
        df = filtered_gdf[cols].copy()
        if not df.empty and 'Area_ha' in df.columns:
            total = pd.DataFrame([{cols[0]: "**Total**", 'Area_ha': df['Area_ha'].sum()}])
            df = pd.concat([df, total], ignore_index=True)
        st.dataframe(df, hide_index=True, column_config={
            "Area_ha": st.column_config.NumberColumn("Area (ha)", format="%.2f")
        })

# Left Dashboard Column
with dash_col1:
    with ui.card(key="showing_on_map_card"):
        ui.element("h3", children=["Filter Selection Showing on Map"])
        
        # Inside the main card, two sub-cards
        with ui.card(key="selected_parcels_card"):
            ui.element("p", children=f"No of Selected Parcels: {len(filtered_gdf)}")
        
        with ui.card(key="selected_area_card"):
            ui.element("p", children=f"Selected Area (ha): {filtered_gdf['Area_ha'].sum():.2f}")

# Combined Column (Tabs for former col2 & col3 content)
with dash_tabs_col:
    tab1, tab2 = st.tabs(["Project Metrics", "Area by GP"])

    with tab1:
        with ui.card(key="project_metrics"):
            ui.element("h4", children=["Project Metrics"])
            if 'Area_ha' in gdf.columns:
                ui.metric_card(
                    title="Total Approved Project Area (ha)",
                    content=f"{gdf['Area_ha'].sum():.2f}"
                )

    with tab2:
        with ui.card(key="GP_area_card"):
            ui.element("h4", children=["Area by GP"])
            if 'GP_Name' in filtered_gdf.columns and not filtered_gdf.empty:
                gp_areas = filtered_gdf.groupby('GP_Name')['Area_ha'].sum()
                st.bar_chart(gp_areas)

