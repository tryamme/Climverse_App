
import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import os
from PIL import Image

# --- PATH SETUP ---
# It's good practice to build paths relative to the script's location
# This makes your app more portable.
APP_DIR = os.path.dirname(os.path.abspath(__file__))
SHAPEFILE_PATH = os.path.join(APP_DIR, "Assets", "Polygons", "SHP", "climverse_Year1.shp") 
LOGO_PATH = os.path.join(APP_DIR, "Assets", "Logo", "Tellus Logo.png")

#App Logo - Use the relative path
logo_image = Image.open(LOGO_PATH)

# ======================
# CUSTOM CSS FOR MODERN LOOK
# ======================
st.markdown("""
    <style>
    /* Remove Streamlit default padding */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    /* Title styling */
    h1 {
        font-weight: 700;
        color: #2E86C1;
    }
    /* Card container */
    .card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05);
    }
    /* Metric text */
    .metric-label {
        font-size: 0.9rem;
        color: gray;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: bold;
        color: #2E4053;
    }
    </style>
""", unsafe_allow_html=True)

#Favicon on brower - MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="Climverse App",
    page_icon=logo_image, # Use the PIL Image object
    layout="wide" # Use wide layout for better map visibility
)

st.logo(LOGO_PATH, link=None, icon_image=None)

# ======================
st.sidebar.title("Climverse App")
st.sidebar.info(
    """
    This is a demo application to visualize the project area
    using Streamlit, GeoPandas, and Folium.
    """
)

# --- MAIN PAGE ---
st.title("Project Area Visualization")

# Load the shapefile
try:
    gdf = gpd.read_file(SHAPEFILE_PATH)
    # Re-project to WGS84 (EPSG:4326) if not already, as it's the standard for web maps
    if gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)
    # --- Data Type Conversion ---
    # Ensure numeric columns are treated as numbers for calculations and sorting
    if 'Area_ha' in gdf.columns:
        gdf['Area_ha'] = pd.to_numeric(gdf['Area_ha'], errors='coerce')

except Exception as e:
    st.error(f"Error loading or processing shapefile: {e}")
    st.stop()

# --- FILTERING WIDGETS ---
st.write("Filter the data using the dropdowns below:")

# Create a copy of the GeoDataFrame to apply filters to
filtered_gdf = gdf.copy()

# --- CASCADING FILTERS ---
# This setup makes filters dependent on previous selections for a better user experience.
# We'll use 3 columns to give the dropdowns more space.
filter_cols = st.columns(3)

# Initialize selected variables to "All" to prevent errors if columns don't exist
selected_name = "All"
selected_block = "All"
selected_parcel_id = "All"
selected_area = "All"
selected_year = "All"

with filter_cols[0]:
    if 'GP_Name' in gdf.columns:
        names = ["All"] + sorted(gdf['GP_Name'].unique().tolist())
        selected_name = st.selectbox("GP Name", names)
        if selected_name != "All":
            filtered_gdf = filtered_gdf[filtered_gdf['GP_Name'] == selected_name]
    
    if 'Block' in filtered_gdf.columns:
        blocks = ["All"] + sorted(filtered_gdf['Block'].unique().tolist())
        selected_block = st.selectbox("Block", blocks)
        if selected_block != "All":
            filtered_gdf = filtered_gdf[filtered_gdf['Block'] == selected_block]

with filter_cols[1]:
    if 'Parcel_Id' in filtered_gdf.columns:
        parcel_ids = ["All"] + sorted(filtered_gdf['Parcel_Id'].unique().tolist())
        selected_parcel_id = st.selectbox("Parcel ID", parcel_ids)
        if selected_parcel_id != "All":
            filtered_gdf = filtered_gdf[filtered_gdf['Parcel_Id'] == selected_parcel_id]

with filter_cols[2]:
    if 'Area_ha' in filtered_gdf.columns:
        # Ensure areas are treated as numbers for correct sorting
        areas = ["All"] + sorted(gdf['Area_ha'].astype(float).unique().tolist())
        selected_area = st.selectbox("Area (ha)", areas)
        if selected_area != "All":
            filtered_gdf = filtered_gdf[filtered_gdf['Area_ha'] == selected_area]

    if 'Year' in filtered_gdf.columns:
        years = ["All"] + sorted(filtered_gdf['Year'].unique().tolist())
        selected_year = st.selectbox("Year", years)
        if selected_year != "All":
            filtered_gdf = filtered_gdf[filtered_gdf['Year'] == selected_year]

