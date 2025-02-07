import streamlit as st
import sqlite3
import streamlit_pdf_viewer
import pandas as pd

PASSCODE = 1234

# Database Connection
conn = sqlite3.connect("watcher.db", check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS editions (
          edition_id INTEGER PRIMARY KEY NOT NULL,
          edition TEXT NOT NULL,
          date TEXT NOT NULL,
          path TEXT
          );''')
conn.commit()

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
    c.execute("SELECT date, path FROM editions WHERE edition = ?", (edition,))
    result = c.fetchone()
    return result if result else None

def admin_view():
    editions = c.execute("SELECT edition_id, edition, date, path FROM editions").fetchall()
    if st.button("HOMEPAGE", use_container_width=True):
        st.session_state.admin = 0
        st.rerun()

    with st.expander("New Edition"):
        edition = st.number_input("", label_visibility="collapsed", placeholder="Edition number", value=None)
        date = st.text_input("", label_visibility="collapsed", placeholder="Date")
        path = st.text_input("", label_visibility="collapsed", placeholder="Path i.e. './example.pdf'")
        if st.button("Upload New Edition", type="primary", use_container_width=True):
            if edition and date and path:
                c.execute("INSERT INTO editions (edition, date, path) VALUES (?, ?, ?)", (edition, date, path))
                conn.commit()
                st.cache_data.clear()  # Clear cache to update editions list

    st.subheader("Editions", divider="rainbow")
    df = pd.DataFrame(editions, columns=["Edition ID", "Edition Number", "Date", "File Path"])
    edited_df = st.data_editor(df, key="edition_table", num_rows="fixed", use_container_width=True, hide_index=True)
    if st.button("Update Editions", use_container_width=True):
        for _, row in edited_df.iterrows():
            c.execute("UPDATE OR IGNORE editions SET edition = ?, date = ?, path = ? WHERE edition_id = ?", 
                      (row["Edition Number"], row["Date"], row["File Path"], row["Edition ID"]))
        conn.commit()
        st.cache_data.clear()  # Clear cache to refresh editions
        st.rerun()

def main():
    if st.session_state.admin == 1:
        admin_view()
    else:
        editions = fetch_editions()  # Cached database fetch
        if st.button("Upload - Only for John"):
            access_admin_dialog()
        st.header("📖 Weekly Watcher Viewer", divider="rainbow")
        st.subheader("📚 View an Edition")
        edition = st.selectbox("Select an Edition", options=editions)
        pdf_data = fetch_pdf(edition)  # Cached fetch

        if pdf_data:
            st.subheader(pdf_data[0], divider="rainbow")
            pdf_path = pdf_data[1]
            streamlit_pdf_viewer.pdf_viewer(pdf_path)

if __name__ == "__main__":
    if "admin" not in st.session_state:
        st.session_state.admin = 0
    main()
