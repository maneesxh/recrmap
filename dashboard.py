import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import re

# ==========================================
# 1. PRE-LOADED COORDINATES (The Heavy Lifting)
# ==========================================
# I have extracted the cities from your files and added their Lat/Longs here.
CITY_COORDINATES = {
    # Maharashtra
    "nagpur": [21.1458, 79.0882], "mumbai": [19.0760, 72.8777], "pune": [18.5204, 73.8567],
    "kamptee": [21.2235, 79.1943], "akola": [20.7002, 77.0082], "amravati": [20.9374, 77.7796],
    "aurangabad": [19.8762, 75.3433], "nashik": [19.9975, 73.7898], "yavatmal": [20.3888, 78.1204],
    "sangli": [16.8524, 74.5815], "kolhapur": [16.7050, 74.2433], "bhandara": [21.1777, 79.6570],
    "wardha": [20.7453, 78.6022], "chandrapur": [19.9615, 79.2961], "gondia": [21.4624, 80.2210],
    # Telangana & AP
    "hyderabad": [17.3850, 78.4867], "secunderabad": [17.4399, 78.4983], "vijayawada": [16.5062, 80.6480],
    "guntur": [16.3067, 80.4365], "visakhapatnam": [17.6868, 83.2185], "vizag": [17.6868, 83.2185],
    "rajahmundry": [17.0005, 81.8040], "kakinada": [16.9891, 82.2475], "nellore": [14.4426, 79.9865],
    "kurnool": [15.8281, 78.0373], "warangal": [17.9689, 79.5941], "tirupati": [13.6288, 79.4192],
    "eluru": [16.7107, 81.0952], "ongole": [15.5057, 80.0499], "tenali": [16.2430, 80.6409],
    "nizamabad": [18.6725, 78.0941], "khammam": [17.2473, 80.1514],
    # Uttar Pradesh
    "gorakhpur": [26.7606, 83.3732], "lucknow": [26.8467, 80.9462], "kanpur": [26.4499, 80.3319],
    "varanasi": [25.3176, 82.9739], "allahabad": [25.4358, 81.8463], "prayagraj": [25.4358, 81.8463],
    "deoria": [26.5081, 83.7780], "kushinagar": [26.9030, 83.9873], "basti": [26.8140, 82.7630],
    "azamgarh": [26.0722, 83.1859], "faizabad": [26.7730, 82.1448], "ayodhya": [26.7922, 82.1998],
    "akbarpur": [26.4385, 82.5350], "mirzapur": [25.1337, 82.5644], "ghazipur": [25.5804, 83.5772],
    # Rajasthan
    "ajmer": [26.4499, 74.6399], "jaipur": [26.9124, 75.7873], "jodhpur": [26.2389, 73.0243],
    "kishangarh": [26.5741, 74.8622], "beawar": [26.1030, 74.3218], "nasirabad": [26.3056, 74.7335],
    "pushkar": [26.4886, 74.5509], "sikar": [27.6094, 75.1398], "bhilwara": [25.3407, 74.6313],
    # Tamil Nadu
    "chennai": [13.0827, 80.2707], "coimbatore": [11.0168, 76.9558], "madurai": [9.9252, 78.1198],
    "salem": [11.6643, 78.1460], "tiruchirappalli": [10.7905, 78.7047], "vellore": [12.9165, 79.1325],
    "tiruvannamalai": [12.2253, 79.0747], "villupuram": [11.9401, 79.4861],
    # Generic
    "bangalore": [12.9716, 77.5946], "delhi": [28.6139, 77.2090], "kolkata": [22.5726, 88.3639]
}

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================

def clean_city_name(city_raw):
    """Cleans up messy city names from CSVs (e.g., 'Gorakhpur, UP' -> 'gorakhpur')"""
    if pd.isna(city_raw):
        return None
    city = str(city_raw).lower().strip()
    # Remove common extra text like " district", " up", ","
    city = re.split(r'[,(\-]', city)[0].strip() # Take first part before comma or bracket
    city = city.replace(" district", "").replace(" city", "")
    return city

def normalize_columns(df):
    """Standardizes column names across different file formats"""
    # Map your variable column names to standard ones
    col_map = {
        'full_name': 'Name', 'name': 'Name', 'Name': 'Name',
        'city': 'City', 'City': 'City', 'location': 'City',
        'what\'s_your_current_designation?': 'Role', 'Designation': 'Role', 'current_designation': 'Role',
        'phone': 'Phone', 'phone_number': 'Phone', 'Contact no`': 'Phone',
        'do_you_have_an_experience_in_jewelry_industry?': 'Exp_Jewellery',
        'do_you_have_an_experience_in_jewelry_industry_?': 'Exp_Jewellery',
        'lead_status': 'Status'
    }
    
    # Rename columns if they exist in the file
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    
    # Ensure standard columns exist, fill with "Unknown" if missing
    required = ['Name', 'City', 'Role', 'Phone']
    for col in required:
        if col not in df.columns:
            df[col] = "Unknown"
            
    return df

