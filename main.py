import streamlit as st
import streamlit_shadcn_ui as ui
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import os
from PIL import Image
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px

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

st.title("Project Dashboard")

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
    # GP Name Filter
    if 'GP_Name' in filtered_gdf.columns:
        gp_names = sorted(filtered_gdf['GP_Name'].unique())
        names = ["All"] + gp_names
        sel_names = st.multiselect("GP Name", names, default=["All"])
        if "All" not in sel_names and sel_names:
            filtered_gdf = filtered_gdf[filtered_gdf['GP_Name'].isin(sel_names)]

    # Parcel ID Filter
    if 'Parcel_Id' in filtered_gdf.columns:
        parcel_ids = sorted(filtered_gdf['Parcel_Id'].unique())
        parcel_ids = ["All"] + parcel_ids
        selected_parcel_id = st.multiselect("Parcel ID", parcel_ids, default=["All"])
        if "All" not in selected_parcel_id and selected_parcel_id:
            filtered_gdf = filtered_gdf[filtered_gdf['Parcel_Id'].isin(selected_parcel_id)]

with filter_cols[1]:
    # Area (ha) Filter
    if 'Area_ha' in filtered_gdf.columns:
        areas = ["All"] + sorted(filtered_gdf['Area_ha'].astype(float).unique())
        sel_area = st.selectbox("Area (ha)", areas)
        if sel_area != "All":
            filtered_gdf = filtered_gdf[filtered_gdf['Area_ha'] == sel_area]

    # Year Filter
    if 'Year' in filtered_gdf.columns:
        years = ["All"] + sorted(filtered_gdf['Year'].unique())
        sel_year = st.selectbox("Year", years)
        if sel_year != "All":
            filtered_gdf = filtered_gdf[filtered_gdf['Year'] == sel_year]

with filter_cols[2]:
    # Block Filter
    if 'Block' in filtered_gdf.columns:
        blocks = ["All"] + sorted(filtered_gdf['Block'].unique())
        sel_block = st.selectbox("Block", blocks)
        if sel_block != "All":
            filtered_gdf = filtered_gdf[filtered_gdf['Block'] == sel_block]

    # District Filter
    if 'District' in filtered_gdf.columns:
        districts = ["All"] + sorted(filtered_gdf['District'].unique())
        sel_district = st.selectbox("District", districts)
        if sel_district != "All":
            filtered_gdf = filtered_gdf[filtered_gdf['District'] == sel_district]

st.info(f"Displaying **{len(filtered_gdf)}** of **{len(gdf)}** parcels based on your selection.")

# Function to make a bordered tile
def bordered_tile(label, value):
    st.markdown(
        f"""
        <div style="
            border: 2px solid #ddd;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            font-family: Arial, sans-serif;
            background-color: #024554;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        ">
            <h3 style="margin: 0;">{value}</h3>
            <p style="margin: 0; color: gray;">{label}</p>
        </div>
        """,
        unsafe_allow_html=True
    )


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
map_col, dash_tabs_col = st.columns([2, 3])

