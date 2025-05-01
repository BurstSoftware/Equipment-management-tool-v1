import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import os

# Initialize session state for data persistence
if 'equipment_df' not in st.session_state:
    # Sample initial data
    st.session_state.equipment_df = pd.DataFrame({
        'ID': [1, 2, 3],
        'Name': ['Excavator', 'Bulldozer', 'Crane'],
        'Status': ['In Use', 'Maintenance', 'Available'],
        'Last_Maintenance': [datetime(2025, 3, 1), datetime(2025, 2, 15), datetime(2025, 4, 10)],
        'Next_Maintenance': [datetime(2025, 6, 1), datetime(2025, 5, 15), datetime(2025, 7, 10)],
        'Usage_Hours': [1200, 800, 500],
        'Rental_Cost': [5000, 3000, 7000],
        'Depreciation': [10000, 8000, 15000],
        'Project': ['Highway 101', 'Bridge Repair', 'None'],
        'Crew': ['Crew A', 'Crew B', 'None']
    })
if 'alerts' not in st.session_state:
    st.session_state.alerts = []

# Function to save data to CSV
def save_data():
    st.session_state.equipment_df.to_csv('equipment_data.csv', index=False)

# Load data if exists
if os.path.exists('equipment_data.csv'):
    st.session_state.equipment_df = pd.read_csv('equipment_data.csv')
    st.session_state.equipment_df['Last_Maintenance'] = pd.to_datetime(st.session_state.equipment_df['Last_Maintenance'])
    st.session_state.equipment_df['Next_Maintenance'] = pd.to_datetime(st.session_state.equipment_df['Next_Maintenance'])

# Maintenance alert function
def check_maintenance():
    today = datetime.now()
    for idx, row in st.session_state.equipment_df.iterrows():
        if row['Next_Maintenance'] <= today:
            st.session_state.alerts.append(f"Maintenance due for {row['Name']} (ID: {row['ID']})")

# Scheduler for maintenance checks (runs every day)
scheduler = BackgroundScheduler()
scheduler.add_job(check_maintenance, 'interval', days=1)
scheduler.start()

# Streamlit app layout
st.title("Construction Equipment Management Tool")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Inventory", "Add Equipment", "Maintenance Alerts", "Cost Tracking", "Dashboards"])

# Inventory Page
if page == "Inventory":
    st.header("Equipment Inventory")
    st.dataframe(st.session_state.equipment_df)
    
    # Filter by status
    status_filter = st.selectbox("Filter by Status", ["All"] + list(st.session_state.equipment_df['Status'].unique()))
    if status_filter != "All":
        filtered_df = st.session_state.equipment_df[st.session_state.equipment_df['Status'] == status_filter]
        st.dataframe(filtered_df)
    
    # Update status or allocation
    st.subheader("Update Equipment")
    equip_id = st.number_input("Equipment ID", min_value=1, step=1)
    new_status = st.selectbox("New Status", ["In Use", "Maintenance", "Available"])
    new_project = st.text_input("New Project")
    new_crew = st.text_input("New Crew")
    if st.button("Update"):
        if equip_id in st.session_state.equipment_df['ID'].values:
            st.session_state.equipment_df.loc[st.session_state.equipment_df['ID'] == equip_id, 'Status'] = new_status
            st.session_state.equipment_df.loc[st.session_state.equipment_df['ID'] == equip_id, 'Project'] = new_project
            st.session_state.equipment_df.loc[st.session_state.equipment_df['ID'] == equip_id, 'Crew'] = new_crew
            save_data()
            st.success("Equipment updated!")
        else:
            st.error("Equipment ID not found.")

# Add Equipment Page
elif page == "Add Equipment":
    st.header("Add New Equipment")
    with st.form("add_equipment_form"):
        equip_id = st.number_input("ID", min_value=1, step=1)
        name = st.text_input("Equipment Name")
        status = st.selectbox("Status", ["In Use", "Maintenance", "Available"])
        last_maintenance = st.date_input("Last Maintenance Date")
        usage_hours = st.number_input("Usage Hours", min_value=0)
        rental_cost = st.number_input("Rental Cost", min_value=0)
        depreciation = st.number_input("Depreciation", min_value=0)
        project = st.text_input("Project")
        crew = st.text_input("Crew")
        submitted = st.form_submit_button("Add Equipment")
        
        if submitted:
            if equip_id not in st.session_state.equipment_df['ID'].values:
                new_row = {
                    'ID': equip_id,
                    'Name': name,
                    'Status': status,
                    'Last_Maintenance': last_maintenance,
                    'Next_Maintenance': last_maintenance + timedelta(days=90),  # Assume 3-month maintenance cycle
                    'Usage_Hours': usage_hours,
                    'Rental_Cost': rental_cost,
                    'Depreciation': depreciation,
                    'Project': project,
                    'Crew': crew
                }
                st.session_state.equipment_df = pd.concat([st.session_state.equipment_df, pd.DataFrame([new_row])], ignore_index=True)
                save_data()
                st.success("Equipment added!")
            else:
                st.error("Equipment ID already exists.")

# Maintenance Alerts Page
elif page == "Maintenance Alerts":
    st.header("Maintenance Alerts")
    if st.session_state.alerts:
        for alert in st.session_state.alerts:
            st.warning(alert)
    else:
        st.info("No maintenance alerts at this time.")
    
    # Manually trigger maintenance check
    if st.button("Check Maintenance Now"):
        check_maintenance()
        st.rerun()

# Cost Tracking Page
elif page == "Cost Tracking":
    st.header("Cost Tracking")
    total_rental = st.session_state.equipment_df['Rental_Cost'].sum()
    total_depreciation = st.session_state.equipment_df['Depreciation'].sum()
    st.metric("Total Rental Costs", f"${total_rental:,.2f}")
    st.metric("Total Depreciation", f"${total_depreciation:,.2f}")
    
    # Breakdown by equipment
    st.subheader("Cost Breakdown by Equipment")
    cost_df = st.session_state.equipment_df[['Name', 'Rental_Cost', 'Depreciation']]
    st.dataframe(cost_df)
    
    # Plot cost breakdown
    fig = px.bar(cost_df, x='Name', y=['Rental_Cost', 'Depreciation'], title="Cost Breakdown by Equipment")
    st.plotly_chart(fig)

# Dashboards Page
elif page == "Dashboards":
    st.header("Equipment Utilization Dashboards")
    
    # Equipment Status Pie Chart
    status_counts = st.session_state.equipment_df['Status'].value_counts()
    fig1 = px.pie(values=status_counts.values, names=status_counts.index, title="Equipment Status Distribution")
    st.plotly_chart(fig1)
    
    # Usage Hours Bar Chart
    fig2 = px.bar(st.session_state.equipment_df, x='Name', y='Usage_Hours', title="Usage Hours by Equipment")
    st.plotly_chart(fig2)
    
    # Project Allocation
    project_counts = st.session_state.equipment_df['Project'].value_counts()
    fig3 = px.bar(x=project_counts.index, y=project_counts.values, title="Equipment Allocation by Project")
    st.plotly_chart(fig3)

# Footer
st.sidebar.markdown("---")
st.sidebar.write("Built with Streamlit, Pandas, Plotly, and APScheduler")
