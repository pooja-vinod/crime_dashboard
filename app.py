# app.py - Streamlit Dashboard for Crime Reporting DB

import streamlit as st
import pandas as pd
import psycopg2
from psycopg2 import sql

# --- Streamlit Page Config ---
st.set_page_config(page_title="Crime Dashboard", layout="wide")
st.title("🚨 Buffalo Crime Reporting Dashboard")


# --- Database Connection ---
def get_connection():
    return psycopg2.connect(
        host=st.secrets["db"]["host"],
        port=st.secrets["db"]["port"],
        database=st.secrets["db"]["database"],
        user=st.secrets["db"]["user"],
        password=st.secrets["db"]["password"]

    )

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


# --- Filtered Incident Data ---
def fetch_data():
    query = """
    SELECT i.datetime, i.incident_type_primary, l.neighbourhood
    FROM incident i
    JOIN location l ON i.incident_id = l.incident_id
    WHERE (%s = '' OR i.incident_type_primary ILIKE %s)
      AND (%s = '' OR l.neighbourhood ILIKE %s)
    ORDER BY i.datetime DESC
    LIMIT 500
"""

    params = (selected_type, f"%{selected_type}%", selected_neighborhood, f"%{selected_neighborhood}%")
    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

# --- Load and Display Filtered Data ---
st.subheader("📄 Recent Crime Incidents")
data = fetch_data()
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
            cursor.execute(user_query)
            if user_query.strip().lower().startswith("select"):
                result = cursor.fetchall()
                cols = [desc[0] for desc in cursor.description]
                result_df = pd.DataFrame(result, columns=cols)
                st.success("✅ Query executed successfully.")
                st.dataframe(result_df, use_container_width=True)
            else:
                conn.commit()
                st.success("✅ Query executed and committed successfully.")
            cursor.close()
            conn.close()
        except Exception as e:
            st.error(f"❌ Error: {e}")
    else:
        st.warning("⚠️ Please enter a query before running.")
