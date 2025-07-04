import streamlit as st
import folium
from streamlit_folium import st_folium
import json

st.set_page_config(layout="wide", page_title="KML Polygon Tester")

st.title("🧪 KML Polygon Tester Interface")
st.markdown("**Easy testing interface for your KML polygon functionality**")

# Pre-defined test polygons for different areas
test_polygons = {
    "Dallas Residential Area": {
        "coordinates": [
            [-96.890000, 33.148000],
            [-96.885000, 33.148000], 
            [-96.885000, 33.145000],
            [-96.890000, 33.145000],
            [-96.890000, 33.148000]
        ],
        "description": "Small residential area in Dallas"
    },
    "Downtown Dallas": {
        "coordinates": [
            [-96.798000, 32.776000],
            [-96.795000, 32.776000],
            [-96.795000, 32.773000],
            [-96.798000, 32.773000],
            [-96.798000, 32.776000]
        ],
        "description": "Downtown Dallas business district"
    },
    "Plano Suburb": {
        "coordinates": [
            [-96.750000, 33.020000],
            [-96.747000, 33.020000],
            [-96.747000, 33.017000],
            [-96.750000, 33.017000],
            [-96.750000, 33.020000]
        ],
        "description": "Suburban area in Plano"
    },
    "Austin Tech Area": {
        "coordinates": [
            [-97.750000, 30.270000],
            [-97.747000, 30.270000],
            [-97.747000, 30.267000],
            [-97.750000, 30.267000],
            [-97.750000, 30.270000]
        ],
        "description": "Tech area in Austin"
    },
    "Houston Energy Corridor": {
        "coordinates": [
            [-95.620000, 29.740000],
            [-95.617000, 29.740000],
            [-95.617000, 29.737000],
            [-95.620000, 29.737000],
            [-95.620000, 29.740000]
        ],
        "description": "Energy corridor in Houston"
    }
}

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📍 Visual Polygon Preview")
    
    # Create map showing all test polygons
    m = folium.Map(location=[32.7767, -96.7970], zoom_start=8)
    
    colors = ['red', 'blue', 'green', 'purple', 'orange']
    
    for i, (name, data) in enumerate(test_polygons.items()):
        # Convert to folium format [lat, lon]
        folium_coords = [[coord[1], coord[0]] for coord in data['coordinates']]
        
        folium.Polygon(
            locations=folium_coords,
            color=colors[i % len(colors)],
            weight=3,
            fill=True,
            fillOpacity=0.3,
            popup=f"<b>{name}</b><br>{data['description']}",
            tooltip=name
        ).add_to(m)
    
    # Display map
    map_data = st_folium(m, width='100%', height=500)

with col2:
    st.subheader("🎮 Test Controls")
    
    # Test polygon selector
    selected_polygon = st.selectbox(
        "Choose test polygon:",
        options=list(test_polygons.keys()),
        help="Select a pre-made polygon for testing"
    )
    
    st.info(f"**Selected**: {test_polygons[selected_polygon]['description']}")
    
    # Generate KML button
    if st.button("🔧 Generate Test KML", type="primary"):
        # Create KML content
        kml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Test Polygons</name>
    <description>Generated test polygons for KML functionality testing</description>
    
    <Placemark>
      <name>{selected_polygon}</name>
      <description>{test_polygons[selected_polygon]['description']}</description>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>'''
        
        # Add coordinates
        for coord in test_polygons[selected_polygon]['coordinates']:
            kml_content += f"\n              {coord[0]},{coord[1]},0"
        
        kml_content += '''
            </coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
  </Document>
</kml>'''
        
        # Save the file
        with open('/app/test_polygon.kml', 'w') as f:
            f.write(kml_content)
        
        st.success("✅ Test KML generated!")
        
        # Download button
        st.download_button(
            "⬇️ Download Test KML",
            kml_content,
            f"test_{selected_polygon.replace(' ', '_').lower()}.kml",
            "text/xml"
        )
    
    st.divider()
    
    # Multi-polygon KML generator
    st.subheader("🔢 Multi-Polygon Test")
    
    selected_multiple = st.multiselect(
        "Select multiple polygons:",
        options=list(test_polygons.keys()),
        default=list(test_polygons.keys())[:3],
        help="Create KML with multiple polygons"
    )
    
    if st.button("🔧 Generate Multi-Polygon KML"):
        if selected_multiple:
            kml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Multi-Polygon Test</name>
    <description>Multiple test polygons for comprehensive testing</description>
'''
            
            for polygon_name in selected_multiple:
                kml_content += f'''
    <Placemark>
      <name>{polygon_name}</name>
      <description>{test_polygons[polygon_name]['description']}</description>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>'''
                
                for coord in test_polygons[polygon_name]['coordinates']:
                    kml_content += f"\n              {coord[0]},{coord[1]},0"
                
                kml_content += '''
            </coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>'''
            
            kml_content += '''
  </Document>
</kml>'''
            
            # Save multi-polygon file
            with open('/app/multi_test_polygons.kml', 'w') as f:
                f.write(kml_content)
            
            st.success(f"✅ Multi-polygon KML with {len(selected_multiple)} polygons generated!")
            
            st.download_button(
                "⬇️ Download Multi-Polygon KML",
                kml_content,
                "multi_test_polygons.kml",
                "text/xml"
            )

