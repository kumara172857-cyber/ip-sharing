import socket, ssl, threading, os, secrets, string, json, subprocess, sys
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from aes_crypto import decrypt

PORT = 9999
STATE_FILE = "state.json"
server_running = True

def generate_password(length=5):
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

PASSWORD = generate_password()

with open(STATE_FILE, "w") as f:
    json.dump({
        "status": "running",
        "password": PASSWORD,
        "file_received": False,
        "filename": ""
    }, f)

subprocess.Popen([sys.executable, "-m", "streamlit", "run", "server/dashboard.py"])

os.makedirs("received_files", exist_ok=True)

with open("server/rsa_private.pem", "rb") as f:
    private_key = serialization.load_pem_private_key(f.read(), password=None)

context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain("server/server.crt", "server/server.key")

def handle_client(conn):
    global server_running
    try:
        if conn.recv(1024).decode().strip() != PASSWORD:
            return

        encrypted_key = conn.recv(256)
        aes_key = private_key.decrypt(
            encrypted_key,
            padding.OAEP(
                mgf=padding.MGF1(hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        filename = conn.recv(1024).decode()
        file_size = int.from_bytes(conn.recv(8), "big")

        encrypted_data = b""
        while len(encrypted_data) < file_size:
            encrypted_data += conn.recv(4096)

        decrypted_data = decrypt(encrypted_data, aes_key)

        with open(f"received_files/{filename}", "wb") as f:
            f.write(decrypted_data)

        conn.send(b"Secure file received successfully")

        with open(STATE_FILE, "w") as f:
            json.dump({
                "status": "stopped",
                "password": PASSWORD,
                "file_received": True,
                "filename": filename
            }, f)

        server_running = False

    finally:
        conn.close()

sock = socket.socket()
sock.bind(("0.0.0.0", PORT))
sock.listen(1)

while server_running:
    conn, _ = sock.accept()
    secure = context.wrap_socket(conn, server_side=True)
    threading.Thread(target=handle_client, args=(secure,), daemon=True).start()

sock.close()
