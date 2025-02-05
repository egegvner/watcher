import streamlit as st
import base64
import sqlite3
import streamlit_pdf_viewer
import time

PASSCODE = 1234

conn = sqlite3.connect("watcher.db", check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS editions (
          edition TEXT NOT NULL PRIMARY KEY,
          date TEXT NOT NULL,
          file_data BLOB 
          );''')
conn.commit()

@st.dialog(" ")
def access_admin_dialog():

    st.subheader("📤 Upload a New PDF Edition", divider="rainbow")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    edition_number = st.text_input("Enter Edition Number")
    date = st.text_input("Enter Date i.e. '1 Jan 2025'")

    if st.button("Upload", use_container_width=True):
        if uploaded_file and edition_number and date:
            pdf_data = uploaded_file.read()
            c.execute("INSERT INTO editions (edition, date, file_data) VALUES (?, ?, ?)", (edition_number, date, pdf_data))
            conn.commit()
            st.success(f"✅ Edition {edition_number} has been successfully uploaded!")
            time.sleep(2)
            st.rerun()
        else:
            st.warning("⚠️ Please select a PDF and enter an edition number.")

def fetch_pdf(edition):
    c.execute("SELECT date, file_data FROM editions WHERE edition = ?", (edition,))
    result = c.fetchone()
    return result if result else None

c.execute("SELECT edition FROM editions")
editions = [row[0] for row in c.fetchall()]

if st.button("Upload - Only for John"):
    access_admin_dialog()

def main():
    st.header("📖 Weekly Watcher Viewer", divider="rainbow")
    st.subheader("📚 View an Edition")
    edition = st.selectbox("Select an Edition", options=editions)
    pdf_data = fetch_pdf(edition)

    st.subheader(pdf_data[0], divider="rainbow")
    with st.container(border=True):
        if pdf_data:
            streamlit_pdf_viewer.pdf_viewer(pdf_data[1], render_text=True)
        else:
            st.warning("⚠️ No PDF available for this edition.")

if __name__ == "__main__":
    main()
