import streamlit as st
import folium
from streamlit_folium import st_folium
from shapely.geometry import Polygon, Point
from geopy.geocoders import Nominatim
import pandas as pd
import numpy as np
import time
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

# Set page config to wide mode
st.set_page_config(layout="wide")

# Custom CSS to improve layout
st.markdown("""
    <style>
    .main > div {
        padding-top: 2rem;
    }
    .stButton>button {
        width: 100%;
        margin-top: 1rem;
    }
    .progress-info {
        margin: 1rem 0;
        padding: 1rem;
        background-color: #f0f2f6;
        border-radius: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize Nominatim geocoder with a meaningful user agent
geolocator = Nominatim(user_agent="my-address-extractor-app-v1.0")

# Initialize session state for map location
if 'map_location' not in st.session_state:
    st.session_state.map_location = [33.14773, -96.88784]  # Default location
if 'map_zoom' not in st.session_state:
    st.session_state.map_zoom = 15  # Default zoom level

# Layout with columns for better space utilization
col1, col2 = st.columns([2, 1])

with col1:
    st.title("Polygon Address Extractor")
    st.markdown("""
        Search for a location, then draw a polygon to extract addresses within that area.
        Use the drawing tools in the top right corner of the map.
    """)

    # Location search functionality
    search_location = st.text_input("Search location (e.g., city, address, landmark)", "")
    
    if st.button("Search", key="search_button"):
        try:
            # Geocode the search query
            location = geolocator.geocode(search_location)
            if location:
                st.session_state.map_location = [location.latitude, location.longitude]
                st.session_state.map_zoom = 15  # Reset zoom to appropriate level
                st.success(f"Found: {location.address}")
                st.experimental_rerun()  # Rerun to update map
            else:
                st.error("Location not found. Please try a different search term.")
        except Exception as e:
            st.error(f"Error searching location: {str(e)}")

# Cache the map creation to improve performance
@st.cache_data
def create_base_map(location, zoom_start):
    m = folium.Map(location=location, zoom_start=zoom_start)
    
    # Add map layers
    folium.TileLayer('openstreetmap', name='OpenStreetMap').add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Satellite"
    ).add_to(m)
    
    # Add drawing controls
    draw = folium.plugins.Draw(
        export=True,
        position='topright',
        draw_options={
            'polyline': False,
            'rectangle': True,
            'circle': False,
            'circlemarker': False,
            'marker': False
        }
    )
    draw.add_to(m)
    
    folium.LayerControl().add_to(m)
    return m

# Create and display the map with current location
with col1:
    m = create_base_map(st.session_state.map_location, st.session_state.map_zoom)
    output = st_folium(
        m,
        width='100%',
        height=700,
    )

# Handle reverse geocoding with retry mechanism and proper coordinate validation
def reverse_geocode_with_retry(lat, lon, max_retries=3):
    try:
        lat = float(lat)
        lon = float(lon)
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            raise ValueError("Coordinates out of valid range")
    except (ValueError, TypeError) as e:
        st.error(f"Invalid coordinates: ({lat}, {lon})")
        return None

    for attempt in range(max_retries):
        try:
            coords = (lat, lon)
            location = geolocator.reverse(coords, language='en', zoom=18)
            return location
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(1 * (attempt + 1))
        except Exception as e:
            st.error(f"Geocoding error: {str(e)}")
            return None

# Rest of the functionality in the second column
with col2:
    # Configuration options in a cleaner layout
    st.subheader("Settings")
    
    # Format the grid density value to show 5 decimal places
    grid_size = st.slider(
        "Grid Density (meters)",
        min_value=0.00005,
        max_value=0.001,
        value=0.0002,
        step=0.00001,
        format="%.5f"  # Show 5 decimal places
    )
    st.caption("Smaller value = more precise but slower")
    st.write(f"Current grid size: {grid_size:.5f}")  # Display current value
    
    # Add a visual separator
    st.divider()
    
    batch_size = st.slider(
        "Batch Size",
        min_value=10,
        max_value=100,
        value=50,
        step=10,
        help="Number of points to process at once"
    )
    st.caption("Larger batch size = faster but more memory intensive")

def generate_grid_within_polygon(polygon, grid_size):
    min_x, min_y, max_x, max_y = polygon.bounds
    x_points = np.arange(min_x, max_x, grid_size)
    y_points = np.arange(min_y, max_y, grid_size)
    
    grid_points = []
    for y in y_points:
        for x in x_points:
            if Point(x, y).within(polygon):
                grid_points.append((y, x))
    return grid_points

# Process drawn polygon
if output is not None and 'all_drawings' in output and output['all_drawings']:
    try:
        drawn_shape = output['all_drawings'][0]
        
        if drawn_shape['geometry']['type'] not in ['Polygon', 'Rectangle']:
            st.error("Please draw a polygon or rectangle on the map.")
            st.stop()
            
        polygon_coords = drawn_shape['geometry']['coordinates'][0]
        polygon = Polygon([(coord[0], coord[1]) for coord in polygon_coords])
        
        with col2:
            st.success("Area successfully defined!")

            if st.button("Extract Addresses", type="primary"):
                grid_points = generate_grid_within_polygon(polygon, grid_size)
                
                if not grid_points:
                    st.error("No points generated within the polygon. Try adjusting the grid size.")
                    st.stop()
                
                total_points = len(grid_points)
                st.info(f"Total points to process: {total_points}")
                
                # Create containers for progress information
                progress_container = st.container()
                with progress_container:
                    progress_status = st.empty()
                    progress_bar = st.progress(0)
                    points_status = st.empty()
                    address_status = st.empty()
                    time_status = st.empty()
                
                addresses = []
                seen_addresses = set()
                processed_count = 0
                start_time = time.time()
                
                for i in range(0, total_points, batch_size):
                    batch = grid_points[i:i + batch_size]
                    
                    for lat, lon in batch:
                        try:
                            location = reverse_geocode_with_retry(lat, lon)
                            processed_count += 1
                            
                            if location and location.address not in seen_addresses:
                                seen_addresses.add(location.address)
                                address_info = location.raw['address']
                                addresses.append({
                                    'Latitude': lat,
                                    'Longitude': lon,
                                    'Address': location.address,
                                    'Postal Code': address_info.get('postcode', ''),
                                    'City': address_info.get('city', ''),
                                    'State': address_info.get('state', ''),
                                    'Country': address_info.get('country', '')
                                })
                            
                            # Update progress information
                            progress = processed_count / total_points
                            progress_bar.progress(progress)
                            
                            # Calculate time estimates
                            elapsed_time = time.time() - start_time
                            points_per_second = processed_count / elapsed_time
                            remaining_points = total_points - processed_count
                            estimated_time_remaining = remaining_points / points_per_second if points_per_second > 0 else 0
                            
                            # Update status displays
                            progress_status.info(f"Processing... ({processed_count}/{total_points})")
                            points_status.text(f"Points processed: {processed_count:,}/{total_points:,}")
                            address_status.text(f"Unique addresses found: {len(addresses):,}")
                            time_status.text(f"Estimated time remaining: {estimated_time_remaining:.1f} seconds")
                            
                            time.sleep(1)  # Respect Nominatim's usage policy
                            
                        except Exception as e:
                            st.warning(f"Error processing point ({lat}, {lon}): {str(e)}")
                            continue
                
                # Clear progress information and show completion message
                progress_container.empty()
                
                if addresses:
                    df = pd.DataFrame(addresses)
                    st.success(f"✅ Completed! Found {len(addresses):,} unique addresses")
                    
                    # Create tabs for results
                    tab1, tab2 = st.tabs(["Preview", "Download"])
                    
                    with tab1:
                        st.dataframe(df, height=400)
                    
                    with tab2:
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="⬇️ Download Results (CSV)",
                            data=csv,
                            file_name="polygon_addresses.csv",
                            mime="text/csv",
                            key='download-csv'
                        )
                else:
                    st.warning("No addresses found in the selected area. Try adjusting the grid size or selecting a different area.")
                    
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
else:
    with col2:
        st.info("Draw a polygon or rectangle on the map to begin.")
