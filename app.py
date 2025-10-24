import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import uuid
import io
import json

# --- Configuration ---
SEARCH_WEBHOOK_URL = "http://localhost:5678/webhook/ai-business-lookup"
UPDATE_WEBHOOK_URL = "http://localhost:5678/webhook/Sheet_management"
EMAIL_WEBHOOK_URL = "http://localhost:5678/webhook/email_writting"
EMAIL_SEND_WEBHOOK_URL = "http://localhost:5678/webhook/email_management"
REQUEST_TIMEOUT = 300 # Seconds (5 minutes)
UPDATE_TIMEOUT = 300 # Seconds for single update/send request

# --- Shared Utility Functions (Code omitted for brevity, but they remain unchanged) ---

def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts necessary columns (like 'timestamp') to their correct data types 
    for compatibility with st.data_editor and fills None values.
    """
    if 'timestamp' in df.columns and df['timestamp'].dtype == object:
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', utc=True)
        except Exception as e:
            st.warning(f"Could not convert 'timestamp' column to datetime. Error: {e}")
    
    if 'emails' in df.columns:
        df['emails'] = df['emails'].astype(str).replace('None', '') 

    return df

def generate_payload(search_query: str) -> dict:
    """Generates the JSON payload for the POST request."""
    return {
        "searchQuery": search_query,
        "requestId": f"req-{uuid.uuid4()}",
        "timestamp": datetime.utcnow().isoformat(timespec='seconds') + 'Z'
    }

def make_search_request(search_query: str):
    """
    Sends the POST request to the n8n webhook and handles the response.
    Returns a pandas DataFrame or None on failure.
    """
    payload = generate_payload(search_query)
    st.info(f"Sending POST request to webhook: {SEARCH_WEBHOOK_URL} with query: **{search_query}** (Timeout set to {REQUEST_TIMEOUT} seconds)")
    
    try:
        response = requests.post(
            SEARCH_WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=REQUEST_TIMEOUT 
        )
        
        if response.status_code == 200:
            try:
                data = json.loads(response.text)
            except json.JSONDecodeError:
                st.error("Error: Could not decode JSON from webhook response.")
                st.code(response.text, language='text')
                return None
                
            if data and isinstance(data, list):
                st.success("Search successful! Data received.")
                df = pd.DataFrame(data)
                return preprocess_data(df)
            else:
                st.warning("Request successful, but received empty or invalid JSON data. Check the format below.")
                st.code(response.text, language='json')
                return None
        else:
            st.error(f"Error: Webhook returned status code {response.status_code}. Response: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        st.error(f"Error making request to webhook: {e}")
        st.warning("Please ensure your n8n webhook is running at the specified URL.")
        return None

def send_batch_update_requests(df: pd.DataFrame, source_key: str):
    """
    Sends an individual POST request for each row in the DataFrame to the update webhook.
    Returns True if successful, False otherwise.
    """
    st.subheader(f"Sending Batch Updates for {source_key} ({len(df)} records)...")
    
    required_cols = ['id', 's_no', 'name']
    if not all(col in df.columns for col in required_cols):
        st.error(f"Cannot perform update. DataFrame is missing one of the required columns: {required_cols}")
        return False

    df_to_send = df.copy()
    df_to_send['timestamp'] = df_to_send['timestamp'].apply(
        lambda x: x.isoformat(timespec='milliseconds').replace('+00:00', 'Z') if pd.notna(x) else None
    )
    
    records = df_to_send.to_dict('records')
    progress_bar = st.progress(0)
    status_text = st.empty()
    success_count = 0
    
    for index, record in enumerate(records):
        s_no = record.get('s_no', index + 1)
        
        payload = {
            "action": "update task",
            **record
        }
        
        status_text.text(f"Updating record {index + 1}/{len(records)}: S.No {s_no} - {record.get('name', 'No Name')}")
        
        try:
            response = requests.post(
                UPDATE_WEBHOOK_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=UPDATE_TIMEOUT
            )
            
            if response.status_code == 200:
                success_count += 1
            else:
                st.error(f"Failed to update S.No {s_no} ({record.get('name', 'No Name')}): Status {response.status_code}. Response: {response.text}")

        except requests.exceptions.RequestException as e:
            st.error(f"Failed to send request for S.No {s_no} ({record.get('name', 'No Name')}): {e}")

        progress_bar.progress((index + 1) / len(records))

    progress_bar.empty()
    status_text.empty()
    
    if success_count == len(records):
        st.success(f"✅ Batch Update COMPLETE! All {success_count} records were saved successfully.")
        return True
    else:
        st.warning(f"⚠️ Batch Update finished with {success_count} successful updates and {len(records) - success_count} failures. Please check error messages above.")
        return False

def send_email_batch_requests(df_emails: pd.DataFrame, source_key: str):
    """
    Sends an individual POST request for each email row to the email management webhook.
    """
    st.subheader(f"Sending {len(df_emails)} Emails (Batch Send)...")
    
    required_cols = ['email_id', 'recipient_email', 'subject', 'body']
    if not all(col in df_emails.columns for col in required_cols):
        st.error(f"Cannot send emails. DataFrame is missing one of the required columns: {required_cols}")
        return

    records = df_emails.to_dict('records')
    progress_bar = st.progress(0)
    status_text = st.empty()
    success_count = 0
    
    for index, record in enumerate(records):
        email_id = record.get('email_id', index + 1)
        recipient = record.get('recipient_email', 'No Recipient')
        
        # Payload must match the exact dummy format
        payload = {
            "email_id": record.get('email_id'),
            "recipient_email": record.get('recipient_email'),
            "subject": record.get('subject'),
            "body": record.get('body')
        }
        
        status_text.text(f"Sending email {index + 1}/{len(records)}: ID {email_id} to {recipient}")
        
        try:
            # Send the POST request to the final send webhook
            response = requests.post(
                EMAIL_SEND_WEBHOOK_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=UPDATE_TIMEOUT
            )
            
            if response.status_code == 200:
                success_count += 1
            else:
                st.error(f"Failed to send email {email_id}: Status {response.status_code}. Response: {response.text}")

        except requests.exceptions.RequestException as e:
            st.error(f"Failed to send request for email {email_id}: {e}")

        progress_bar.progress((index + 1) / len(records))

    progress_bar.empty()
    status_text.empty()
    
    if success_count == len(records):
        st.success(f"🎉 Email Batch Send COMPLETE! Successfully sent all {success_count} emails.")
    else:
        st.warning(f"⚠️ Email Batch Send finished with {success_count} successful sends and {len(records) - success_count} failures. Check error messages above.")


# --- UI Functions ---

def email_composer_ui(source_key):
    """UI for composing and sending the final email request."""
    st.title("📧 Email Composer")
    st.markdown("Your previous action was successful. Now, compose the email subject and body to generate contact emails for the updated list.")

    # 1. Inputs
    subject = st.text_input("Email Subject:", key=f"email_subject_{source_key}", 
                            value="Project Update: Progress Report for AI System")
    body = st.text_area("Email Body:", key=f"email_body_{source_key}", height=250, 
                        value="Hello Team,\n\nThis is to inform you that our AI system project is progressing as planned. The next development phase will start tomorrow, focusing on model optimization and testing.\n\nBest regards,\nMuhammad Owais")

    # 2. Proceed Button
    if st.button("🚀 Proceed to Generate Emails", key=f"proceed_button_{source_key}", type="primary"):
        if not subject or not body:
            st.error("Subject and Body cannot be empty.")
            return

        payload = {
            "subject": subject,
            "body": body
        }

        st.info(f"Sending POST request to email generation webhook: {EMAIL_WEBHOOK_URL}")
        
        with st.spinner("Generating and previewing emails..."):
            try:
                response = requests.post(
                    EMAIL_WEBHOOK_URL,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=UPDATE_TIMEOUT
                )
                
                if response.status_code == 200:
                    data = json.loads(response.text)
                    if data and isinstance(data, list):
                        df = pd.DataFrame(data)
                        
                        # --- FIX: Rename 'recipient' to 'recipient_email' ---
                        if 'recipient' in df.columns and 'recipient_email' not in df.columns:
                            df.rename(columns={'recipient': 'recipient_email'}, inplace=True)
                        # --- END FIX ---

                        st.session_state[f'email_preview_df_{source_key}'] = df
                        st.session_state.pop(f'show_write_downloads_{source_key}', None) # Reset download visibility
                        st.success("Email previews generated successfully!")
                    else:
                        st.error("Webhook returned successful status but the response data was empty or invalid. Check the format below.")
                        st.code(response.text, language='json')
                else:
                    st.error(f"Error: Email webhook returned status code {response.status_code}. Response: {response.text}")

            except requests.exceptions.RequestException as e:
                st.error(f"Error making request to email webhook: {e}")
        
    # 3. Display Preview Table (Email Composer)
    email_preview_key = f'email_preview_df_{source_key}'
    edited_email_data_key = f'edited_email_data_{source_key}'

    if email_preview_key in st.session_state and st.session_state[email_preview_key] is not None:
        df_email = st.session_state[email_preview_key]
        st.subheader("✉️ Email Preview Table (Editable)")
        st.markdown("You can edit the subject and body for final checks before sending.")
        
        edited_email_df = st.data_editor(
            df_email,
            key=f"email_data_editor_{source_key}",
            use_container_width=True,
            hide_index=True,
            column_config={
                "email_id": "Email ID",
                "recipient_email": st.column_config.TextColumn("Recipient Email", required=True),
                "subject": st.column_config.TextColumn("Final Subject", required=True),
                "body": st.column_config.TextColumn("Final Body", required=True),
            }
        )
        st.session_state[edited_email_data_key] = edited_email_df
        
        st.divider()
        st.subheader("Final Email Actions")
        
        # --- SEND EMAILS BUTTON (Final Action) ---
        col_send, col_download_csv, col_download_json = st.columns([2, 1, 1])

        with col_send:
            if st.button("✉️ Send All Emails (Batch Send)", key=f"send_button_{source_key}", use_container_width=True, type="primary"):
                if st.session_state[edited_email_data_key] is not None and not st.session_state[edited_email_data_key].empty:
                    send_email_batch_requests(st.session_state[edited_email_data_key], source_key)
                else:
                    st.warning("No emails to send.")

        # --- Download Buttons Section ---
        df_download = st.session_state[edited_email_data_key]
        csv_data_email = df_download.to_csv(index=False).encode('utf-8')
        json_buffer_email = io.StringIO()
        df_download.to_json(json_buffer_email, orient='records', indent=4)
        json_data_email = json_buffer_email.getvalue().encode('utf-8')

        with col_download_csv:
            st.download_button(
                label="💾 Download CSV",
                data=csv_data_email,
                file_name=f"{source_key}_final_emails.csv",
                mime="text/csv",
                use_container_width=True
            )
        with col_download_json:
            st.download_button(
                label="💾 Download JSON",
                data=json_data_email,
                file_name=f"{source_key}_final_emails.json",
                mime="application/json",
                use_container_width=True
            )

    # Back button to return to the data editor
    if st.button("⬅️ Back to Data Editor", key=f"back_button_{source_key}"):
        st.session_state[f'current_view_{source_key}'] = "data_editor"
        st.session_state.pop(email_preview_key, None)
        st.session_state.pop(edited_email_data_key, None)
        st.rerun()


# --- Tab 1: Webhook Search Main Logic ---

def webhook_search_tab():
    # State management for multi-step UI
    if st.session_state.current_view_tab1 == "email_composer":
        email_composer_ui("tab1")
        return

    # --- Data Editor View (Default) ---
    st.title("🌐 Webhook Search & Live Editing")
    st.markdown("Enter a search query below to send a POST request to the webhook and get results.")

    # 1. Search Input and Button
    search_query = st.text_input(
        "Search Query (e.g., AI startups in Pakistan)",
        key="query_input_tab1",
        on_change=lambda: st.session_state.pop('search_results_df', None), 
        placeholder="Enter your search query here..."
    )
    col1, col2 = st.columns([1, 4])
    with col1:
        search_button = st.button("Search", key="search_button_tab1")

    # 2. Search Logic
    if search_button or (search_query and st.session_state.last_query != search_query):
        if search_query:
            st.session_state.last_query = search_query
            with st.spinner(f"Searching for '{search_query}'..."):
                df = make_search_request(search_query) 
                st.session_state.search_results_df = df
                st.session_state.edited_data = None
        else:
            st.warning("Please enter a search query.")
            st.session_state.search_results_df = None

    # 3. Display Results, Editable Table, and Action Options
    if st.session_state.search_results_df is not None:
        df = st.session_state.search_results_df
        
        st.subheader(f"Search Results for: '{st.session_state.last_query}'")
        st.markdown(f"**Total Records Found:** {len(df)}")

        # Editable Data Table
        edited_df = st.data_editor(df, key="data_editor_tab1", use_container_width=True, hide_index=True, num_rows="dynamic",
            column_order=('name', 'type', 'location', 'phone', 'emails', 'website', 'rating', 's_no', 'timestamp', 'id'),
            column_config={
                "name": st.column_config.TextColumn("Name", required=True), "type": st.column_config.TextColumn("Type"),
                "location": st.column_config.TextColumn("Location"), "phone": st.column_config.TextColumn("Phone"),
                "emails": st.column_config.TextColumn("Emails"), "website": st.column_config.LinkColumn("Website", display_text="[Link]"),
                "rating": st.column_config.NumberColumn("Rating", format="%.1f", help="Google Rating"), "s_no": "S.No",
                "timestamp": st.column_config.DatetimeColumn("Timestamp", format="YYYY-MM-DD HH:mm:ss Z"), "id": "ID (Internal)",
            })
        st.session_state.edited_data = edited_df

        st.divider()
        st.subheader("Action Options")
        
        col_save, col_download_csv, col_download_json = st.columns([2, 1, 1])
        
        with col_save:
            if st.button("✅ Save All Changes (Batch Update)", key="save_button_tab1_update", use_container_width=True, type="primary"):
                if st.session_state.edited_data is not None and not st.session_state.edited_data.empty:
                    if send_batch_update_requests(st.session_state.edited_data, "Webhook Search"):
                        st.session_state.current_view_tab1 = "email_composer"
                        st.rerun()
                else:
                    st.warning("No data to save. Please perform a search first.")
        
        # Download buttons
        csv_data = st.session_state.edited_data.to_csv(index=False).encode('utf-8') if st.session_state.edited_data is not None else b''
        json_buffer = io.StringIO()
        if st.session_state.edited_data is not None:
            st.session_state.edited_data.to_json(json_buffer, orient='records', date_format='iso', indent=4)
        json_data = json_buffer.getvalue().encode('utf-8') if st.session_state.edited_data is not None else b''

        with col_download_csv:
            st.download_button(label="💾 Download CSV", data=csv_data, file_name=f"{st.session_state.last_query.replace(' ', '_')}_edited.csv", mime="text/csv", use_container_width=True, disabled=st.session_state.edited_data is None)
        with col_download_json:
            st.download_button(label="💾 Download JSON", data=json_data, file_name=f"{st.session_state.last_query.replace(' ', '_')}_edited.json", mime="application/json", use_container_width=True, disabled=st.session_state.edited_data is None)


# --- Tab 2: JSON to Table Tester Main Logic ---

def json_tester_tab():
    # State management for multi-step UI
    if st.session_state.current_view_tab2 == "email_composer":
        email_composer_ui("tab2")
        return

    # --- Data Editor View (Default) ---
    st.title("🧪 JSON to Editable Table Tester")
    st.markdown("Paste your raw JSON array output from the webhook below and click the button to generate the editable table.")

    # 1. JSON Input Area
    json_input = st.text_area("Paste JSON Array Here (Must start with '['):", height=300, key="json_input_tab2",
        placeholder="[ \n  { \n    \"name\": \"Example Business\", \n    \"type\": \"Restaurant\", \n    \"timestamp\": \"2025-10-24T10:39:23.146Z\" \n  }, \n  ... \n]")

    # 2. Button and Conversion Logic
    if st.button("Generate Table from JSON", key="generate_button_tab2"):
        if json_input:
            try:
                data = json.loads(json_input)
                if isinstance(data, list) and len(data) > 0:
                    df = pd.DataFrame(data)
                    st.session_state.test_df = preprocess_data(df)
                    st.session_state.edited_data_test = None
                    st.success(f"Successfully loaded {len(df)} records.")
                elif isinstance(data, dict):
                    st.error("Error: The JSON appears to be a single object. Please paste a JSON array (starts with '[').")
                    st.session_state.test_df = None
                else:
                    st.warning("JSON list is empty. Please paste valid data.")
                    st.session_state.test_df = None
            except json.JSONDecodeError:
                st.error("Error: Invalid JSON format. Please check for syntax errors.")
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
        
        st.subheader(f"Editable Test Results")
        st.markdown(f"**Total Records Loaded:** {len(df)}")

        # Editable Data Table
        edited_df_test = st.data_editor(df, key="data_editor_test_tab2", use_container_width=True, hide_index=True, num_rows="dynamic",
            column_order=('name', 'type', 'location', 'phone', 'emails', 'website', 'rating', 's_no', 'timestamp', 'id'),
            column_config={
                "name": st.column_config.TextColumn("Name", required=True), "type": st.column_config.TextColumn("Type"),
                "location": st.column_config.TextColumn("Location"), "phone": st.column_config.TextColumn("Phone"),
                "emails": st.column_config.TextColumn("Emails"), "website": st.column_config.LinkColumn("Website", display_text="[Link]"),
                "rating": st.column_config.NumberColumn("Rating", format="%.1f", help="Google Rating"), "s_no": "S.No",
                "timestamp": st.column_config.DatetimeColumn("Timestamp", format="YYYY-MM-DD HH:mm:ss Z"), "id": "ID (Internal)",
            })
        st.session_state.edited_data_test = edited_df_test

        st.divider()
        st.subheader("Action Options")
        
        col_save, col_download_csv, col_download_json = st.columns([2, 1, 1])

        with col_save:
            if st.button("✅ Save All Changes (Batch Update)", key="save_button_tab2_update", use_container_width=True, type="primary"):
                if st.session_state.edited_data_test is not None and not st.session_state.edited_data_test.empty:
                    if send_batch_update_requests(st.session_state.edited_data_test, "JSON Tester"):
                        st.session_state.current_view_tab2 = "email_composer"
                        st.rerun()
                else:
                    st.warning("No data to save. Please load JSON data first.")

        # Download buttons
        csv_data_test = st.session_state.edited_data_test.to_csv(index=False).encode('utf-8') if st.session_state.edited_data_test is not None else b''
        json_buffer_test = io.StringIO()
        if st.session_state.edited_data_test is not None:
            st.session_state.edited_data_test.to_json(json_buffer_test, orient='records', date_format='iso', indent=4)
        json_data_test = json_buffer_test.getvalue().encode('utf-8') if st.session_state.edited_data_test is not None else b''

        with col_download_csv:
            st.download_button(label="💾 Download CSV", data=csv_data_test, file_name="json_tester_edited.csv", mime="text/csv", use_container_width=True, disabled=st.session_state.edited_data_test is None)
        with col_download_json:
            st.download_button(label="💾 Download JSON", data=json_data_test, file_name="json_tester_edited.json", mime="application/json", use_container_width=True, disabled=st.session_state.edited_data_test is None)


# --- Main App Execution ---

st.set_page_config(
    page_title="Business & Hospital Lookup",
    layout="wide"
)

# Initialize ALL session state keys globally (FIXED: Moved up)
if 'current_view_tab1' not in st.session_state:
    st.session_state.current_view_tab1 = "data_editor"
if 'current_view_tab2' not in st.session_state:
    st.session_state.current_view_tab2 = "data_editor"
if 'search_results_df' not in st.session_state:
    st.session_state.search_results_df = None
if 'last_query' not in st.session_state:
    st.session_state.last_query = ""
if 'edited_data' not in st.session_state:
    st.session_state.edited_data = None
if 'test_df' not in st.session_state:
    st.session_state.test_df = None
if 'edited_data_test' not in st.session_state:
    st.session_state.edited_data_test = None
if 'email_preview_df_tab1' not in st.session_state:
    st.session_state.email_preview_df_tab1 = None
if 'edited_email_data_tab1' not in st.session_state:
    st.session_state.edited_email_data_tab1 = None
if 'email_preview_df_tab2' not in st.session_state:
    st.session_state.email_preview_df_tab2 = None
if 'edited_email_data_tab2' not in st.session_state:
    st.session_state.edited_email_data_tab2 = None


# Create two tabs
tab1, tab2 = st.tabs(["🌐 Webhook Search & Live Edit", "🧪 JSON to Table Tester"])

with tab1:
    webhook_search_tab()

with tab2:
    json_tester_tab()