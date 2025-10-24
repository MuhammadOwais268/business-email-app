## 🎯 Project Overview

This application provides a robust, multi-stage interface for managing business data, performing data cleansing, and executing targeted email outreach. It is built using **Streamlit** for the frontend UI and relies on **n8n** webhooks for all backend processing, data persistence, and communication.

The app uses a state-driven UI to guide the user through a sequential workflow: **Search → Edit/Save → Compose Email → Batch Send/Download.**

## ⚙️ Prerequisites

Before running the application, ensure you have the following installed and configured:

1.  **Python 3.8+**
2.  **Required Python Libraries:**
    ```bash
    pip install streamlit pandas requests
    ```
3.  **n8n Instance:** Your n8n workflow tool must be running and accessible at `http://localhost:5678`.
4.  **n8n Webhooks:** You must have the following four webhooks configured and active in your n8n instance:

| Webhook Name | Endpoint (Used in App) | Purpose |
| :--- | :--- | :--- |
| Search (Data Acquisition) | `http://localhost:5678/webhook/ai-business-lookup` | Returns initial business search data. |
| Update (Data Persistence) | `http://localhost:5678/webhook/Sheet_management` | Receives individual records for batch saving/database updates. |
| Email Generation | `http://localhost:5678/webhook-test/email_writting` | Generates a preview list of emails based on a template. |
| Email Send (Final Action) | `http://localhost:5678/webhook-test/email_management` | Executes the final batch sending/logging of each individual email. |

## 🚀 Getting Started

1.  **Save the Code:** Save the provided Python code as `app.py`.
2.  **Run the Application:** Open your terminal in the directory where `app.py` is saved and run:
    ```bash
    streamlit run app.py
    ```
3.  The application will open in your default web browser at `http://localhost:8501`.

## 📖 User Workflow

The application operates across two tabs, but the primary workflow is on the first tab.

### Tab 1: 🌐 Webhook Search & Live Edit (Operational Workflow)

This tab handles the full sequence from initial search to final email dispatch.

| Step | Action | Description |
| :--- | :--- | :--- |
| **1. Search** | Enter a query (e.g., `AI startups in Pakistan`) and click **Search**. | Triggers the **Search Webhook**. Results are displayed in an editable table. |
| **2. Edit** | Modify cells directly in the table (data cleansing). | Data is stored locally in the session state as you edit. |
| **3. Batch Update** | Click **✅ Save All Changes (Batch Update)** (Green Button). | Triggers the **Update Webhook** in a row-by-row batch operation. Progress is displayed live. **On success, the view switches to the Email Composer.** |
| **4. Compose Email** | Fill in the **Subject** and **Body** template. Click **🚀 Proceed to Generate Emails**. | Triggers the **Email Generation Webhook**. Returns a list of personalized email drafts. |
| **5. Review & Edit**| Review the drafts in the **Editable Email Preview Table** and make final corrections. | The table is ready for the final send action. |
| **6. Batch Send** | Click **✉️ Send All Emails (Batch Send)**. | Triggers the **Email Send Webhook** in a row-by-row batch operation for each final email draft. |

### Tab 2: 🧪 JSON to Table Tester (Utility Workflow)

This tab is a debugging and utility tool to test the editing and batch features without relying on a successful initial search:

1.  **Load Data:** Paste a valid JSON array (`[...]`) into the text area.
2.  **Generate Table:** Click **Generate Table from JSON**.
3.  The workflow continues from **Step 2** (Edit & Batch Update) as in the primary tab.

## 🛠️ Key Technical Details

*   **View Management:** The transition between the **Data Editor** view and the **Email Composer** view is controlled by `st.session_state.current_view_tab1` and is forced with `st.rerun()`.
*   **Batch Request Logic:** Functions `send_batch_update_requests` and `send_email_batch_requests` iterate over DataFrame rows, construct specific JSON payloads, and send requests sequentially with live progress updates.
*   **Data Compatibility Fix:** The `preprocess_data` function is crucial for converting the webhook's string `timestamp` format into a proper `datetime` object for compatible editing in Streamlit, resolving the `StreamlitAPIException`.
*   **Robust JSON Parsing:** The `make_search_request` function uses `json.loads(response.text)` to ensure the payload is correctly parsed even if the webhook sends a generic `Content-Type` header.
*   **Column Correction:** The `email_composer_ui` includes a critical rename step (`df.rename(columns={'recipient': 'recipient_email'}, inplace=True)`) to harmonize the data structure between n8n's output and the app's requirements.