import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import plotly.express as px
import re
from datetime import datetime
import numpy as np

# ==========================================
# 1. ENTERPRISE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Recruitment Analytics Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. PROFESSIONAL CSS
# ==========================================
st.markdown("""
<style>
    /* GLOBAL FONTS */
    html, body, [class*="css"] {
        font-family: 'Segoe UI', 'Roboto', sans-serif;
        background-color: #F3F4F6;
    }
    
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
    }
    
    /* METRIC CARDS */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 8px !important;
        padding: 15px !important;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
    }
    
    div[data-testid="stMetricLabel"] {
        font-size: 14px !important;
        font-weight: 700 !important;
        color: #111827 !important; /* Dark Grey */
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 28px !important;
        font-weight: 800 !important;
        color: #111827 !important; /* Pure Black */
    }
    
    /* TABS */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
        padding-bottom: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 6px;
        color: #6B7280;
        font-weight: 600;
        font-size: 14px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        border: 1px solid #2563EB !important;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. BACKEND LOGIC
# ==========================================

CITY_COORDINATES = {
    # --- METROS ---
    "hyderabad": [17.3850, 78.4867], "bangalore": [12.9716, 77.5946],
    "chennai": [13.0827, 80.2707], "delhi": [28.6139, 77.2090],
    "mumbai": [19.0760, 72.8777], "kolkata": [22.5726, 88.3639],
    "pune": [18.5204, 73.8567], "ahmedabad": [23.0225, 72.5714],

    # --- ANDHRA PRADESH ---
    "vijayawada": [16.5062, 80.6480], "guntur": [16.3067, 80.4365],
    "visakhapatnam": [17.6868, 83.2185], "vizag": [17.6868, 83.2185],
    "rajahmundry": [17.0005, 81.8040], "kakinada": [16.9891, 82.2475],
    "nellore": [14.4426, 79.9865], "tirupati": [13.6288, 79.4192],
    "kurnool": [15.8281, 78.0373], "anantapur": [14.6819, 77.6006],
    "eluru": [16.7107, 81.0952], "ongole": [15.5057, 80.0499],
    "tenali": [16.2430, 80.6409], "srikakulam": [18.3008, 83.8968],
    "vizianagaram": [18.1067, 83.3956], "chittoor": [13.2172, 79.1003],
    "kadapa": [14.4673, 78.8242], "machilipatnam": [16.1685, 81.1303],
    "bhimavaram": [16.5449, 81.5212], "gudivada": [16.4410, 80.9926],
    "narsaraopet": [16.2305, 80.0543], "tadepalligudem": [16.8073, 81.5316],
    "nandyal": [15.4875, 78.4876], "proddatur": [14.7526, 78.5529],
    "hindupur": [13.8266, 77.4933], "guntakal": [15.1700, 77.3800],
    "dharmavaram": [14.4333, 77.7167], "nidadavole": [16.9038, 81.6669],
    "chirala": [15.8246, 80.3521], "kavali": [14.9132, 79.9928],
    "tanuku": [16.7587, 81.6787], "markapuram": [15.7441, 79.2687],

    # --- TELANGANA ---
    "warangal": [17.9689, 79.5941], "nizamabad": [18.6725, 78.0941],
    "khammam": [17.2473, 80.1514], "karimnagar": [18.4386, 79.1288],
    "mahabubnagar": [16.7488, 78.0035], "nalgonda": [17.0577, 79.2728],
    "adilabad": [19.6641, 78.5320], "siddipet": [18.1019, 78.8521],
    "mancherial": [18.8679, 79.4639], "jagtial": [18.7909, 78.9123],
    "medchal": [17.6297, 78.4814], "sangareddy": [17.6194, 78.0813],
    "bhainsa": [19.0964, 77.9657], "huzurabad": [18.2008, 79.4087],
    "secunderabad": [17.4399, 78.4983],
    
    # --- MAHARASHTRA & OTHERS ---
    "nagpur": [21.1458, 79.0882], "kamptee": [21.2235, 79.1943],
    "amravati": [20.9374, 77.7796], "aurangabad": [19.8762, 75.3433],
    "nashik": [19.9975, 73.7898], "solapur": [17.6599, 75.9064],
    "gorakhpur": [26.7606, 83.3732], "lucknow": [26.8467, 80.9462],
    "ajmer": [26.4499, 74.6399], "jaipur": [26.9124, 75.7873],
    "jodhpur": [26.2389, 73.0243], "kota": [25.2138, 75.8648],
    "kanpur": [26.4499, 80.3319], "varanasi": [25.3176, 82.9739],
    "bhopal": [23.2599, 77.4126], "indore": [22.7196, 75.8577],
    "surat": [21.1702, 72.8311], "coimbatore": [11.0168, 76.9558]
}

def clean_city_name(city_raw):
    if pd.isna(city_raw): return "Unknown"
    city = str(city_raw).lower().strip()
    
    # 1. Check if it's a STATE (and drop it)
    known_states = ["andhra pradesh", "telangana", "maharashtra", "karnataka", "tamil nadu", "uttar pradesh", "rajasthan", "gujarat", "bihar", "west bengal", "madhya pradesh"]
    if city in known_states:
        return "Unknown"
    
    # 2. Map Dirty Variations to Clean Names
    if 'hyd' in city: return 'Hyderabad'
    if 'secunderabad' in city: return 'Secunderabad'
    if 'vizag' in city or 'vishakhapatnam' in city: return 'Visakhapatnam'
    if 'vijay' in city or 'bezawada' in city: return 'Vijayawada'
    if 'gorkhpur' in city: return 'Gorakhpur'
    if 'bengaluru' in city: return 'Bangalore'
    if 'rajahmundry' in city or 'rajhamundry' in city: return 'Rajahmundry'
    if 'tirupati' in city or 'tirupathi' in city: return 'Tirupati'
    if 'ajmer' in city: return 'Ajmer'
    if 'kanpur' in city: return 'Kanpur'
    if 'noida' in city: return 'Noida'
    if 'delhi' in city: return 'Delhi'
    
    # 3. Filter Garbage
    if re.search(r'\d', city): return "Unknown" 
    if "job" in city or "enquiry" in city: return "Unknown"
    
    # 4. Standard Cleanup
    city = re.split(r'[,(\-/]', city)[0].strip()
    city = city.replace(" district", "").replace(" city", "").strip()
    
    return city.title()

def clean_role_name(role):
    if pd.isna(role): return "Unknown"
    role = str(role).lower().strip()
    
    if re.search(r'^\d', role): return "Unknown" 
    if 'km' in role: return "Unknown"
    if role in ['yes', 'no', 'male', 'female', 'unknown', 'other']: return "Unknown"
    if len(role) < 2: return "Unknown"
    
    # Map to Target List
    if "retail sales" in role: return "Retail Sales Officer"
    if "sales associate" in role: return "Sales Associate"
    if "sales consultant" in role: return "Sales Consultant"
    if "sales executive" in role or "sales exec" in role or "sr. sales" in role: return "Sales Executive"
    
    if "store manager" in role or "store mgr" in role: return "Store Manager"
    if "floor manager" in role: return "Floor Manager"
    if "branch manager" in role: return "Branch Manager"
    
    if "account" in role: return "Accountant"
    if "billing" in role or "cashier" in role: return "Billing/Cashier"
    if "data analyst" in role or "data entry" in role: return "Data Analyst"
    if "customer service" in role or "cse" in role or "support" in role: return "Customer Service"
    if "recruit" in role: return "Recruiter"
    if "telecaller" in role or "tele" in role: return "Telecaller"
    if "stone" in role or "assorter" in role: return "Stone Assorter"
    if "social media" in role: return "Social Media Executive"
    
    if "hr" in role or "human resource" in role: return "HR"
    if "marketing" in role: return "Marketing"
    if "quality" in role or "qc" in role: return "Quality Check"
    if "b2b" in role: return "B2B"
    if "b2c" in role: return "B2C"
    
    if "manager" in role: return "Store Manager" 
    if "sales" in role: return "Sales Executive" 

    return "Other"

def normalize_columns(df, filename=""):
    df.columns = [str(c).lower().strip() for c in df.columns]
    
    col_map = {
        'full_name': 'Name', 'name': 'Name', 'candidate name': 'Name', 'full name': 'Name',
        'city': 'City', 'location': 'City', 'preferred location': 'City', 'current city': 'City', 'region': 'City',
        'what\'s_your_current_designation?': 'Role', 'designation': 'Role', 
        'major job title': 'Role', 'job title': 'Role', 'role': 'Role',
        'whats your current designation?': 'Role', 'current_designation': 'Role',
        'phone': 'Phone', 'phone_number': 'Phone', 'contact': 'Phone',
        'contact no': 'Phone', 'contact no`': 'Phone', 'mobile': 'Phone',
        'lead_status': 'Status', 'status': 'Status',
        'created_time': 'Date', 'timestamp': 'Date', 'date': 'Date'
    }
    
    new_columns = {}
    for col in df.columns:
        if col in col_map:
            new_columns[col] = col_map[col]
    
    df = df.rename(columns=new_columns)
    
    # Merge Duplicate Columns
    if not df.columns.is_unique:
        df = df.replace(['Unknown', 'unknown'], np.nan)
        df = df.groupby(level=0, axis=1).first()
    
    if 'Status' not in df.columns: df['Status'] = 'New'
    if 'Date' not in df.columns: df['Date'] = pd.to_datetime('today').date()
    else: 
        try: df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
        except: df['Date'] = pd.to_datetime('today').date()

    # FORCE CREATE COLUMNS (Fixes KeyError)
    for col in ['Interview_Date', 'Salary', 'Remarks']:
        if col not in df.columns: df[col] = None
    
    for col in ['Name', 'City', 'Role', 'Phone']:
        if col not in df.columns: df[col] = "Unknown"

    is_role_missing = df['Role'].eq("Unknown").all() or df['Role'].isnull().all()
    if is_role_missing:
        inferred_role = "Unknown"
        fname_lower = str(filename).lower()
        if 'sales' in fname_lower: inferred_role = "Sales Executive"
        elif 'manager' in fname_lower: inferred_role = "Store Manager"
        elif 'hr' in fname_lower: inferred_role = "HR"
        elif 'accountant' in fname_lower: inferred_role = "Accountant"
        if inferred_role != "Unknown":
            df['Role'] = inferred_role
            
    df['Role'] = df['Role'].apply(clean_role_name)
    df['Status'] = df['Status'].fillna('New')
    return df

# ==========================================
# 4. SESSION STATE
# ==========================================
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame()

# ==========================================
# 5. APP INTERFACE
# ==========================================

st.title("Recruitment Analytics Platform")

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### Data Import")
    uploaded_files = st.file_uploader("Upload Source Files (CSV/XLSX)", accept_multiple_files=True)
    
    if uploaded_files and st.session_state.data.empty:
        all_data = []
        for file in uploaded_files:
            try:
                if file.name.endswith('.csv'): df_temp = pd.read_csv(file)
                else: df_temp = pd.read_excel(file)
                
                df_temp = normalize_columns(df_temp, filename=file.name)
                df_temp['Source'] = file.name
                all_data.append(df_temp)
            except Exception as e:
                st.error(f"Error reading {file.name}: {e}")
        
        if all_data:
            master_df = pd.concat(all_data, ignore_index=True)
            # DUPLICATES KEPT as requested
            
            # --- FINAL SAFETY CHECK ---
            for col in ['Interview_Date', 'Salary', 'Remarks', 'Status', 'Role', 'City', 'Phone']:
                if col not in master_df.columns:
                    master_df[col] = None

            master_df['Clean_City'] = master_df['City'].apply(clean_city_name)
            
            # MAP FIX: Lowercase lookup
            master_df['Lat'] = master_df['Clean_City'].map(lambda x: CITY_COORDINATES.get(str(x).lower(), [None, None])[0])
            master_df['Lon'] = master_df['Clean_City'].map(lambda x: CITY_COORDINATES.get(str(x).lower(), [None, None])[1])
            
            st.session_state.data = master_df
            st.success("Dataset successfully loaded.")

    st.markdown("---")
    st.markdown("### Data Export")
    if not st.session_state.data.empty:
        csv = st.session_state.data.to_csv(index=False).encode('utf-8')
        st.download_button("Download Master Dataset", csv, f"Recruitment_Master_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")

# --- MAIN DASHBOARD ---
if not st.session_state.data.empty:
    df = st.session_state.data
    
    # NAVIGATION
    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Outreach", "Pipeline Management", "Reporting"])

    # --- TAB 1: EXECUTIVE DASHBOARD ---
    with tab1:
        st.markdown("#### Executive Summary")
        
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Candidates", f"{len(df):,}")
        k2.metric("New (Current Month)", f"{len(df[df['Status'].isin(['New', 'CREATED'])]):,}")
        k3.metric("Interviews Scheduled", f"{len(df[df['Status'] == 'Interview Scheduled']):,}")
        k4.metric("Hired Candidates", f"{len(df[df['Status'] == 'Hired']):,}")
        
        st.markdown("---")
        
        # 2. CITY-WISE SCREENER (Replaces State Screener)
        st.markdown("### 📋 City-wise Role Matrix")
        screener_df = df.copy()
        screener_df['Role'] = screener_df['Role'].astype(str)
        
        # Filter Garbage for cleaner matrix
        screener_df = screener_df[~screener_df['Role'].isin(['Unknown', 'Other'])]
        screener_df = screener_df[screener_df['Clean_City'] != 'Unknown']
        
        # Pivot on Clean_City (Rows) vs Role (Cols)
        city_pivot = screener_df.pivot_table(index='Clean_City', columns='Role', aggfunc='size', fill_value=0)
        
        # Sort by Total
        city_pivot['Total'] = city_pivot.sum(axis=1)
        city_pivot = city_pivot.sort_values('Total', ascending=False).drop(columns='Total')
        
        # Format
        city_pivot.columns.name = None
        city_pivot.index.name = "City / Location"
        
        st.dataframe(city_pivot, use_container_width=True, height=500)
        
        st.markdown("---")
        
        # 3. MAP & CHARTS
        col_map, col_stats = st.columns([1.5, 1])
        with col_map:
            st.markdown("#### Geographic Distribution")
            map_df = df.dropna(subset=['Lat', 'Lon'])
            if not map_df.empty:
                m = folium.Map(location=[21.7679, 78.8718], zoom_start=5, tiles="CartoDB positron")
                marker_cluster = MarkerCluster().add_to(m)
                for idx, row in map_df.iterrows():
                    tooltip_text = f"{row['Name']} ({row['Role']})"
                    folium.Marker(
                        location=[row['Lat'], row['Lon']],
                        tooltip=tooltip_text,
                        icon=folium.Icon(color="green" if row['Status']=='Hired' else "blue", icon="user")
                    ).add_to(marker_cluster)
                st_folium(m, width=None, height=500)
            else:
                st.warning("Geographic data unavailable. Check city names.")

        with col_stats:
            st.markdown("#### Pipeline Funnel")
            status_counts = df['Status'].value_counts().reset_index()
            status_counts.columns = ['Stage', 'Count']
            fig_funnel = px.bar(status_counts, x='Stage', y='Count', text='Count', color_discrete_sequence=['#2563EB'])
            fig_funnel.update_layout(showlegend=False, height=220, margin=dict(t=0,b=0,l=0,r=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_funnel, use_container_width=True)
            
            st.markdown("#### Role Composition")
            role_df_clean = df[df['Role'] != 'Unknown']
            role_counts = role_df_clean['Role'].value_counts().head(5).reset_index()
            role_counts.columns = ['Role', 'Count']
            fig_pie = px.pie(role_counts, values='Count', names='Role', hole=0.6, color_discrete_sequence=px.colors.sequential.Blues_r)
            fig_pie.update_layout(height=220, margin=dict(t=0,b=0,l=0,r=0), showlegend=False)
            st.plotly_chart(fig_pie, use_container_width=True)

    # --- TAB 2: OUTREACH ---
    with tab2:
        st.markdown("#### Candidate Outreach")
        
        all_stats = df['Status'].unique().tolist()
        def_stats = ['New', 'CREATED']
        valid_defs = [x for x in def_stats if x in all_stats]
        if not valid_defs and all_stats: valid_defs = [all_stats[0]]
        
        status_filter = st.multiselect("Filter Status", all_stats, default=valid_defs)
        filtered_df = df[df['Status'].isin(status_filter)]
        
        edited_df = st.data_editor(
            filtered_df,
            column_config={
                "Status": st.column_config.SelectboxColumn("Status", options=["New", "Interested", "Not Interested", "Call Back Later", "Wrong Number"], required=True),
                "Remarks": st.column_config.TextColumn("Notes", width="large")
            },
            disabled=["Name", "Phone", "City", "Role"],
            hide_index=True,
            key="telecaller",
            use_container_width=True
        )
        
        if st.button("Save Changes", type="primary"):
            st.session_state.data.update(edited_df)
            st.success("Records updated successfully.")
            st.rerun()

    # --- TAB 3: PIPELINE ---
    with tab3:
        st.markdown("#### Pipeline Management")
        
        hr_opts = df['Status'].unique().tolist()
        hr_defs = ['Interested', 'Interview Scheduled']
        valid_hr = [x for x in hr_defs if x in hr_opts]
        
        hr_filter = st.multiselect("Filter Stage", hr_opts, default=valid_hr)
        hr_df = df[df['Status'].isin(hr_filter)]
        
        hr_edited = st.data_editor(
            hr_df,
            column_config={
                "Status": st.column_config.SelectboxColumn("Stage", options=["Interested", "Interview Scheduled", "Interviewed - Showed Up", "Interviewed - No Show", "Hired", "Rejected"]),
                "Interview_Date": st.column_config.DateColumn("Interview Date"),
                "Salary": st.column_config.NumberColumn("Offer", format="₹%d"),
                "Remarks": st.column_config.TextColumn("Notes")
            },
            disabled=["Name", "Phone", "City", "Role"],
            hide_index=True,
            key="hr",
            use_container_width=True
        )
        
        if st.button("Update Pipeline", type="primary"):
            st.session_state.data.update(hr_edited)
            st.success("Pipeline updated successfully.")
            st.rerun()

    # --- TAB 4: REPORTING ---
    with tab4:
        st.markdown("#### Automated Reports")
        
        r1, r2 = st.columns(2)
        with r1:
            st.markdown("**Interview Schedule**")
            int_df = df[df['Status'] == 'Interview Scheduled'][['Name', 'Phone', 'Role', 'City', 'Interview_Date']]
            st.dataframe(int_df, hide_index=True, use_container_width=True)
            st.download_button("Download CSV", int_df.to_csv(index=False).encode('utf-8'), "Interviews.csv", "text/csv")
            
        with r2:
            st.markdown("**Hired Candidates**")
            hired_df = df[df['Status'] == 'Hired'][['Name', 'Phone', 'Role', 'City', 'Salary', 'Date']]
            st.dataframe(hired_df, hide_index=True, use_container_width=True)
            st.download_button("Download CSV", hired_df.to_csv(index=False).encode('utf-8'), "Hired.csv", "text/csv")

else:
    st.info("Please import data files using the sidebar to initialize the dashboard.")