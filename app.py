import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
import json
from datetime import datetime
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus.flowables import HRFlowable

# Set page config
st.set_page_config(
    page_title="Vehicle Management System",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
def init_db():
    conn = sqlite3.connect('vehicles.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS vehicles (
            p_key INTEGER PRIMARY KEY AUTOINCREMENT,
            VEH_ID TEXT UNIQUE,
            REG_NO TEXT,
            VEHICLE_TYPE TEXT,
            MAKE TEXT,
            MODEL TEXT,
            YEAR INTEGER,
            OWNER TEXT,
            USED_FOR TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Constants
VEHICLE_TYPES = [
    "Chain Arm Roll", "Compactor", "Dumper (20m3)", "Dumper (5m3)",
    "Front End Loader", "Loader Rickshaw", "Mechanical Sweeper",
    "Mini Tipper", "Tractor Loader", "Tractor Trolley",
    "Water Bowzer", "Gulli Sucker", "Drain Cleaner"
]

USAGE_CATEGORIES = [
    "Container Base Collection", "Secondary Waste Collection",
    "Bulk Waste Collection", "Door to Door (Residential)",
    "Mechanical Sweeping", "Door to Door (Commercial)",
    "Mechanical Washing", "Dumpsite Management"
]

# Vehicle type to ID prefix mapping
VEH_ID_PREFIXES = {
    "Chain Arm Roll": "AR",
    "Compactor": "C",
    "Dumper (20m3)": "D",
    "Dumper (5m3)": "D",
    "Front End Loader": "FL",
    "Loader Rickshaw": "LR",
    "Mechanical Sweeper": "MS",
    "Mini Tipper": "MT",
    "Tractor Loader": "TL",
    "Tractor Trolley": "TT",
    "Water Bowzer": "MW",
    "Gulli Sucker": "GS",
    "Drain Cleaner": "DC"
}

# Auto-assignment rules for usage categories
USAGE_RULES = {
    "Chain Arm Roll": "Container Base Collection",
    "Compactor": "Container Base Collection",
    "Dumper (20m3)": "Secondary Waste Collection",
    "Dumper (5m3)": "Secondary Waste Collection",
    "Front End Loader": "Secondary Waste Collection",
    "Loader Rickshaw": "Door to Door (Residential)",
    "Mechanical Sweeper": "Mechanical Sweeping",
    "Mini Tipper": "Door to Door (Commercial)",
    "Tractor Loader": "Bulk Waste Collection",
    "Tractor Trolley": "Bulk Waste Collection",
    "Water Bowzer": "Mechanical Washing",
    "Gulli Sucker": "Dumpsite Management",
    "Drain Cleaner": ""
}

def main():
    init_db()
    
    st.title("🚗 Vehicle Management System")
    st.subheader("Care Services Consortium, Faisalabad")
    
    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Navigation",
        ["Home", "Import Data", "Add/Edit Vehicle", "Generate Vehicles", "Reports"]
    )
    
    if page == "Home":
        show_home_page()
    elif page == "Import Data":
        show_import_page()
    elif page == "Add/Edit Vehicle":
        show_vehicle_form()
    elif page == "Generate Vehicles":
        show_generation_form()
    elif page == "Reports":
        show_reports_page()

def show_home_page():
    # Admin Panel in a smaller expander
    with st.expander("⚙️ Admin Panel", expanded=False):
        if st.button("Reset Database"):
            if st.session_state.get('confirm_reset', False):
                reset_database()
                st.success("Database has been reset!")
                st.session_state.confirm_reset = False
            else:
                st.session_state.confirm_reset = True
                st.warning("Click again to confirm database reset!")
    
    # Compact header with statistics
    col1, col2 = st.columns([1, 3])
    with col1:
        total_vehicles = get_total_vehicles()
        st.metric("Total Vehicles", total_vehicles)
    
    # Search functionality
    st.subheader("🔍 Search Vehicles")
    search_col1, search_col2 = st.columns([3, 1])
    with search_col1:
        search_term = st.text_input("Search by Vehicle ID, Registration, Type, Make, Model, or Owner", placeholder="Enter search term...")
    with search_col2:
        search_field = st.selectbox("Search in", ["All Fields", "VEH_ID", "REG_NO", "VEHICLE_TYPE", "MAKE", "MODEL", "OWNER", "USED_FOR"])
    
    # Vehicle Table with Edit/Delete buttons
    st.subheader("🚗 All Vehicles")
    show_vehicle_table(search_term, search_field)

def show_import_page():
    st.subheader("📥 Import Vehicle Data")
    uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=['csv', 'xlsx'])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.write("Preview of uploaded data:")
            st.dataframe(df.head())
            
            if st.button("Import Data"):
                import_vehicles(df)
                st.success("Data imported successfully!")
        except Exception as e:
            st.error(f"Error importing data: {str(e)}")

