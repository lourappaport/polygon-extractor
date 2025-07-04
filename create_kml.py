import streamlit as st

st.title("Create KML from Coordinates")

st.write("Enter your polygon coordinates (longitude, latitude pairs):")

polygon_name = st.text_input("Polygon Name:", "My Polygon")
coordinates = st.text_area(
    "Enter coordinates (one per line: longitude,latitude):", 
    placeholder="-96.890000,33.148000\n-96.885000,33.148000\n-96.885000,33.145000\n-96.890000,33.145000",
    height=150
)

if st.button("Generate KML"):
    if coordinates:
        lines = coordinates.strip().split('\n')
        coord_pairs = []
        
        for line in lines:
            if ',' in line:
                parts = line.strip().split(',')
                if len(parts) >= 2:
                    coord_pairs.append(f"{parts[0]},{parts[1]},0")
        
        if len(coord_pairs) >= 3:
            # Close the polygon by adding first point at the end
            if coord_pairs[0] != coord_pairs[-1]:
                coord_pairs.append(coord_pairs[0])
            
            kml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Generated Polygons</name>
    <Placemark>
      <name>{polygon_name}</name>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>
              {chr(10).join(coord_pairs)}
            </coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
  </Document>
</kml>'''
            
            st.success("KML generated successfully!")
            st.code(kml_content, language='xml')
            
            st.download_button(
                "Download KML File",
                kml_content,
                f"{polygon_name.replace(' ', '_')}.kml",
                "text/xml"
            )
        else:
            st.error("Need at least 3 coordinate pairs for a polygon")
    else:
        st.warning("Please enter coordinates")