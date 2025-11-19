from flask import Flask, render_template, request, redirect, url_for, session, send_file, jsonify
from werkzeug.utils import secure_filename
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import base64
import uuid

app = Flask(__name__)
app.secret_key = os.environ.get("APP_SECRET", "dev-secret-key")

STORAGE_DIR = os.environ.get("STORAGE_DIR", "storage_py")
os.makedirs(STORAGE_DIR, exist_ok=True)

# In-memory repo
users = {}
files = {}
keys = {}

def seed():
    users[str(uuid.uuid4())] = {
        "username": "authority", "password": "password", "type": "AUTHORITY",
        "attributes": "Role:Authority", "active": True
    }
    users[str(uuid.uuid4())] = {
        "username": "owner", "password": "password", "type": "DATA_OWNER",
        "attributes": "Role:Owner,Department:HR", "active": True
    }

seed()


def get_user_by_credentials(username, password):
    uname = (username or "").strip().lower()
    pwd = (password or "").strip()
    for uid, u in users.items():
        if u.get("username", "").lower() == uname and u.get("password", "") == pwd:
            return uid, u
    return None, None


def satisfies_policy(policy, attributes):
    if not policy:
        return True
    if not attributes:
        return False
    parts = [p.strip() for p in policy.split("AND")]
    return all(p in attributes for p in parts)


@app.route("/")
def index():
    return render_template("index.html", role=session.get("role"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", error=request.args.get("error"))
    username = request.form.get("username")
    password = request.form.get("password")
    remember = request.form.get("remember") == "on"

    # naive lockout using session counters
    attempts = session.get("login_attempts", 0)
    if attempts >= 5:
        return redirect(url_for("login", error="Too many attempts. Try again later."))
    uid, user = get_user_by_credentials(username, password)
    if uid and user.get("active"):
        session["user_id"] = uid
        session["role"] = user.get("type")
        session["attributes"] = user.get("attributes")
        session["login_attempts"] = 0
        if remember:
            session.permanent = True
        return redirect(url_for("index"))
    session["login_attempts"] = attempts + 1
    return redirect(url_for("login", error="Invalid credentials"))


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.get("/files")
def list_files():
    return render_template("files.html", files=list(files.values()))


@app.get("/upload")
def upload_page():
    return render_template("upload.html")


@app.post("/upload")
def upload():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    f = request.files.get("file")
    policy = request.form.get("policy", "")
    if not f:
        return redirect(url_for("upload"))
    filename = secure_filename(f.filename)
    data = f.read()

    key = AESGCM.generate_key(bit_length=256)
    aesgcm = AESGCM(key)
    iv = os.urandom(12)
    enc = aesgcm.encrypt(iv, data, None)

    payload = iv + enc
    storage_key = os.path.join(STORAGE_DIR, str(uuid.uuid4()) + "_" + filename)
    with open(storage_key, "wb") as out:
        out.write(payload)

    file_id = str(uuid.uuid4())
    files[file_id] = {
        "file_id": file_id,
        "owner_id": session.get("user_id"),
        "filename": filename,
        "storage_key": storage_key,
        "access_policy": policy
    }
    # Note: in a full system you'd wrap the key via CP-ABE to users' attributes
    keys[file_id] = base64.b64encode(key).decode()
    return redirect(url_for("list_files"))


@app.get("/files/<file_id>/challenge")
def challenge(file_id):
    rec = files.get(file_id)
    if not rec:
        return jsonify({"error": "not_found"}), 404
    return jsonify({
        "id": str(uuid.uuid4()),
        "policy": rec["access_policy"],
        "nonce": str(uuid.uuid4())
    })


@app.get("/files/<file_id>/download")
def download(file_id):
    rec = files.get(file_id)
    if not rec:
        return jsonify({"error": "not_found"}), 404
    attrs = session.get("attributes")
    if not satisfies_policy(rec.get("access_policy"), attrs):
        return jsonify({"error": "forbidden"}), 403
    return send_file(rec["storage_key"], as_attachment=True, download_name=rec["filename"]) 


@app.get("/authority")
def authority_page():
    return render_template("authority.html", users=[{"user_id": uid, **u} for uid, u in users.items()])


@app.post("/authority/issue")
def authority_issue():
    if session.get("role") != "AUTHORITY":
        return redirect(url_for("login"))
    user_id = request.form.get("userId")
    attributes = request.form.get("attributes", "")
    u = users.get(user_id)
    if u:
        u["attributes"] = attributes
        u["active"] = True
    return redirect(url_for("authority_page"))


@app.post("/authority/revoke")
def authority_revoke():
    if session.get("role") != "AUTHORITY":
        return redirect(url_for("login"))
    user_id = request.form.get("userId")
    u = users.get(user_id)
    if u:
        u["active"] = False
    return redirect(url_for("authority_page"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