# ==========================================
# 3. STREAMLIT APP LOGIC
# ==========================================

st.set_page_config(layout="wide", page_title="Recruitment Map")

# Sidebar for uploading
st.sidebar.header("📁 Upload Data")
uploaded_files = st.sidebar.file_uploader("Upload CSV/Excel files", accept_multiple_files=True, type=['csv', 'xlsx'])

st.title("🇮🇳 Recruitment War Room")
st.markdown("Cursor-interactive map. Hover for counts, Click to zoom, Click marker for details.")

if uploaded_files:
    all_data = []
    
    # PROGRESS BAR
    progress_bar = st.progress(0)
    
    for i, file in enumerate(uploaded_files):
        # Read file
        if file.name.endswith('.csv'):
            df_temp = pd.read_csv(file)
        else:
            df_temp = pd.read_excel(file)
            
        # Standardize Columns
        df_temp = normalize_columns(df_temp)
        
        # Add Source File Name (for tracking)
        df_temp['Source_File'] = file.name
        
        all_data.append(df_temp)
        progress_bar.progress((i + 1) / len(uploaded_files))

    # Combine all files into one Master Table
    master_df = pd.concat(all_data, ignore_index=True)
    
    # --- GEOCODING LOGIC ---
    # Create Lat/Lon columns based on the City Name
    latitudes = []
    longitudes = []
    
    for city in master_df['City']:
        clean_name = clean_city_name(city)
        coords = CITY_COORDINATES.get(clean_name)
        
        if coords:
            latitudes.append(coords[0])
            longitudes.append(coords[1])
        else:
            # Random jitter for unknowns so they don't crash, or skip
            # Putting unknowns in the middle of India (approx) to indicate "Location Required"
            latitudes.append(22.0) 
            longitudes.append(79.0)

    master_df['lat'] = latitudes
    master_df['lon'] = longitudes
    
    # Filter out the "Unknown" locations (optional) or keep them to show data quality issues
    map_data = master_df
    
    # --- METRICS ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Candidates", len(map_data))
    c2.metric("Files Merged", len(uploaded_files))
    c3.metric("Cities Covered", map_data['City'].nunique())
    # Simple logic to find top role
    top_role = map_data['Role'].value_counts().idxmax() if not map_data['Role'].empty else "N/A"
    c4.metric("Top Designation", str(top_role)[:15]+"...")

    # --- MAP CONSTRUCTION ---
    # Center on India
    m = folium.Map(location=[21.7679, 78.8718], zoom_start=5, tiles="CartoDB positron")
    
    # The Clustering Magic
    marker_cluster = MarkerCluster().add_to(m)

    for idx, row in map_data.iterrows():
        # Create the pop-up text
        html = f"""
        <div style="font-family:sans-serif; width:200px;">
            <h4>{row['Name']}</h4>
            <p><b>Role:</b> {row['Role']}</p>
            <p><b>Phone:</b> {row['Phone']}</p>
            <p><b>City:</b> {row['City']}</p>
            <p style="font-size:10px; color:gray;">Src: {row['Source_File']}</p>
        </div>
        """
        
        # Add marker to cluster
        folium.Marker(
            location=[row['lat'], row['lon']],
            popup=folium.Popup(html, max_width=250),
            tooltip=f"{row['City']}: {row['Name']}",
            icon=folium.Icon(color="blue", icon="user")
        ).add_to(marker_cluster)

    # Render Map
    st_folium(m, width=1400, height=700)
    
    # --- DATA TABLE ---
    st.subheader("Candidate Database (Merged)")
    st.dataframe(master_df, use_container_width=True)

else:
    st.info("👆 Please upload your candidate CSV files in the sidebar to generate the map.")
    
    # Helper to show what the app expects
    st.markdown("""
    **How to use:**
    1. Drag and drop your **Nagpur**, **Hyderabad**, **Gorakhpur** etc. CSV files into the sidebar.
    2. The map will auto-generate.
    3. **Zoom out** to see the numbered clusters (e.g., '50' on Maharashtra).
    4. **Click the clusters** to drill down into cities.
    5. **Click the blue markers** to see candidate details.
    """)