#Styling for first two selected tiles
def colored_tile(title, content, bg_color="#6A8C69"):
    st.markdown(
        f"""
        <div style="
            background-color: {bg_color};
            border: 2px solid black;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        ">
            <h4 style="margin: 0; color: white;">{title}</h4>
            <p style="margin: 0; font-size: 18px; color: white;">{content}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# Map Column
with map_col:
    # Top tiles
    top_col1, top_col2 = st.columns(2)
    with top_col1:
        colored_tile("Selected Area", f"{filtered_gdf['Area_ha'].sum():.2f}")
    with top_col2:
        colored_tile("No of Parcels", f"{len(filtered_gdf)}")
    st.markdown("<br>", unsafe_allow_html=True)

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


# Combined Column (Tabs for former col2 & col3 content)
with dash_tabs_col:
    tab1, tab2, tab3, tab4 = st.tabs(["Project Metrics", "Area Status", "Nursery", "SHG Identification"])

    with tab1:
        st.header("Project Metrics")

        # Create 2x2 grid
        col1, col2 = st.columns(2)
        
        #for adding a vertical space between first two tile and second two tiles
        spacer = st.empty()
        spacer.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)
        
        col3, col4 = st.columns(2)

        with col1:
            bordered_tile("Total Approved Area", f"{gdf['Area_ha'].sum():.2f} ha")
        with col2:
            bordered_tile("Trees", f"{gdf['Area_ha'].sum() * 2500:,.0f}")

        with col3:
            bordered_tile("SHGs", "15")
        with col4:
            bordered_tile("Employment Generated (Direct + Indirect)", "550")

        
    with tab2:
        # Create two columns with width ratio 2:3
        col1, col2 = st.columns([2, 3])

        #Styling for pie chart
        # --- Pie chart (3D style mimic) ---
        labels = ["Approved", "Pending", "Rejected"]
        values = [45, 30, 25]
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.3,
            marker=dict(
                colors=['#6BA292', '#FFD166', '#EF476F'],
                line=dict(color='#000000', width=1)
            ),
            textinfo='label+percent',
            textfont=dict(size=14, color='white'),
            pull=[0.05, 0.02, 0],
            direction="clockwise"
        )])

        fig_pie.update_traces(
            marker=dict(
                colors=['#6BA292', '#FFD166', '#EF476F'],
                line=dict(color='black', width=2)
            )
        )
        fig_pie.update_layout(
            title="3D Styled Pie Chart",
            title_x=0.5,
            showlegend=True,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        # ---- Tile 1: Pie chart ----
        with col1:
            st.markdown("<h3 style='text-align: center;'>Status Distribution</h3>",
    unsafe_allow_html=True)

            # Dummy data
            data = {"Yet to Plant": 45, "WIP": 30, "Plantation Done": 25}

            # Convert to DataFrame for Plotly
            import pandas as pd
            df = pd.DataFrame({
                "Status": list(data.keys()),
                "Value": list(data.values())
            })

            # Create interactive pie chart
            fig = px.pie(
                df,
                names="Status",
                values="Value",
                hole=0,  # 0 for full pie, >0 for donut chart
                #title="Project Status Distribution",
            )

           # 3D-style shading (not true 3D, but looks raised)
            fig.update_traces(
                pull=[0.10, 0.05, 0.05],  # slight pull-out for slices
                marker=dict(
                    line=dict(color='#000000', width=5)  # black border for 3D effect
                )
            )

            # Move legend to bottom center
            fig.update_layout(
                legend=dict(
                    orientation="h",  # horizontal
                    yanchor="bottom",
                    y=-0.2,
                    xanchor="center",
                    x=0.5
                )
            )

            # Show chart in Streamlit
            st.plotly_chart(fig, use_container_width=True)

        # ---- Tile 2: Table ----
        with col2:
            st.markdown("<h3 style='text-align: center;'>Project Status Overview</h3>",
    unsafe_allow_html=True)
            # Dummy dataframe
            df = pd.DataFrame({
                "GP_Name": ["GP1", "GP2", "GP3"],
                "Approved Area": [12.5, 15.2, 10.8],
                "LOA Collection Status": ["Completed", "Pending", "In Progress"],
                "SHG Mapping Status": ["Pending", "Completed", "Completed"],
                "Nursery Readiness": ["Ready", "Not Ready", "Ready"],
                "Plantation Status": ["Not Started", "Ongoing", "Completed"]
            })
            st.dataframe(df, use_container_width=True)

    with tab3:
        st.header("The Mangrove")
        st.image("https://cdn.pixabay.com/photo/2015/08/27/11/15/mangrove-910269_1280.jpg", width=800)

    with tab4:
        st.header("The Mangrove 2")
        st.image("https://cdn.pixabay.com/photo/2022/04/03/09/34/mangrove-7108484_1280.jpg", width=800)
