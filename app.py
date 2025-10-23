import streamlit as st
import requests
import json
import pandas as pd

# Configuration: Load from secrets.toml
BASE_URL = st.secrets["BASE_URL"]  # e.g., "https://your-pbx-domain.com:443"
API_PATH = "/openapi/v1.0"
USERNAME = st.secrets["USERNAME"]  # Client ID
PASSWORD = st.secrets["PASSWORD"]  # Client Secret
HEADERS = {
    "User-Agent": "OpenAPI",
    "Content-Type": "application/json"
}

# Function to get access token
@st.cache_data(ttl=1800)  # Cache for 30 minutes (token expiry time)
def get_access_token():
    url = f"{BASE_URL}{API_PATH}/get_token"
    payload = {
        "username": USERNAME,
        "password": PASSWORD
    }
    try:
        response = requests.post(url, headers=HEADERS, data=json.dumps(payload))
        response.raise_for_status()  # Raises error for bad status codes
        data = response.json()
        if data["errcode"] == 0:
            return data["access_token"]
        else:
            st.error(f"Authentication failed: {data['errmsg']}")
            return None
    except requests.RequestException as e:
        st.error(f"Error connecting to API: {str(e)}")
        return None

# Function to fetch system information
def fetch_system_info(token):
    url = f"{BASE_URL}{API_PATH}/system/information"
    headers = {
        "User-Agent": "OpenAPI",
        "Authorization": token  # No 'Bearer' prefix per Yeastar docs
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data["errcode"] == 0:
            return data
        else:
            st.error(f"Failed to fetch system info: {data['errmsg']}")
            return None
    except requests.RequestException as e:
        st.error(f"Error fetching system info: {str(e)}")
        return None

# Function to fetch extensions
def fetch_extensions(token):
    url = f"{BASE_URL}{API_PATH}/extension/list"
    headers = {
        "User-Agent": "OpenAPI",
        "Authorization": token
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data["errcode"] == 0:
            return data["extension"]  # List of extensions
        else:
            st.error(f"Failed to fetch extensions: {data['errmsg']}")
            return None
    except requests.RequestException as e:
        st.error(f"Error fetching extensions: {str(e)}")
        return None

# Streamlit app layout
st.title("Yeastar PBX Dashboard")
st.write("Real-time data from your Yeastar PBX system.")

# Get access token
token = get_access_token()
if not token:
    st.stop()  # Stop app if authentication fails

# System Information Section
st.header("System Information")
system_info = fetch_system_info(token)
if system_info:
    for key, value in system_info.items():
        if key not in ["errcode", "errmsg"]:  # Skip error fields
            st.markdown(f"**{key.replace('_', ' ').title()}**: {value}")

# Extensions Section
st.header("Extensions")
extensions = fetch_extensions(token)
if extensions:
    df = pd.DataFrame(extensions)  # Convert to DataFrame for table display
    st.dataframe(df, use_container_width=True)  # Display as interactive table
else:
    st.write("No extensions data available.")

# Refresh button
if st.button("Refresh Data"):
    st.cache_data.clear()  # Clear cache to force new API calls
    st.rerun()  # Rerun app to refresh data