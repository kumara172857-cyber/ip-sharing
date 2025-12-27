import streamlit as st
import json
import os
import time

# ===============================
# PATH CONFIG (ROOT-LEVEL)
# ===============================
STATE_FILE = "state.json"
RECEIVED_DIR = "received_files"

st.set_page_config(
    page_title="Secure File Receiver",
    layout="centered"
)

st.title("🔐 Secure File Receiver")

# ===============================
# HELPERS
# ===============================
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return None

def get_received_files():
    if os.path.exists(RECEIVED_DIR):
        return os.listdir(RECEIVED_DIR)
    return []

# ===============================
# UI LOOP
# ===============================
placeholder = st.empty()

while True:
    state = load_state()

    with placeholder.container():
        if not state:
            st.warning("Waiting for server to start...")
        else:
            # -------- SERVER RUNNING --------
            if state["status"] == "running":
                st.success("🟢 Server is running")
                st.subheader("🔑 One-Time Password")
                st.code(state["password"], language="text")

            # -------- FILE RECEIVED --------
            else:
                st.error("🔴 Server stopped")
                st.success("✅ File received successfully")

                if st.button("📂 Show Files"):
                    files = get_received_files()

                    if not files:
                        st.warning("No files found")
                    else:
                        st.subheader("📄 Received Files")

                        for file in files:
                            file_path = os.path.join(RECEIVED_DIR, file)

                            # Safe binary read
                            with open(file_path, "rb") as f:
                                file_bytes = f.read()

                            st.markdown(f"**{file}**")
                            st.download_button(
                                label="⬇ Download",
                                data=file_bytes,
                                file_name=file,
                                mime="application/octet-stream"
                            )

                break  # stop refresh loop after file received

    time.sleep(1)
