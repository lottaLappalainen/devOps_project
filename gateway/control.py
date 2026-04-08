#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import subprocess
import urllib.parse
import uuid
import os

HOST = "127.0.0.1"
PORT = 5000

TOKEN_FILE = "/tmp/jwt.token"
SESSION_FILE = "/tmp/session.active"


# ---------------- session + token helpers ------------------

def load_token():
    try:
        with open(TOKEN_FILE, "r") as f:
            tok = f.read().strip()
            return tok if tok else None
    except:
        return None

def save_token(t):
    with open(TOKEN_FILE, "w") as f:
        f.write(t)

def session_active():
    return os.path.exists(SESSION_FILE)

def create_session():
    with open(SESSION_FILE, "w") as f:
        f.write("1")

def clear_session():
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)



# ---------------- HTTP Handler ------------------

class Handler(BaseHTTPRequestHandler):

    # ---------- Handle POST ----------
    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path

        # ---------- ENABLE SESSION AND ISSUE TOKEN ----------
        if path == "/enable":
            # If no session, verify nginx authenticated user via Basic Auth
            if not session_active():
                user = self.headers.get("X-Remote-User", "")
                if not user:
                    self.send_response(401)
                    self.end_headers()
                    self.wfile.write(b"No Basic Auth user")
                    return

                # Basic Auth succeeded → create server-side session
                create_session()

            token = load_token()
            if not token:
                token = str(uuid.uuid4())
                save_token(token)

            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(token.encode())
            return

        # ---------- LOGOUT ----------
        if path == "/logout":
            clear_session()
            save_token("")   # clear token
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Logged out")
            return

        # ---------- switch/discard ----------
        if path in ["/switch", "/discard"]:
            if not session_active():
                self.send_response(401)
                self.end_headers()
                self.wfile.write(b"Not logged in")
                return

            cmd = [path + ".sh"]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out, _ = proc.communicate()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(out)
            return

        self.send_response(404)
        self.end_headers()


    # ---------- VALIDATE JWT FOR PORT 8199 ----------
    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path

        if path == "/validate":
            auth = self.headers.get("Authorization", "")
            stored = load_token()

            # Session active → entire API enabled (assignment requirement)
            if session_active():
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
                return

            # Otherwise, require Bearer token explicitly
            if auth.startswith("Bearer ") and stored and auth.split(" ", 1)[1] == stored:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
                return

            self.send_response(401)
            self.end_headers()
            self.wfile.write(b"Unauthorized")
            return

        # Fallback GET (not used normally)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"control OK")


if __name__ == "__main__":
    save_token("")
    clear_session()
    httpd = HTTPServer((HOST, PORT), Handler)
    httpd.serve_forever()
