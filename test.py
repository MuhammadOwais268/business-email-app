import streamlit as st
import pandas as pd
import json

# --- Utility Functions ---

def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts necessary columns (like 'timestamp') to their correct data types 
    for compatibility with st.data_editor.
    """
    # 1. Convert 'timestamp' string to proper datetime object
    if 'timestamp' in df.columns and df['timestamp'].dtype == object:
        try:
            # The 'Z' at the end indicates UTC time. pandas handles this with utc=True.
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', utc=True)
        except Exception as e:
            st.warning(f"Could not convert 'timestamp' column to datetime. Error: {e}")
    
    # 2. Fill None values in 'emails' for cleaner display
    if 'emails' in df.columns:
        df['emails'] = df['emails'].fillna('')

    return df

# --- Streamlit UI ---

st.set_page_config(
    page_title="JSON to Editable Table Tester",
    layout="wide"
)

st.title("🧪 JSON to Editable Table Tester")
st.markdown("Paste your raw JSON array output from the webhook below and click the button to generate the editable table.")

# Initialize session state for storing data
if 'test_df' not in st.session_state:
    st.session_state.test_df = None

# 1. JSON Input Area
json_input = st.text_area(
    "Paste JSON Array Here (Must start with '['):",
    height=300,
    key="json_input",
    placeholder="[ \n  { \n    \"name\": \"Example Business\", \n    \"type\": \"Restaurant\", \n    \"timestamp\": \"2025-10-24T10:39:23.146Z\" \n  }, \n  ... \n]"
)

# 2. Button and Conversion Logic
if st.button("Generate Table from JSON", key="generate_button"):
    if json_input:
        try:
            # 1. Parse the JSON input string
            data = json.loads(json_input)
            
            # 2. Validate that it's a list (array) and not empty
            if isinstance(data, list) and len(data) > 0:
                # 3. Convert to a pandas DataFrame and preprocess
                df = pd.DataFrame(data)
                df = preprocess_data(df) # <-- Apply the necessary type conversion
                
                st.session_state.test_df = df
                st.success(f"Successfully loaded {len(df)} records.")
            elif isinstance(data, dict):
                st.error("Error: The JSON appears to be a single object, not a list of objects. Please paste a JSON array (starts with '[').")
                st.session_state.test_df = None
            else:
                st.warning("JSON list is empty. Please paste valid data.")
                st.session_state.test_df = None

        except json.JSONDecodeError:
            st.error("Error: Invalid JSON format. Please check for syntax errors (e.g., missing quotes, trailing commas).")
            st.session_state.test_df = None
        except Exception as e:
            st.error(f"An unexpected error occurred during processing: {e}")
            st.session_state.test_df = None
    else:
        st.warning("Please paste JSON data into the text area.")
        st.session_state.test_df = None


# 3. Display Results and Editable Table
if st.session_state.test_df is not None:
    df = st.session_state.test_df
    
    st.subheader(f"Editable Search Results")
    st.markdown(f"**Total Records Loaded:** {len(df)}")

    # Use st.data_editor to display an editable table
    edited_df = st.data_editor(
        df,
        key="data_editor_test",
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic", # Allows adding/deleting rows
        # Specify column order and configuration based on your n8n output keys
        column_order=('name', 'type', 'location', 'phone', 'emails', 'website', 'rating', 's_no', 'timestamp', 'id'),
        # Define column configurations for better user experience
        column_config={
            "name": st.column_config.TextColumn("Name", required=True),
            "type": st.column_config.TextColumn("Type"),
            "location": st.column_config.TextColumn("Location"),
            "phone": st.column_config.TextColumn("Phone"),
            "emails": st.column_config.TextColumn("Emails"),
            "website": st.column_config.LinkColumn("Website", display_text="[Link]"),
            "rating": st.column_config.NumberColumn("Rating", format="%.1f", help="Google Rating"),
            "s_no": "S.No",
            # This works because the data is now a pandas datetime object
            "timestamp": st.column_config.DatetimeColumn("Timestamp", format="YYYY-MM-DD HH:mm:ss Z"),
            "id": "ID (Internal)",
        }
    )
    
    st.session_state.edited_data_test = edited_df

    st.divider()
    # Display the final edited data for verification (optional)
    st.subheader("Final Edited Data (DataFrame)")
    st.dataframe(st.session_state.edited_data_test, use_container_width=True)