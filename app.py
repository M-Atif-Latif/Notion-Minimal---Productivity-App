import streamlit as st
import uuid
st.set_page_config(page_title="Notion Minimal - Productivity App", layout="wide")

from streamlit_quill import st_quill
import requests
import json
import os
from datetime import datetime
from io import BytesIO
import base64
import calendar as cal

# --- Custom CSS for Notion-like Dark Theme ---
st.markdown("""
<style>
body, .stApp {
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, 'Noto Sans', sans-serif;
    background-color: #18191a !important;
    color: #ececec !important;
}

[data-testid="stExpander"] {
    background: #23272f !important;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.12);
    margin-bottom: 1.5rem;
    border: 1px solid #23272f;
}

button[kind="primary"] {
    background: #2f80ed !important;
    color: #fff !important;
    border-radius: 6px;
    font-weight: 600;
    border: none;
    box-shadow: 0 1px 2px rgba(0,0,0,0.08);
}

section[data-testid="stSidebar"] {
    background: #202124 !important;
    border-right: 1px solid #23272f;
}

h1, h2, h3, h4 {
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, 'Noto Sans', sans-serif;
    font-weight: 700;
    color: #ececec !important;
}

.notion-tag {
    display: inline-block;
    background: #23272f;
    color: #ececec;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 0.85em;
    margin-right: 4px;
    margin-bottom: 2px;
}

.stCheckbox > label {
    font-size: 1em;
    color: #ececec !important;
}

/* Streamlit input backgrounds for dark mode */
input, textarea, .stTextInput, .stTextArea, .stDateInput, .stFileUploader, .stDownloadButton, .stButton {
    background-color: #23272f !important;
    color: #ececec !important;
    border: 1px solid #393e46 !important;
}

/* Streamlit spinner and success/info colors for dark mode */
.css-1v0mbdj, .stAlert, .stSpinner {
    background: #23272f !important;
    color: #ececec !important;
}
</style>
""", unsafe_allow_html=True)

# --- Persistent Storage ---
NOTES_FILE = "notes.json"
def load_notes():
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_notes(notes):
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)

notes = load_notes()

# --- Handle Shared Note View ---
shared_note_id = st.query_params.get("note_id", [None])[0]
if shared_note_id:
    shared_note = next((n for n in notes if n.get("id") == shared_note_id), None)
    if shared_note:
        st.title(f"Shared Note: {shared_note['title']}")
        st.markdown(shared_note["content"], unsafe_allow_html=True)
        st.write(f"Tags: {', '.join(shared_note.get("tags", []))}")
        if shared_note.get("checklist"):
            st.write("Checklist:")
            for i, item in enumerate(shared_note["checklist"]):
                st.checkbox(item["text"], value=item["done"], key=f"shared_chk_{i}", disabled=True)
        st.stop() # Stop execution to only show the shared note
    else:
        st.error("Shared note not found.")
        st.stop()

st.title("📝 Notion Minimal")
st.caption("A minimal Notion-like productivity app with AI task suggestions and voice-to-note.")

# Sidebar for navigation
st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["Notes", "AI Task Suggestions", "Voice to Note"])

# Add LinkedIn profile link to the sidebar for professionalism
st.sidebar.markdown("""
### Connect with Me
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue)](https://www.linkedin.com/in/muhammad-atif-latif-13a171318?utm_source=share&utm_campaign=share_via&utm_content=profile&utm_medium=android_app)
""")

# --- Tag Helper ---
def get_all_tags(notes):
    tags = set()
    for n in notes:
        tags.update(n.get("tags", []))
    return sorted(tags)

