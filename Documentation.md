
# Project Report: Business and Email Workflow Application

## 1. Executive Summary

The **Business and Email Workflow Application** is a dynamic web tool designed to streamline the multi-stage process of business data acquisition, cleansing, persistence, and targeted email outreach. Built on the **Streamlit** framework for the frontend and integrated with **n8n** webhooks for backend workflow automation, this application provides a robust, user-friendly interface for a complex data-to-action pipeline. Its core innovation lies in its ability to handle **batch operations** (updates and emails) directly from an editable data grid, significantly boosting operational efficiency.

## 2. Project Goals and Scope

### 2.1. Goals

*   **Unified Interface:** Create a single application to manage all data and communication tasks.
*   **Data Integrity:** Allow users to review and manually edit data immediately before persistence.
*   **Batch Automation:** Implement reliable, live progress tracking for row-by-row batch updates and email sending.
*   **Flexibility:** Include a utility section to test data transformation logic without relying on the live search webhook.

### 2.2. Scope of Functionality

| Feature Category | Implemented Functions |
| :--- | :--- |
| **Data Acquisition** | Search by query (POST request to n8n), Export previous data (POST to n8n). |
| **Data Persistence** | Editable Data Grid (`st.data_editor`), Batch Update/Save (POST requests per row to n8n). |
| **Data Management** | Clear all previous data (POST request to n8n). |
| **Email Workflow** | State-driven transition to Email Composer, Subject/Body composition, Batch Email Send (POST requests per email draft to n8n). |
| **Utility** | JSON to Table Tester (bypassing search webhook). |

## 3. Technical Stack and Requirements

### 3.1. Technical Stack

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Frontend UI** | Python (Streamlit) | Interactive web interface, session state management, data visualization. |
| **Backend Workflow** | n8n (Webhooks) | Handles complex logic: data fetching, database updates, email generation, and final email sending. |
| **Data Processing** | Python (Pandas) | Data structure manipulation, column standardization, and type conversion. |
| **Communication** | Python (Requests) | Synchronous HTTP POST requests to n8n webhooks. |

### 3.2. System Requirements

The application requires a standard Python environment and access to four specific n8n webhook endpoints.

| Requirement | Details |
| :--- | :--- |
| **Operating System** | Windows, macOS, or Linux (Any system capable of running Python). |
| **Python Version** | Python 3.8 or higher. |
| **Required Libraries** | `streamlit`, `pandas`, `requests` |
| **n8n Connectivity** | n8n instance must be running and accessible at `http://localhost:5678`. |

## 4. Application Structure and Working Principles

### 4.1. Project Structure

The project is simplified into a single file for easy deployment:

```
business-email-app/
├── app.py          <-- All application code and logic
└── requirements.txt  <-- List of required Python packages
```

### 4.2. Core Logic and Data Flow

The application operates on a strict sequence of events managed by Streamlit's `st.session_state` and `st.rerun()`.

| Function/State | Role in Data Flow |
| :--- | :--- |
| **`handle_data_management_request(action)`** | Executes the 'Get data' or 'Clear' POST requests to the `Sheet_management` webhook. If successful, loads the data into a DataFrame. |
| **`make_search_request(query)`** | Executes the initial search POST request. Loads results into a DataFrame. |
| **`standardize_columns(df)`** | **Critical step:** Renames inconsistent column headers (e.g., `'ID'` to `'id'`, `'Serial'` to `'s_no'`) to match the application's required schema, ensuring data compatibility. |
| **`send_batch_update_requests(df)`** | Iterates row-by-row over the edited DataFrame, sending a POST request to the `Sheet_management` webhook for every single record. Upon 100% success, it triggers the view change. |
| **`email_composer_ui(source_key)`** | Collects Subject/Body and sends a request to the **Email Generation** webhook. Displays the returned personalized drafts in a final editable table. |
| **`send_email_batch_requests(df_emails)`** | Iterates row-by-row over the *final* edited email drafts, sending a POST request to the **Email Send** webhook for every single email. |

### 4.3. n8n Webhook Mapping

| App Constant | n8n URL (Example) | Action Payload |
| :--- | :--- | :--- |
| `UPDATE_WEBHOOK_URL` (Get) | `/webhook-test/Sheet_management` | `{"action": "Get data"}` |
| `UPDATE_WEBHOOK_URL` (Clear) | `/webhook-test/Sheet_management` | `{"action": "Clear"}` |
| `UPDATE_WEBHOOK_URL` (Update) | `/webhook-test/Sheet_management` | `{"action": "update task", "id": "..."}` |
| `EMAIL_WEBHOOK_URL` | `/webhook-test/email_writting` | `{"subject": "...", "body": "..."}` |
| `EMAIL_SEND_WEBHOOK_URL` | `/webhook-test/email_management` | `{"email_id": "...", "recipient_email": "..."}` |

## 5. Usage Guide

### 5.1. Setup

1.  Ensure all **n8n webhooks** are active.
2.  Install dependencies: `pip install streamlit pandas requests`.
3.  Run the application: `streamlit run app.py`.

### 5.2. Step-by-Step Workflow (Primary Tab)

| Step | Action | Button Click | Next View |
| :--- | :--- | :--- | :--- |
| **A. Data Load** | Load existing data from the sheet. | **⬇️ Export Previous Data (Get)** | Same View (Table Appears) |
| **B. Data Acquisition**| Search for new data. | **Execute Search** | Same View (Table Appears) |
| **C. Cleansing** | Edit any data directly in the table. | *None* | *None* |
| **D. Persistence** | Finalize changes and save to the sheet. | **✅ Save Changes & Proceed to Email** | **Email Composer** |
| **E. Email Draft** | Enter Subject/Body to generate personalized drafts. | **🚀 Proceed to Generate Emails** | Same View (Email Preview Table Appears) |
| **F. Final Send** | Send the final edited drafts. | **✉️ Send All Emails (Batch Send)** | Same View (Final Success/Failure Status) |

## 6. Technical Stack and Requirements

### 6.1. Installation and Setup (Cloning from GitHub)

This application is hosted on GitHub, allowing any user to easily clone and run the project locally.

#### A. Downloading the Project

The easiest way to obtain the project files is by cloning the repository using Git:

1.  **Install Git:** Ensure the Git version control system is installed on your machine.
2.  **Open Terminal/Command Prompt.**
3.  **Clone the Repository:** Execute the following command:

    ```bash
    git clone https://github.com/MuhammadOwais268/business-email-app.git
    ```

4.  **Navigate to the Project Directory:**
    ```bash
    cd business-email-app
    ```

#### B. Installing Dependencies

The project relies on standard Python libraries, listed in a `requirements.txt` file (or assumed if not explicitly provided in the repository).

1.  **(Optional but Recommended) Create a Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use: .\venv\Scripts\activate
    ```

2.  **Install Required Libraries:**
    *   *Assuming a `requirements.txt` is present:*
        ```bash
        pip install -r requirements.txt
        ```
    *   *If no `requirements.txt` is present, install manually:*
        ```bash
        pip install streamlit pandas requests
        ```

#### C. Running the Application

1.  **Ensure Webhooks are Active:** Confirm that your n8n instance is running and all required webhooks (as detailed in Section 3.2) are active and listening at `http://localhost:5678`.
2.  **Execute the App:** Run the application using the Streamlit command:
    ```bash
    streamlit run app.py
    ```

The application will launch in your default web browser at `http://localhost:8501`.

---