def show_vehicle_form():
    st.subheader("🚗 Add/Edit Vehicle")
    
    # Check if we're editing an existing vehicle
    editing = False
    vehicle_data = {}
    
    if st.session_state.get('edit_vehicle'):
        veh_id_to_edit = st.session_state.edit_vehicle
        conn = sqlite3.connect('vehicles.db')
        df = pd.read_sql_query("SELECT * FROM vehicles WHERE VEH_ID = ?", conn, params=(veh_id_to_edit,))
        conn.close()
        
        if not df.empty:
            vehicle_data = df.iloc[0].to_dict()
            editing = True
            st.info(f"Editing vehicle: {veh_id_to_edit}")
    
    # Form for adding/editing vehicle
    with st.form("vehicle_form"):
        veh_id = st.text_input("Vehicle ID", value=vehicle_data.get('VEH_ID', ''), disabled=editing)
        reg_no = st.text_input("Registration Number", value=vehicle_data.get('REG_NO', ''))
        vehicle_type = st.selectbox("Vehicle Type", VEHICLE_TYPES, index=VEHICLE_TYPES.index(vehicle_data.get('VEHICLE_TYPE', VEHICLE_TYPES[0])) if 'VEHICLE_TYPE' in vehicle_data else 0)
        make = st.text_input("Make", value=vehicle_data.get('MAKE', ''))
        model = st.text_input("Model", value=vehicle_data.get('MODEL', ''))
        year = st.number_input("Year", min_value=1900, max_value=2100, value=int(vehicle_data.get('YEAR', 2020)))
        owner = st.text_input("Owner", value=vehicle_data.get('OWNER', ''))
        used_for = st.selectbox("Usage Category", USAGE_CATEGORIES, index=USAGE_CATEGORIES.index(vehicle_data.get('USED_FOR', USAGE_CATEGORIES[0])) if 'USED_FOR' in vehicle_data else 0)
        
        submitted = st.form_submit_button("Submit")
        if submitted:
            save_vehicle(veh_id, reg_no, vehicle_type, make, model, year, owner, used_for)
            st.success("Vehicle information saved!")
            
            # Clear the editing state
            if editing:
                st.session_state.edit_vehicle = None
                st.experimental_rerun()

def show_generation_form():
    st.subheader("🔄 Generate Vehicles")
    
    with st.form("generation_form"):
        st.write("Enter the number of vehicles to generate for each type:")
        vehicle_counts = {}
        
        for v_type in VEHICLE_TYPES:
            vehicle_counts[v_type] = st.number_input(f"{v_type}", min_value=0, value=0)
        
        if st.form_submit_button("Generate Vehicles"):
            generate_vehicles(vehicle_counts)
            st.success("Vehicles generated successfully!")

def show_reports_page():
    st.subheader("📊 Reports")
    
    report_type = st.radio("Select Report Type", ["By Vehicle Type", "By Usage"])
    
    if report_type == "By Vehicle Type":
        vehicle_type = st.selectbox("Select Vehicle Type", VEHICLE_TYPES)
        if st.button("Generate Report"):
            generate_vehicle_type_report(vehicle_type)
    else:
        usage = st.selectbox("Select Usage Category", USAGE_CATEGORIES)
        if st.button("Generate Report"):
            generate_usage_report(usage)

# Helper functions (to be implemented)
def get_total_vehicles():
    conn = sqlite3.connect('vehicles.db')
    c = conn.cursor()
    count = c.execute('SELECT COUNT(*) FROM vehicles').fetchone()[0]
    conn.close()
    return count

def show_vehicle_table(search_term="", search_field="All Fields"):
    conn = sqlite3.connect('vehicles.db')
    
    # Build the query based on search parameters
    if search_term and search_field != "All Fields":
        query = f"SELECT * FROM vehicles WHERE {search_field} LIKE ?"
        df = pd.read_sql_query(query, conn, params=(f"%{search_term}%",))
    elif search_term:
        # Search in all text fields
        query = """
        SELECT * FROM vehicles 
        WHERE VEH_ID LIKE ? 
        OR REG_NO LIKE ? 
        OR VEHICLE_TYPE LIKE ? 
        OR MAKE LIKE ? 
        OR MODEL LIKE ? 
        OR OWNER LIKE ? 
        OR USED_FOR LIKE ?
        """
        params = tuple([f"%{search_term}%"] * 7)
        df = pd.read_sql_query(query, conn, params=params)
    else:
        # No search, get all vehicles
        df = pd.read_sql_query("SELECT * FROM vehicles", conn)
    
    conn.close()
    
    if not df.empty:
        # Create columns for buttons
        if 'edit_vehicle' not in st.session_state:
            st.session_state.edit_vehicle = None
        
        # Display the dataframe
        st.dataframe(df)
        
        # Add Edit/Delete functionality below the table
        col1, col2 = st.columns(2)
        
        with col1:
            vehicle_to_edit = st.selectbox(
                "Select Vehicle to Edit", 
                df['VEH_ID'].tolist(),
                index=None,
                placeholder="Choose a vehicle..."
            )
            if st.button("Edit Selected Vehicle"):
                if vehicle_to_edit:
                    st.session_state.edit_vehicle = vehicle_to_edit
                    st.info(f"Navigate to the 'Add/Edit Vehicle' page to edit {vehicle_to_edit}")
        
        with col2:
            vehicle_to_delete = st.selectbox(
                "Select Vehicle to Delete", 
                df['VEH_ID'].tolist(),
                index=None,
                placeholder="Choose a vehicle..."
            )
            if st.button("Delete Selected Vehicle"):
                if vehicle_to_delete:
                    delete_vehicle(vehicle_to_delete)
                    st.success(f"Vehicle {vehicle_to_delete} deleted successfully!")
                    st.experimental_rerun()
    else:
        st.info("No vehicles found matching your search criteria")

