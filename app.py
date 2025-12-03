import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import plotly.express as px
import re

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Recruitment Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Structure/Fonts only (No hardcoded colors to avoid theme conflicts)
st.markdown("""
<style>
    /* Professional Font Stack */
    html, body, [class*="css"] {
        font-family: 'Segoe UI', 'Helvetica Neue', 'Arial', sans-serif;
    }
    
    /* Clean up top padding */
    .block-container {
        padding-top: 1.5rem;
    }
    
    /* KPI Card Borders (Theme agnostic) */
    div[data-testid="stMetric"] {
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 15px;
        border-radius: 8px;
        background-color: rgba(255, 255, 255, 0.05); /* Subtle transparency */
    }
    
    /* Hide default Streamlit clutter */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. BACKEND LOGIC & DATA
# ==========================================

CITY_COORDINATES = {
    # Key Hubs
    "nagpur": [21.1458, 79.0882], "mumbai": [19.0760, 72.8777], "pune": [18.5204, 73.8567],
    "hyderabad": [17.3850, 78.4867], "vijayawada": [16.5062, 80.6480], "gorakhpur": [26.7606, 83.3732],
    "ajmer": [26.4499, 74.6399], "chennai": [13.0827, 80.2707], "bangalore": [12.9716, 77.5946],
    "delhi": [28.6139, 77.2090], "kolkata": [22.5726, 88.3639], "lucknow": [26.8467, 80.9462],
    # Secondary Hubs
    "kamptee": [21.2235, 79.1943], "amravati": [20.9374, 77.7796], "aurangabad": [19.8762, 75.3433],
    "nashik": [19.9975, 73.7898], "guntur": [16.3067, 80.4365], "visakhapatnam": [17.6868, 83.2185],
    "rajahmundry": [17.0005, 81.8040], "kakinada": [16.9891, 82.2475], "nellore": [14.4426, 79.9865],
    "kanpur": [26.4499, 80.3319], "varanasi": [25.3176, 82.9739], "jaipur": [26.9124, 75.7873],
    "jodhpur": [26.2389, 73.0243], "salem": [11.6643, 78.1460], "coimbatore": [11.0168, 76.9558],
    "tiruvannamalai": [12.2253, 79.0747], "vellore": [12.9165, 79.1325], "akola": [20.7002, 77.0082],
    "noida": [28.5355, 77.3910], "agra": [27.1767, 78.0081], "meerut": [28.9845, 77.7064],
    "eluru": [16.7107, 81.0952], "ongole": [15.5057, 80.0499], "tenali": [16.2430, 80.6409],
    "warangal": [17.9689, 79.5941], "kurnool": [15.8281, 78.0373], "nizamabad": [18.6725, 78.0941],
    "ahmedabad": [23.0225, 72.5714], "surat": [21.1702, 72.8311], "indore": [22.7196, 75.8577]
}

def clean_city_name(city_raw):
    """Normalize city names."""
    if pd.isna(city_raw): return None
    city = str(city_raw).lower().strip()
    city = re.split(r'[,(\-]', city)[0].strip()
    city = city.replace(" district", "").replace(" city", "").strip()
    return city

def normalize_columns(df):
    """Maps various CSV headers to a standard enterprise format."""
    col_map = {
        'full_name': 'Name', 'name': 'Name', 'Name': 'Name', 'Candidate Name': 'Name',
        'city': 'City', 'City': 'City', 'location': 'City',
        'what\'s_your_current_designation?': 'Role', 'Designation': 'Role', 'current_designation': 'Role',
        'phone': 'Phone', 'phone_number': 'Phone', 'Contact no`': 'Phone',
        'do_you_have_an_experience_in_jewelry_industry?': 'Experience',
        'how_many_years_of_experience_do_you_have_in_jewelry_industry?': 'Years_Exp',
        'lead_status': 'Status'
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    for col in ['Name', 'City', 'Role', 'Phone']:
        if col not in df.columns: df[col] = "Unknown"
    return df

# ==========================================
# 3. INTERFACE LOGIC
# ==========================================

st.title("Recruitment Analytics")
st.markdown("### Executive Dashboard")

# --- SIDEBAR CONFIGURATION ---
st.sidebar.markdown("### Data Configuration")
uploaded_files = st.sidebar.file_uploader("Import Source Data (CSV/XLSX)", accept_multiple_files=True)

if uploaded_files:
    # 1. LOAD & NORMALIZE DATA
    all_data = []
    for file in uploaded_files:
        try:
            if file.name.endswith('.csv'): df_temp = pd.read_csv(file)
            else: df_temp = pd.read_excel(file)
            df_temp = normalize_columns(df_temp)
            df_temp['Source'] = file.name
            all_data.append(df_temp)
        except Exception:
            pass

    master_df = pd.concat(all_data, ignore_index=True)
    
    # 2. GEOCODING
    master_df['Clean_City'] = master_df['City'].apply(clean_city_name)
    master_df['Lat'] = master_df['Clean_City'].map(lambda x: CITY_COORDINATES.get(x, [None, None])[0])
    master_df['Lon'] = master_df['Clean_City'].map(lambda x: CITY_COORDINATES.get(x, [None, None])[1])
    
    # 3. FILTERING
    map_df = master_df.dropna(subset=['Lat', 'Lon'])
    city_counts = map_df['Clean_City'].value_counts()
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Geography Filter")
    
    view_selection = st.sidebar.selectbox(
        "Select Region",
        ["All Regions (Overview)"] + [f"{city.title()}" for city in city_counts.index]
    )

    # Determine Active Data based on selection
    if "All Regions" in view_selection:
        active_df = map_df
        view_mode = "MAP"
    else:
        target_city = view_selection.lower()
        active_df = map_df[map_df['Clean_City'] == target_city]
        view_mode = "LIST"

    # --- KPI SECTION (Adaptive) ---
    kpi_container = st.container()
    with kpi_container:
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Candidates", f"{len(active_df):,}")
        k2.metric("Locations", active_df['Clean_City'].nunique())
        top_role = active_df['Role'].mode()[0] if not active_df['Role'].empty else "N/A"
        k3.metric("Primary Role", str(top_role)[:20])
        k4.metric("Sources", active_df['Source'].nunique())

    st.markdown("---")

    # --- MAIN VISUALIZATION ---
    
    if view_mode == "MAP":
        st.subheader("Geographic Distribution")
        
        # We use a neutral map tile that works for both Dark/Light modes
        # "CartoDB positron" is light grey, which is standard for Data Dashboards
        m = folium.Map(location=[21.7679, 78.8718], zoom_start=5, tiles="CartoDB positron")
        marker_cluster = MarkerCluster().add_to(m)

        for idx, row in active_df.iterrows():
            # Popups need inline styling to look good in both modes
            # We force black text inside the white popup bubble for readability
            html = f"""
            <div style="font-family:sans-serif; color: #333; font-size:12px;">
                <strong style="color: #004B87; font-size:14px;">{row['Name']}</strong>
                <hr style="margin:5px 0; border:0; border-top:1px solid #ddd;">
                <div><b>Role:</b> {row['Role']}</div>
                <div><b>City:</b> {row['City'].title()}</div>
                <div><b>Ref:</b> {row['Source']}</div>
            </div>
            """
            folium.Marker(
                location=[row['Lat'], row['Lon']],
                popup=folium.Popup(html, max_width=200),
                tooltip=f"{row['City']} - {row['Name']}",
                icon=folium.Icon(color="blue", icon="user", prefix="fa")
            ).add_to(marker_cluster)

        st_folium(m, width=1400, height=600)

    else:
        st.subheader(f"Regional Analytics: {view_selection}")
        
        col_charts, col_data = st.columns([1, 2])
        
        with col_charts:
            st.markdown("##### Role Breakdown")
            role_data = active_df['Role'].value_counts().reset_index()
            role_data.columns = ['Role', 'Count']
            
            # Use Streamlit native theme for chart colors
            fig = px.pie(role_data.head(8), values='Count', names='Role', hole=0.5)
            fig.update_traces(textinfo='percent+label')
            fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=300)
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("##### Export")
            csv = active_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"Download CSV",
                data=csv,
                file_name=f"{view_selection}_data.csv",
                mime='text/csv',
                use_container_width=True
            )

        with col_data:
            st.markdown("##### Candidate Roster")
            st.dataframe(
                active_df[['Name', 'Role', 'Phone', 'City', 'Source']],
                use_container_width=True,
                height=500,
                hide_index=True,
                column_config={
                    "Name": st.column_config.TextColumn("Candidate Name", width="medium"),
                    "Role": st.column_config.TextColumn("Designation", width="medium"),
                    "Phone": st.column_config.TextColumn("Contact", width="small"),
                    "City": st.column_config.TextColumn("Location", width="small"),
                    "Source": st.column_config.TextColumn("Source File", width="medium"),
                }
            )

else:
    # Empty State
    st.info("Please upload your candidate CSV or Excel files in the sidebar to begin.")