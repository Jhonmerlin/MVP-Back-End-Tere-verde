from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
from werkzeug.utils import secure_filename
import jwt
from functools import wraps
from datetime import datetime, timedelta, timezone

# ---------- CONFIG ----------
SECRET_KEY = "muda_essa_chave_para_algo_secreto"  # troque em produção
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASS = "1234"

app = Flask(__name__, static_folder="static")
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DB_PATH = os.path.join(BASE_DIR, "database.db")


# ---------- DB helpers ----------
def connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            role TEXT DEFAULT 'user'
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS trilhas(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            image TEXT
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS trilha_inscritos(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trilha_id INTEGER,
            user_id INTEGER,
            created_at TEXT
        );
    """)
    conn.commit()
    conn.close()


init_db()


# ---------- JWT helpers ----------
def generate_token(user_id, role, expires_minutes=120):
    current_time = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "exp": current_time + timedelta(minutes=expires_minutes),
        "iat": current_time
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def decode_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except Exception:
        return None


def token_required(role_required=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            auth = request.headers.get("Authorization", None)
            print("AUTH HEADER RECEBIDO:", auth)

            if not auth:
                return jsonify({"error": "Token ausente"}), 401

            try:
                token = auth.replace("Bearer ", "")
                payload = decode_token(token)

                if not payload:
                    return jsonify({"error": "Token inválido ou expirado"}), 401

                if role_required and payload.get("role") != role_required:
                    return jsonify({"error": "Permissão negada"}), 403

                request.user_id = payload.get("sub")
                request.user_role = payload.get("role")

            except Exception as e:
                print("ERRO NO TOKEN:", e)
                return jsonify({"error": "Token inválido"}), 401

            return f(*args, **kwargs)
        return wrapper
    return decorator


# ---------- ROTAS ----------

@app.route("/")
def home():
    return jsonify({"message": "API rodando!"})


# --- LOGIN ADMIN / USER ---
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    # Login do admin fixo
    if email == ADMIN_EMAIL and password == ADMIN_PASS:
        token = generate_token(0, "admin")
        return jsonify({"token": token, "role": "admin"})

    conn = connection()
    cur = conn.cursor()
    cur.execute("SELECT id, password, role FROM users WHERE email=?", (email,))
    user = cur.fetchone()
    conn.close()

    if not user or user[1] != password:
        return jsonify({"error": "Credenciais inválidas"}), 401

    token = generate_token(user[0], user[2])
    return jsonify({"token": token, "role": user[2]})


# --- REGISTRO DE USUÁRIO ---
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    conn = connection()
    cur = conn.cursor()

    try:
        cur.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                    (name, email, password))
        conn.commit()
        conn.close()
        return jsonify({"message": "Usuário registrado com sucesso"})
    except:
        return jsonify({"error": "Email já registrado"}), 400


# --- CRIAR TRILHA ---
@app.route("/trilhas", methods=["POST"])
@token_required(role_required="admin")
def create_trilha():
    title = request.form.get("title")
    description = request.form.get("description")
    image = request.files.get("image")

    filename = None
    if image:
        filename = secure_filename(image.filename)
        image.save(os.path.join(UPLOAD_FOLDER, filename))

    conn = connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO trilhas (title, description, image)
        VALUES (?, ?, ?)
    """, (title, description, filename))
    conn.commit()
    conn.close()

    return jsonify({"message": "Trilha criada com sucesso"})


# --- LISTAR TRILHAS ---
@app.route("/trilhas", methods=["GET"])
def list_trilhas():
    conn = connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM trilhas")
    rows = cur.fetchall()
    conn.close()

    trilhas = []
    for r in rows:
        trilhas.append({
            "id": r[0],
            "title": r[1],
            "description": r[2],
            "image": r[3]
        })

    return jsonify(trilhas)


# --- EDITAR TRILHA ---
@app.route("/trilhas/<int:id>", methods=["PUT"])
@token_required(role_required="admin")
def update_trilha(id):
    data = request.json
    title = data.get("title")
    description = data.get("description")

    conn = connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE trilhas SET title=?, description=? WHERE id=?
    """, (title, description, id))
    conn.commit()
    conn.close()

    return jsonify({"message": "Trilha atualizada"})


# --- DELETAR TRILHA ---
@app.route("/trilhas/<int:id>", methods=["DELETE"])
@token_required(role_required="admin")
def delete_trilha(id):
    conn = connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM trilhas WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Trilha removida"})


# --- INSCREVER EM TRILHA ---
@app.route("/trilhas/<int:trilha_id>/inscrever", methods=["POST"])
@token_required()
def inscrever(trilha_id):
    user_id = request.user_id

    conn = connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO trilha_inscritos (trilha_id, user_id, created_at)
        VALUES (?, ?, ?)
    """, (trilha_id, user_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()

    return jsonify({"message": "Inscrição realizada com sucesso"})


# --- SERVE IMAGENS ---
@app.route("/uploads/<path:filename>")
def serve_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)