def save_vehicle(veh_id, reg_no, vehicle_type, make, model, year, owner, used_for):
    conn = sqlite3.connect('vehicles.db')
    c = conn.cursor()
    
    try:
        c.execute('''
            INSERT OR REPLACE INTO vehicles 
            (VEH_ID, REG_NO, VEHICLE_TYPE, MAKE, MODEL, YEAR, OWNER, USED_FOR)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (veh_id, reg_no, vehicle_type, make, model, year, owner, used_for))
        conn.commit()
    except Exception as e:
        st.error(f"Error saving vehicle: {str(e)}")
    finally:
        conn.close()

def import_vehicles(df):
    conn = sqlite3.connect('vehicles.db')
    required_columns = ['VEH_ID', 'REG_NO', 'VEHICLE_TYPE', 'MAKE', 'MODEL', 'YEAR', 'OWNER', 'USED_FOR']
    
    if not all(col in df.columns for col in required_columns):
        st.error("Missing required columns in the uploaded file")
        return
    
    df.to_sql('vehicles', conn, if_exists='append', index=False)
    conn.close()

def reset_database():
    conn = sqlite3.connect('vehicles.db')
    c = conn.cursor()
    c.execute('DROP TABLE IF EXISTS vehicles')
    init_db()
    conn.close()

def generate_vehicle_type_report(vehicle_type):
    # Get data for the report
    conn = sqlite3.connect('vehicles.db')
    df = pd.read_sql_query(
        f"SELECT * FROM vehicles WHERE vehicle_type = ?", 
        conn, 
        params=(vehicle_type,)
    )
    conn.close()
    
    if df.empty:
        st.warning(f"No vehicles found of type: {vehicle_type}")
        return
    
    # Display data in Streamlit
    st.dataframe(df)
    
    # Generate PDF report using the new module
    from pdf_reports_final import generate_vehicle_report
    pdf_file = generate_vehicle_report(df, vehicle_type, "vehicle_type")
    
    # Provide download button
    with open(pdf_file, "rb") as f:
        st.download_button(
            label="Download PDF Report",
            data=f,
            file_name=pdf_file,
            mime="application/pdf"
        )

def generate_usage_report(usage):
    # Get data for the report
    conn = sqlite3.connect('vehicles.db')
    df = pd.read_sql_query(
        f"SELECT * FROM vehicles WHERE USED_FOR = ?", 
        conn, 
        params=(usage,)
    )
    conn.close()
    
    if df.empty:
        st.warning(f"No vehicles found for usage: {usage}")
        return
    
    # Display data in Streamlit
    st.dataframe(df)
    
    # Generate PDF report using the new module
    from pdf_reports_final import generate_vehicle_report
    pdf_file = generate_vehicle_report(df, usage, "usage")
    
    # Provide download button
    with open(pdf_file, "rb") as f:
        st.download_button(
            label="Download PDF Report",
            data=f,
            file_name=pdf_file,
            mime="application/pdf"
        )

def delete_vehicle(veh_id):
    conn = sqlite3.connect('vehicles.db')
    c = conn.cursor()
    
    try:
        c.execute('DELETE FROM vehicles WHERE VEH_ID = ?', (veh_id,))
        conn.commit()
    except Exception as e:
        st.error(f"Error deleting vehicle: {str(e)}")
    finally:
        conn.close()

def generate_vehicles(vehicle_counts):
    conn = sqlite3.connect('vehicles.db')
    c = conn.cursor()
    
    for vehicle_type, count in vehicle_counts.items():
        for _ in range(count):
            veh_id = f"{VEH_ID_PREFIXES[vehicle_type]}{len([row for row in c.execute('SELECT * FROM vehicles WHERE VEHICLE_TYPE = ?', (vehicle_type,)).fetchall()]) + 1}"
            reg_no = f"{vehicle_type} REG {len([row for row in c.execute('SELECT * FROM vehicles WHERE VEHICLE_TYPE = ?', (vehicle_type,)).fetchall()]) + 1}"
            make = "Default Make"
            model = "Default Model"
            year = 2020
            owner = "Default Owner"
            used_for = USAGE_RULES[vehicle_type]
            
            c.execute('''
                INSERT INTO vehicles 
                (VEH_ID, REG_NO, VEHICLE_TYPE, MAKE, MODEL, YEAR, OWNER, USED_FOR)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (veh_id, reg_no, vehicle_type, make, model, year, owner, used_for))
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()