# --- Notes Page ---
if page == "Notes":
    st.header("Rich Text Notes")
    # Tag selection
    all_tags = get_all_tags(notes)
    selected_tag = st.selectbox("Filter by tag", ["All"] + all_tags)
    filtered_notes = [n for n in notes if selected_tag == "All" or selected_tag in n.get("tags", [])]
    # Search
    search_query = st.text_input("Search notes")
    if search_query:
        filtered_notes = [n for n in filtered_notes if search_query.lower() in n["content"].lower()]
    # List notes
    for idx, note in enumerate(filtered_notes):
        # Ensure note has an ID, assign if missing (for older notes)
        if "id" not in note:
            note["id"] = uuid.uuid4().hex
            save_notes(notes) # Save the updated note with ID

        with st.expander(f"{note['title']} ({note['date']})", expanded=False):
            st.markdown(note["content"], unsafe_allow_html=True)
            st.write(f"Tags: {', '.join(note.get("tags", []))}")
            if note.get("checklist"):
                st.write("Checklist:")
                for i, item in enumerate(note["checklist"]):
                    st.checkbox(item["text"], value=item["done"], key=f"chk_{idx}_{i}", disabled=True)
            col1, col2, col3, col4 = st.columns(4) # Change to 4 columns
            with col1:
                if st.button("Export as Markdown", key=f"md_{idx}", help="Export this note as a Markdown file."):
                    b = BytesIO(note["content"].encode("utf-8"))
                    st.download_button("Download", b, file_name=f"note_{idx}.md", help="Download the note as a Markdown file.")
            with col2:
                if st.button("Export as PDF", key=f"pdf_{idx}", help="Export this note as a PDF file."):
                    try:
                        from fpdf import FPDF
                        pdf = FPDF()
                        pdf.add_page()
                        pdf.set_font("Arial", size=12)
                        pdf.multi_cell(0, 10, note["content"])
                        pdf_bytes = BytesIO()
                        pdf.output(pdf_bytes)
                        st.download_button("Download PDF", pdf_bytes, file_name=f"note_{idx}.pdf", help="Download the note as a PDF file.")
                    except ImportError:
                        st.error("Install fpdf: pip install fpdf")
            with col3:
                share_param = f"?note_id={note['id']}"
                st.write("Share Link:")
                st.markdown(f"""
                <script>
                function copyToClipboard_{idx}() {{
                    const baseUrl = window.location.origin + window.location.pathname;
                    const shareUrl = baseUrl + '{share_param}';
                    navigator.clipboard.writeText(shareUrl).then(() => {{
                        alert('Share link copied to clipboard!');
                    }}).catch(err => {{
                        alert('Failed to copy link: ' + err);
                    }});
                }}
                </script>
                <button onclick="copyToClipboard_{idx}()" aria-label="Copy shareable link for this note" title="Copy shareable link for this note">📋 Copy Share Link</button>
                """, unsafe_allow_html=True)
                st.caption("Copies the full URL for sharing this note.")
            with col4: # Add the delete button in the new 4th column
                if st.button("🗑️ Delete", key=f"del_{idx}", help="Delete this note permanently."):
                    note_id_to_delete = note["id"]
                    notes[:] = [n for n in notes if n.get("id") != note_id_to_delete]
                    save_notes(notes)
                    st.success(f"Note '{note['title']}' deleted.")
                    st.rerun()
    # Add new note
    st.subheader("Add New Note")
    title = st.text_input("Title", key="new_title")
    content = st_quill(key="new_content")
    tags = st.text_input("Tags (comma separated)", key="new_tags")
    checklist_raw = st.text_area("Checklist (one item per line)", key="new_checklist")
    due_date = st.date_input("Due Date", key="new_due")
    if st.button("Save Note", key="save_note_btn"):
        note = {
            "id": uuid.uuid4().hex, # Add unique ID
            "title": title or f"Note {len(notes)+1}",
            "content": content or "",
            "tags": [t.strip() for t in tags.split(",") if t.strip()],
            "checklist": [{"text": t, "done": False} for t in checklist_raw.splitlines() if t.strip()],
            "date": due_date.strftime("%Y-%m-%d") if due_date else datetime.now().strftime("%Y-%m-%d")
        }
        notes.append(note)
        save_notes(notes)
        st.success("Note saved!")
        st.rerun()

# --- Calendar Page ---
if page == "Notes" and notes:
    st.subheader("Calendar View")
    # Show a simple calendar with notes by date
    dates = [n["date"] for n in notes]
    st.write(f"Notes by date: {dict((d, dates.count(d)) for d in set(dates))}")
    # (For demo: show a list, for full calendar use streamlit-calendar or similar)

elif page == "AI Task Suggestions":
    st.header("AI-based Task Suggestions")
    api_key = st.text_input("Enter your Google Gemini API Key", type="password")
    note = st.session_state.get("last_note", "")
    st.write("**Last Note:**", note if note else "No note found. Please add a note first.")
    get_suggestions = st.button("Get Task Suggestions", key="get_suggestions_btn")
    if get_suggestions:
        if not api_key or not note:
            st.warning("Please enter your API key and ensure you have a note saved.")
        else:
            with st.spinner("Getting suggestions from Gemini..."):
                try:
                    # Use the correct Gemini model and endpoint
                    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro:generateContent?key={api_key}"
                    headers = {"Content-Type": "application/json"}
                    prompt = f"Suggest actionable tasks based on this note: {note}"
                    data = {"contents": [{"parts": [{"text": prompt}]}]}
                    response = requests.post(url, headers=headers, json=data)
                    if response.status_code == 200:
                        result = response.json()
                        suggestion = result["candidates"][0]["content"]["parts"][0]["text"]
                        st.success("Task Suggestions:")
                        st.write(suggestion)
                    else:
                        st.error(f"Gemini API error: {response.text}")
                except Exception as e:
                    st.error(f"Error: {e}")

elif page == "Voice to Note":
    st.header("Voice to Note")
    st.caption("Record your voice and get the note as text.")
    audio_file = st.file_uploader("Upload or record your voice note (WAV/MP3)", type=["wav", "mp3"])
    api_key = st.text_input("Enter your Google Cloud Speech-to-Text API Key", type="password")
    transcript = ""
    if st.button("Transcribe Voice Note", key="transcribe_btn"):
        if not audio_file or not api_key:
            st.warning("Please upload an audio file and enter your API key.")
        else:
            with st.spinner("Transcribing..."):
                try:
                    audio_bytes = audio_file.read()
                    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
                    audio_format = "LINEAR16" if audio_file.type == "audio/wav" else "MP3"
                    url = f"https://speech.googleapis.com/v1/speech:recognize?key={api_key}"
                    headers = {"Content-Type": "application/json"}
                    data = {
                        "config": {
                            "encoding": audio_format,
                            "languageCode": "en-US"
                        },
                        "audio": {
                            "content": audio_base64
                        }
                    }
                    response = requests.post(url, headers=headers, json=data)
                    if response.status_code == 200:
                        result = response.json()
                        transcript = result.get("results", [{}])[0].get("alternatives", [{}])[0].get("transcript", "")
                        if transcript:
                            st.success("Transcription:")
                            st.text_area("Voice Note", value=transcript, height=100)
                        else:
                            st.info("No speech detected in the audio.")
                    else:
                        st.error(f"Google Speech-to-Text API error: {response.text}")
                except Exception as e:
                    st.error(f"Error: {e}")
    # Show info if nothing yet
    if not transcript:
        st.info("Your voice note transcription will appear here after you upload and transcribe.")
