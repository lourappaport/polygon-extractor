import streamlit as st
import xml.etree.ElementTree as ET

st.title("KML Text Converter")
st.write("If you can't upload KML files directly, paste your KML content here:")

kml_text = st.text_area("Paste your KML content here:", height=200)

if st.button("Convert and Save"):
    if kml_text:
        try:
            # Validate KML
            root = ET.fromstring(kml_text)
            
            # Save to file
            with open('user_kml.kml', 'w') as f:
                f.write(kml_text)
            
            st.success("KML content saved! You can now use it in the main app.")
            st.download_button(
                "Download KML File",
                kml_text,
                "your_polygons.kml",
                "text/xml"
            )
        except Exception as e:
            st.error(f"Invalid KML format: {e}")
    else:
        st.warning("Please paste your KML content first.")