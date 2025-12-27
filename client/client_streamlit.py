import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import socket, ssl, os as _os, secrets
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from aes_crypto import encrypt


st.set_page_config(page_title="Secure File Sender", layout="centered")
st.title("🔐 Secure IP File Sharing")

server_ip = st.text_input("Server IP Address")
password = st.text_input("One-Time Password", type="password")
file = st.file_uploader("Choose File")

if st.button("Send File"):
    if not server_ip or not password or not file:
        st.error("Fill all fields")
        st.stop()

    aes_key = secrets.token_bytes(32)

    with open("server/rsa_public.pem", "rb") as f:

        pub_key = serialization.load_pem_public_key(f.read())

    encrypted_key = pub_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    sock = socket.socket()
    s = context.wrap_socket(sock)
    s.connect((server_ip, 9999))

    try:
        s.sendall(password.encode())
        s.sendall(encrypted_key)
        s.sendall(file.name.encode())

        encrypted_data = encrypt(file.read(), aes_key)

        s.sendall(len(encrypted_data).to_bytes(8, "big"))
        s.sendall(encrypted_data)

        st.success(s.recv(1024).decode())

    except Exception as e:
        st.error(f"Transfer failed: {e}")

    finally:
        s.close()