st.info(f"Displaying **{len(filtered_gdf)}** of **{len(gdf)}** parcels based on your selection.")

# --- MAP VISUALIZATION ---
# Adjust map center and zoom level based on the selection
if filtered_gdf.empty:
    st.warning("No data to display for the selected parcel.")
    st.stop()

map_center = [filtered_gdf.unary_union.centroid.y, filtered_gdf.unary_union.centroid.x]

# Determine if any filter is active to adjust zoom
is_filtered = not (
    selected_name == "All" and
    selected_parcel_id == "All" and
    selected_area == "All" and
    selected_block == "All" and
    selected_year == "All"
)
zoom_level = 14 if is_filtered and len(filtered_gdf) > 0 else 10

# Map preparation and generation
m = folium.Map(location=map_center, zoom_start=zoom_level, tiles="CartoDB positron")

folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', # URL template for Google Satellite Hybrid
    attr='Google',
    name='Google Satellite Hybrid',
    overlay=False, # Set to False for base maps, it's a separate base layer option
    control=True   # Add to the layer control
).add_to(m)

# Add the filtered GeoDataFrame to the map
folium.GeoJson(
    filtered_gdf,
    style_function=lambda x: {'fillColor': '#228B22', 'color': "#E6DB0C", 'weight': 2, 'fillOpacity': 0.2}
).add_to(m)

# --- PAGE LAYOUT: MAP AND DASHBOARDS ---
# Create three columns: a wider one for the map and two for dashboards.
map_col, dash_col1, dash_col2 = st.columns([2, 1, 1])

with map_col:
    # Display the map in the first column
    st_folium(m, use_container_width=True, height=500)

    # Expander for displaying the filtered data, placed below the map
    columns_to_show = ['GP_Name', 'Block', 'District', 'Area_ha']
    with st.expander("View Selected Data", expanded=False):
        # Check if the columns exist before trying to display them
        display_cols = [col for col in columns_to_show if col in filtered_gdf.columns]
        df_to_display = filtered_gdf[display_cols].copy()

        # Add a total row if 'Area_ha' is present and data exists
        if not df_to_display.empty and 'Area_ha' in df_to_display.columns:
            # Ensure 'Area_ha' is numeric before summing
            df_to_display['Area_ha'] = pd.to_numeric(df_to_display['Area_ha'], errors='coerce')

            # Create a summary dictionary for the total row
            summary_data = {col: '' for col in display_cols}
            summary_data[display_cols[0]] = '**Total**'
            summary_data['Area_ha'] = df_to_display['Area_ha'].sum()
            summary_df = pd.DataFrame([summary_data])

            # Append the total row
            df_to_display = pd.concat([df_to_display, summary_df], ignore_index=True)

        st.dataframe(
            df_to_display,
            hide_index=True,
            column_config={
                "Area_ha": st.column_config.NumberColumn(
                    "Area (ha)", format="%.2f"
                )
            },
        )

with dash_col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Showing on Map")
    # Display the number of selected parcels
    st.metric(label="Selected Parcels", value=f"{len(filtered_gdf)}")

    # Display the sum of the area for the selected parcels
    if 'Area_ha' in filtered_gdf.columns and not filtered_gdf.empty:
        st.metric(label="Selected Area (ha)", value=f"{filtered_gdf['Area_ha'].sum():.2f}")
    st.markdown('</div>', unsafe_allow_html=True)

with dash_col2:
    # We wrap the "Project Metrics" in a div with our custom class
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("Project Metrics")
    # Display total project area from the original unfiltered GeoDataFrame
    if 'Area_ha' in gdf.columns:
        st.metric(label="Total Project Area (ha)", value=f"{gdf['Area_ha'].sum():.2f}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="block-container">', unsafe_allow_html=True)
    st.subheader("Area by Block")
    if 'Block' in filtered_gdf.columns and 'Area_ha' in filtered_gdf.columns and not filtered_gdf.empty:
        block_areas = filtered_gdf.groupby('Block')['Area_ha'].sum()
        st.bar_chart(block_areas)
    st.markdown('</div>', unsafe_allow_html=True)
