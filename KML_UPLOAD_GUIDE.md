# How to Upload Your Own KML File

## Option 1: If you have a KML file already

1. **Copy your KML file content**
2. **Use the KML converter tool**: `streamlit run kml_converter.py --server.port 8502`
3. **Paste the content** and download the converted file

## Option 2: Create KML from coordinates

1. **Get your polygon coordinates** (longitude, latitude pairs)
2. **Use the KML creator tool**: `streamlit run create_kml.py --server.port 8503`
3. **Enter coordinates** and download the generated KML

## Option 3: Manual file creation

Create a file with `.kml` extension containing:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>My Polygons</name>
    
    <Placemark>
      <name>Area 1</name>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>
              -96.890000,33.148000,0
              -96.885000,33.148000,0
              -96.885000,33.145000,0
              -96.890000,33.145000,0
              -96.890000,33.148000,0
            </coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
    
    <!-- Add more Placemark elements for additional polygons -->
    
  </Document>
</kml>
```

## KML File Requirements

✅ **Supported formats:**
- Standard KML 2.2 format
- Multiple polygons per file (up to 100)
- Named polygons (will show in dropdown)

✅ **Coordinate format:**
- longitude,latitude,altitude (altitude can be 0)
- First and last coordinates should be the same (closed polygon)
- Minimum 3 coordinate pairs per polygon

✅ **File size:**
- Keep under 10MB for best performance
- Large files with many polygons may take longer to process