import streamlit as st
import folium
from streamlit_folium import st_folium
from shapely.geometry import Polygon, Point
from geopy.geocoders import Nominatim
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

# Set page config to wide mode
st.set_page_config(layout="wide")

# Custom CSS for layout and attribution
st.markdown("""
    <style>
    .main > div {
        padding-top: 1rem;
    }
    .stButton>button {
        width: 100%;
        margin-top: 0.5rem;
    }
    .attribution {
        position: fixed;
        bottom: 10px;
        right: 10px;
        font-size: 12px;
        color: #666;
        background-color: white;
        padding: 5px;
        border-radius: 4px;
        z-index: 1000;
    }
    </style>
    <div class="attribution">
        Data © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors<br>
        Geocoding by <a href="https://nominatim.org/">Nominatim</a>
    </div>
    """, unsafe_allow_html=True)

# Initialize session state
if 'last_request_time' not in st.session_state:
    st.session_state.last_request_time = datetime.min
if 'request_count' not in st.session_state:
    st.session_state.request_count = 0
if 'cache' not in st.session_state:
    st.session_state.cache = {}
if 'cache_timestamp' not in st.session_state:
    st.session_state.cache_timestamp = datetime.now()
if 'map_location' not in st.session_state:
    st.session_state.map_location = [33.14773, -96.88784]
if 'map_zoom' not in st.session_state:
    st.session_state.map_zoom = 15

# Constants
MAX_AREA = 5.0  # Maximum area in square kilometers
MAX_POINTS = 1000  # Maximum points per request
COOLDOWN_MINUTES = 5  # Cooldown period between requests
REQUESTS_PER_PERIOD = 3  # Number of requests allowed per period
CACHE_DURATION = timedelta(hours=24)  # Cache duration

# Initialize Nominatim geocoder
geolocator = Nominatim(
    user_agent="FlytrexAddressExtractor/1.0 (+https://www.flytrex.com) Contact: shaik@flytrex.com"
)

def clear_expired_cache():
    current_time = datetime.now()
    if current_time - st.session_state.cache_timestamp > CACHE_DURATION:
        st.session_state.cache = {}
        st.session_state.cache_timestamp = current_time

def get_cache_key(lat, lon):
    return f"{lat:.6f},{lon:.6f}"

def check_polygon_size(polygon):
    bounds = polygon.bounds
    width = abs(bounds[2] - bounds[0]) * 111
    height = abs(bounds[3] - bounds[1]) * 111
    area = width * height
    return area <= MAX_AREA, area

def check_points_limit(points):
    return len(points) <= MAX_POINTS, len(points)

def check_rate_limit():
    current_time = datetime.now()
    time_diff = current_time - st.session_state.last_request_time
    
    if time_diff > timedelta(minutes=COOLDOWN_MINUTES):
        st.session_state.request_count = 0
        st.session_state.last_request_time = current_time
        return True
    
    if st.session_state.request_count >= REQUESTS_PER_PERIOD:
        return False
    
    return True

def reverse_geocode_with_retry(lat, lon, max_retries=3, initial_delay=1):
    try:
        lat = float(lat)
        lon = float(lon)
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            raise ValueError("Coordinates out of valid range")
        
        cache_key = get_cache_key(lat, lon)
        if cache_key in st.session_state.cache:
            return st.session_state.cache[cache_key]
        
        for attempt in range(max_retries):
            try:
                delay = initial_delay * (2 ** attempt)
                time.sleep(delay)
                
                location = geolocator.reverse((lat, lon), language='en', zoom=18)
                
                if location:
                    st.session_state.cache[cache_key] = location
                return location
                
            except (GeocoderTimedOut, GeocoderServiceError) as e:
                if attempt == max_retries - 1:
                    raise e
                continue
            except ConnectionError as e:
                if attempt == max_retries - 1:
                    raise e
                continue
                
    except Exception as e:
        return None

# Layout with columns
col1, col2 = st.columns([2, 1])

