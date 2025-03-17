import streamlit as st
import sqlite3
import streamlit_pdf_viewer
import pandas as pd
import random
import time
import os
import json

PASSCODE = "01012024"

conn = sqlite3.connect("watcher.db", check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS editions (
                edition_id INTEGER NOT NULL,
                edition TEXT NOT NULL,
                date TEXT NOT NULL,
                path TEXT
                );''')
conn.commit()

def load_editions_from_json():
    if os.path.exists("./editions.json"):
        with open("./editions.json", "r") as f:
            try:
                editions_data = json.load(f)
            except Exception as e:
                st.error(f"Error loading JSON: {e}")
                return
        # Iterate over each edition in the JSON file
        for edition in editions_data:
            edition_id = edition.get("edition_id")
            edition_number = edition.get("edition_number")
            date = edition.get("date")
            file_path = edition.get("file_path")
            # Check if this edition already exists in the database
            c.execute("SELECT path FROM editions WHERE edition_id = ?", (edition_id,))
            result = c.fetchone()
            if result:
                # If file path is absent or empty, update it from JSON data
                if not result[0]:
                    c.execute("UPDATE editions SET path = ? WHERE edition_id = ?", (file_path, edition_id))
            else:
                # Insert the edition if it doesn't exist
                c.execute("INSERT INTO editions (edition_id, edition, date, path) VALUES (?, ?, ?, ?)",
                          (edition_id, edition_number, date, file_path))
        conn.commit()

# Ensure JSON is loaded only once per session
if "json_loaded" not in st.session_state:
    load_editions_from_json()
    st.session_state.json_loaded = True

@st.dialog("Admin")
def access_admin_dialog():
    guess = st.text_input("", label_visibility="collapsed", placeholder="Enter password")
    if st.button("Enter", use_container_width=True):
        if guess == str(PASSCODE):
            st.session_state.admin = 1
            st.rerun()

@st.cache_data
def fetch_editions():
    c.execute("SELECT edition FROM editions")
    return [row[0] for row in c.fetchall()]

@st.cache_resource
def fetch_pdf(edition):
    c.execute("SELECT edition, date, path FROM editions WHERE edition = ?", (edition,))
    result = c.fetchone()
    return result if result else None

def admin_view():
    editions = c.execute("SELECT edition_id, edition, date, path FROM editions").fetchall()
    if st.button("HOME", use_container_width=True):
        st.session_state.admin = 0
        st.session_state.section = "home"
        st.rerun()

    c1, c2 = st.columns(2)
    with c1:
        with st.container():
            edition = st.text_input("", label_visibility="collapsed", placeholder="Edition number")
            date = st.text_input("", label_visibility="collapsed", placeholder="Date")
            uploaded_file = st.file_uploader("Upload PDF", type="pdf")
            if st.button("Upload New Edition", type="primary", use_container_width=True):
                with st.spinner("Uploading..."):
                    if edition and date and uploaded_file:
                        # Save the uploaded file to the current working directory
                        file_path = os.path.join(os.getcwd(), uploaded_file.name)
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        # Generate a random edition_id
                        edition_id = random.randint(100000, 999999)
                        # Insert into the database
                        c.execute("INSERT INTO editions (edition_id, edition, date, path) VALUES (?, ?, ?, ?)",
                                  (edition_id, edition, date, file_path))
                        conn.commit()
                        st.cache_data.clear()

                        # Update or create the editions.json file
                        if os.path.exists("./editions.json"):
                            try:
                                with open("./editions.json", "r") as json_file:
                                    editions_json = json.load(json_file)
                            except Exception as e:
                                st.error(f"Error reading ./editions.json: {e}")
                                editions_json = []
                        else:
                            editions_json = []
                        # Append the new edition
                        new_record = {
                            "edition_id": edition_id,
                            "edition_number": edition,
                            "date": date,
                            "file_path": file_path
                        }
                        editions_json.append(new_record)
                        with open("./editions.json", "w") as json_file:
                            json.dump(editions_json, json_file, indent=4)
                    time.sleep(2)
                st.rerun()

    with c2:
        df = pd.DataFrame(editions, columns=["Edition ID", "Edition Number", "Date", "File Path"])
        edited_df = st.data_editor(df, key="edition_table", num_rows="fixed", use_container_width=True, hide_index=True)
        if st.button("Update Editions", use_container_width=True):
            for _, row in edited_df.iterrows():
                c.execute("UPDATE OR IGNORE editions SET edition = ?, date = ?, path = ? WHERE edition_id = ?", 
                          (row["Edition Number"], row["Date"], row["File Path"], row["Edition ID"]))
            conn.commit()
            st.cache_data.clear()
            st.rerun()

        edition_id_to_delete = st.text_input("", label_visibility="collapsed", placeholder="Edition ID to Delete")
        if st.button("Delete Edition", use_container_width=True):
            c.execute("DELETE FROM editions WHERE edition_id = ?", (edition_id_to_delete,))
            conn.commit()
            st.rerun()

def main():
    st.set_page_config(
        page_title="Watcher Viewer",
        page_icon="📜",
        layout="centered" if st.session_state.section == "home" else "wide",
    )

    st.markdown(
    """
    <style>
        * {
            font-family: 'Times New Roman', Times, serif;
        }
        .t {
            font-family: 'Times New Roman', Times, serif;
        }
    </style>
    """,
    unsafe_allow_html=True
    )
    editions = fetch_editions()
    if st.session_state.admin == 1:
        admin_view()
    else:
        st.header("📖 Weekly Watcher Viewer", divider="gray")
        st.write("View an Edition")
        c1, c2 = st.columns([5, 2])
        edition = c1.selectbox("", label_visibility="collapsed", options=editions)
        pdf_data = fetch_pdf(edition)
        if c2.button("Add New", icon=":material/add:", use_container_width=True, type="secondary"):
            st.session_state.section = "admin"
            access_admin_dialog()
    
        if pdf_data:
            st.text("")
            st.text("")
            st.subheader(f":blue[{pdf_data[0]}:] {pdf_data[1]}", divider="gray")
            streamlit_pdf_viewer.pdf_viewer(pdf_data[2], render_text=True, height=2000)
        else:
            st.warning("⚠️ No PDF available for this edition.")

if __name__ == "__main__":
    if "admin" not in st.session_state:
        st.session_state.admin = 0
    if "section" not in st.session_state:
        st.session_state.section = "home"
    main()
