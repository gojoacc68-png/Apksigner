import os, subprocess, tempfile, secrets, threading
from flask import Flask, send_file, jsonify

app = Flask(__name__)

BASE_APK = "/app/base.apk"
BUILD_TOOLS = "/opt/build-tools"
COUNTER_FILE = "/data/counter.txt"   # /data is a Fly persistent volume
_lock = threading.Lock()

def bump_counter():
    with _lock:
        n = 0
        if os.path.exists(COUNTER_FILE):
            n = int(open(COUNTER_FILE).read() or "0")
        n += 1
        os.makedirs(os.path.dirname(COUNTER_FILE), exist_ok=True)
        open(COUNTER_FILE, "w").write(str(n))
        return n

@app.route("/count")
def count():
    n = int(open(COUNTER_FILE).read()) if os.path.exists(COUNTER_FILE) else 0
    return jsonify(downloads=n)

@app.route("/download")
def download():
    n = bump_counter()
    work = tempfile.mkdtemp()
    ks = os.path.join(work, "tmp.jks")
    out = os.path.join(work, "signed.apk")
    pw = secrets.token_hex(12)

    # 1. random keystore
    subprocess.run([
        "keytool", "-genkeypair", "-keystore", ks, "-alias", "k",
        "-keyalg", "RSA", "-keysize", "2048", "-validity", "365",
        "-storepass", pw, "-keypass", pw,
        "-dname", f"CN=app{secrets.token_hex(4)}"
    ], check=True, capture_output=True)

    # 2. align then sign
    aligned = os.path.join(work, "aligned.apk")
    subprocess.run([f"{BUILD_TOOLS}/zipalign", "-f", "4", BASE_APK, aligned],
                   check=True, capture_output=True)
    subprocess.run([
        f"{BUILD_TOOLS}/apksigner", "sign",
        "--ks", ks, "--ks-pass", f"pass:{pw}", "--key-pass", f"pass:{pw}",
        "--out", out, aligned
    ], check=True, capture_output=True)

    return send_file(out, as_attachment=True, download_name="app.apk",
                     mimetype="application/vnd.android.package-archive")

@app.route("/")
def health():
    return "ok"