with col1:
    st.title("Polygon Address Extractor")
    st.markdown("""
        Search for a location, then draw a polygon to extract addresses within that area.
        Use the drawing tools in the top right corner of the map.
    """)

    # Location search
    search_location = st.text_input("Search location (e.g., city, address, landmark)", "")
    
    if st.button("Search", key="search_button"):
        try:
            location = geolocator.geocode(search_location)
            if location:
                st.session_state.map_location = [location.latitude, location.longitude]
                st.session_state.map_zoom = 15
                st.success(f"Found: {location.address}")
                st.rerun()
            else:
                st.error("Location not found. Please try a different search term.")
        except Exception as e:
            st.error(f"Error searching location: {str(e)}")

# Map creation and display
@st.cache_data
def create_base_map(location, zoom_start):
    m = folium.Map(location=location, zoom_start=zoom_start)
    folium.TileLayer('openstreetmap', name='OpenStreetMap').add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Satellite"
    ).add_to(m)
    
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

with col1:
    m = create_base_map(st.session_state.map_location, st.session_state.map_zoom)
    output = st_folium(m, width='100%', height=700)

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
        format="%.5f"
    )
    st.caption("Smaller value = more precise but slower")
    
    # Process drawn polygon
    if output is not None and 'all_drawings' in output and output['all_drawings']:
        try:
            clear_expired_cache()
            
            drawn_shape = output['all_drawings'][0]
            
            if drawn_shape['geometry']['type'] not in ['Polygon', 'Rectangle']:
                st.error("Please draw a polygon or rectangle on the map.")
                st.stop()
                
            polygon_coords = drawn_shape['geometry']['coordinates'][0]
            polygon = Polygon([(coord[0], coord[1]) for coord in polygon_coords])
            
            is_valid_size, area = check_polygon_size(polygon)
            if not is_valid_size:
                st.error(f"Selected area is too large ({area:.2f} km²). Please select an area smaller than {MAX_AREA} km².")
                st.stop()

            min_x, min_y, max_x, max_y = polygon.bounds
            x_points = np.arange(min_x, max_x, grid_size)
            y_points = np.arange(min_y, max_y, grid_size)
            
            grid_points = []
            for y in y_points:
                for x in x_points:
                    if Point(x, y).within(polygon):
                        grid_points.append((y, x))
            
            is_valid_points, point_count = check_points_limit(grid_points)
            if not is_valid_points:
                st.error(f"Too many points ({point_count}). Please select a smaller area or increase grid size.")
                st.stop()
            
            if not check_rate_limit():
                remaining_time = COOLDOWN_MINUTES - (datetime.now() - st.session_state.last_request_time).total_seconds() / 60
                st.error(f"Rate limit exceeded. Please wait {remaining_time:.1f} minutes before trying again.")
                st.stop()
            
            st.success("Area successfully defined!")

            if st.button("Extract Addresses", type="primary"):
                st.session_state.request_count += 1
                st.session_state.last_request_time = datetime.now()
                
                progress_container = st.container()
                with progress_container:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    addresses = []
                    seen_addresses = set()
                    
                    for idx, (lat, lon) in enumerate(grid_points):
                        try:
                            location = reverse_geocode_with_retry(lat, lon)
                            
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
                            
                            progress = (idx + 1) / len(grid_points)
                            progress_bar.progress(progress)
                            status_text.text(f"Processed {idx + 1}/{len(grid_points)} points")
                            
                        except Exception as e:
                            continue
                    
                    if addresses:
                        df = pd.DataFrame(addresses)
                        st.success(f"✅ Found {len(addresses)} unique addresses")
                        
                        tab1, tab2 = st.tabs(["Preview", "Download"])
                        with tab1:
                            st.dataframe(df, height=400)
                        with tab2:
                            csv = df.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                "⬇️ Download Results (CSV)",
                                csv,
                                "addresses.csv",
                                "text/csv",
                                key='download-csv'
                            )
                    else:
                        st.warning("No addresses found in the selected area.")
                        
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
    else:
        st.info("Draw a polygon or rectangle on the map to begin.")
