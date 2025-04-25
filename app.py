# app.py - Streamlit Dashboard for Crime Reporting DB using SQLite3

import streamlit as st
import pandas as pd
import sqlite3
import time

# --- Streamlit Page Config ---
st.set_page_config(page_title="Crime Dashboard", layout="wide")
st.title("🚨 Buffalo Crime Reporting Dashboard")

# --- Database Connection ---
def get_connection():
    return sqlite3.connect('crime_reporting_with_indexes.db')

def get_filter_options():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT incident_type_primary FROM incident ORDER BY incident_type_primary")
    crime_types = [row[0] for row in cur.fetchall() if row[0]]
    cur.execute("SELECT DISTINCT neighbourhood FROM location ORDER BY neighbourhood")
    neighborhoods = [row[0] for row in cur.fetchall() if row[0]]
    cur.close()
    conn.close()
    return crime_types, neighborhoods

crime_type_list, neighborhood_list = get_filter_options()

# --- Sidebar Filters ---
st.sidebar.header("📊 Filter Crime Records")
selected_type = st.sidebar.selectbox("Select Crime Type:", options=[""] + crime_type_list)
selected_neighborhood = st.sidebar.selectbox("Select Neighborhood:", options=[""] + neighborhood_list)
selected_day = st.sidebar.selectbox("Day of Week:", options=["", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])



def fetch_data():
    query = """
    SELECT i.datetime, i.incident_type_primary, l.neighbourhood
    FROM incident i
    JOIN location l ON i.incident_id = l.incident_id
    WHERE (? = '' OR i.incident_type_primary LIKE ?)
      AND (? = '' OR l.neighbourhood LIKE ?)
    ORDER BY i.datetime DESC
    LIMIT 500
    """

    params = (selected_type, f"%{selected_type}%", selected_neighborhood, f"%{selected_neighborhood}%")
    conn = get_connection()
    
    # Start timing
    start_time = time.time()
    
    df = pd.read_sql_query(query, conn, params=params)
    
    # End timing
    end_time = time.time()
    
    query_duration = end_time - start_time
    
    conn.close()
    
    return df, query_duration


# --- Load and Display Filtered Data ---
st.subheader("📄 Recent Crime Incidents")
data, query_time = fetch_data()
st.write(f"⏱️ Query executed in {query_time:.2f} seconds.")

st.dataframe(data, use_container_width=True)

# --- Charts ---
if not data.empty:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📌 Incidents by Type")
        type_counts = data["incident_type_primary"].value_counts()
        st.bar_chart(type_counts)

    with col2:
        st.subheader("📍 Incidents by Neighborhood")
        hood_counts = data["neighbourhood"].value_counts()
        st.bar_chart(hood_counts)
else:
    st.info("No records found for the selected filters.")

# --- Arbitrary SQL Execution Panel ---
st.markdown("---")
st.subheader("🛠️ Execute Custom SQL Queries")

user_query = st.text_area("Enter your SQL query below:", height=150)
if st.button("Run Query"):
    if user_query.strip() != "":
        try:
            conn = get_connection()
            cursor = conn.cursor()
            start = time.time()
            cursor.execute(user_query)
            end = time.time()
            query_duration = end - start
            if user_query.strip().lower().startswith("select"):
                result = cursor.fetchall()
                cols = [description[0] for description in cursor.description]
                result_df = pd.DataFrame(result, columns=cols)
                st.success(f"✅ Query executed successfully in {query_duration:.2f} seconds.")
                st.dataframe(result_df, use_container_width=True)
            else:
                conn.commit()
                st.success(f"✅ Query executed and committed in {query_duration:.2f} seconds.")
            cursor.close()
            conn.close()
        except Exception as e:
            st.error(f"❌ Error: {e}")
    else:
        st.warning("⚠️ Please enter a query before running.")