# Custom polygon creator
st.divider()
st.subheader("✏️ Custom Polygon Creator")

col3, col4 = st.columns(2)

with col3:
    st.write("**Create your own test polygon:**")
    
    polygon_name = st.text_input("Polygon name:", "My Test Area")
    polygon_desc = st.text_input("Description:", "Custom test polygon")
    
    st.write("**Enter coordinates (longitude, latitude):**")
    coord_input = st.text_area(
        "One coordinate pair per line:",
        value="-96.890000,33.148000\n-96.885000,33.148000\n-96.885000,33.145000\n-96.890000,33.145000",
        height=150,
        help="Format: longitude,latitude"
    )

with col4:
    if st.button("🔧 Generate Custom KML"):
        if coord_input and polygon_name:
            try:
                lines = coord_input.strip().split('\n')
                coordinates = []
                
                for line in lines:
                    if ',' in line:
                        parts = line.strip().split(',')
                        if len(parts) >= 2:
                            lon, lat = float(parts[0]), float(parts[1])
                            coordinates.append([lon, lat])
                
                if len(coordinates) >= 3:
                    # Close polygon
                    if coordinates[0] != coordinates[-1]:
                        coordinates.append(coordinates[0])
                    
                    kml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Custom Test Polygon</name>
    <Placemark>
      <name>{polygon_name}</name>
      <description>{polygon_desc}</description>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>'''
                    
                    for coord in coordinates:
                        kml_content += f"\n              {coord[0]},{coord[1]},0"
                    
                    kml_content += '''
            </coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
  </Document>
</kml>'''
                    
                    with open('/app/custom_test_polygon.kml', 'w') as f:
                        f.write(kml_content)
                    
                    st.success("✅ Custom KML generated!")
                    
                    st.download_button(
                        "⬇️ Download Custom KML",
                        kml_content,
                        f"custom_{polygon_name.replace(' ', '_').lower()}.kml",
                        "text/xml"
                    )
                else:
                    st.error("Need at least 3 coordinate pairs")
                    
            except Exception as e:
                st.error(f"Error: {e}")

# Quick test section
st.divider()
st.subheader("🚀 Quick Testing")

col5, col6, col7 = st.columns(3)

with col5:
    if st.button("🏠 Test Small Area", help="Quick test with small residential area"):
        st.info("Generate small area KML and upload to main app")

with col6:
    if st.button("🏢 Test Large Area", help="Test with larger commercial area"):
        st.info("Generate large area KML for comprehensive testing")

with col7:
    if st.button("🔄 Test Multi-Area", help="Test with multiple polygons"):
        st.info("Generate multi-polygon KML for batch testing")

# Instructions
st.divider()
st.subheader("📋 Testing Instructions")

instructions = """
### How to Test Your KML System:

1. **Generate Test KML**:
   - Select a polygon from the dropdown above
   - Click "Generate Test KML" 
   - Download the generated KML file

2. **Upload to Main App**:
   - Go to your main app at `http://localhost:8501`
   - Use the "Upload KML File" section
   - Upload the downloaded KML file

3. **Test Analysis**:
   - Select polygon from dropdown in main app
   - Click "Analyze KML Polygon"
   - Watch progress and view results

4. **Test Different Scenarios**:
   - Single polygon vs multiple polygons
   - Different geographic areas
   - Various polygon sizes

### Test Scenarios to Try:
- ✅ **Single small polygon** (Dallas Residential)
- ✅ **Multiple polygons** (All 5 areas)
- ✅ **Custom polygon** (Your own coordinates)
- ✅ **Different cities** (Dallas, Austin, Houston)
"""

st.markdown(instructions)

# Sample coordinates for different areas
with st.expander("📍 Sample Coordinates for Different Areas"):
    sample_coords = {
        "New York Manhattan": "-73.9857,40.7484\n-73.9847,40.7484\n-73.9847,40.7474\n-73.9857,40.7474",
        "Los Angeles Downtown": "-118.2537,34.0522\n-118.2527,34.0522\n-118.2527,34.0512\n-118.2537,34.0512",
        "Chicago Loop": "-87.6298,41.8781\n-87.6288,41.8781\n-87.6288,41.8771\n-87.6298,41.8771",
        "Miami Beach": "-80.1300,25.7907\n-80.1290,25.7907\n-80.1290,25.7897\n-80.1300,25.7897",
    }
    
    for city, coords in sample_coords.items():
        st.code(f"{city}:\n{coords}", language="text")