# app.py
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
from werkzeug.utils import secure_filename
import jwt
from functools import wraps
from datetime import datetime, timedelta

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
def generate_token(user_id, role, expires_minutes=60):
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=expires_minutes)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def decode_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except Exception as e:
        return None

def token_required(role_required=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            auth = request.headers.get("Authorization", None)
            print("AUTH HEADER RECEBIDO:", auth)  # DEBUG AQUI

            if not auth:
                return jsonify({"error":"Token ausente"}), 401
            parts = auth.split()
            if len(parts) != 2 or parts[0].lower() != "bearer":
                return jsonify({"error":"Header Authorization inválido"}), 401
            token = parts[1]
            payload = decode_token(token)
            if payload is None:
                return jsonify({"error":"Token inválido ou expirado"}), 401
            if role_required and payload.get("role") != role_required:
                return jsonify({"error":"Permissão negada"}), 403
            # attach user info to request
            request.user = {"id": payload.get("sub"), "role": payload.get("role")}
            
            return f(*args, **kwargs)
        return wrapper
    return decorator

# ---------- Routes: Auth ----------
@app.route("/login", methods=["POST"])
def login():
    data = request.json or {}
    email = data.get("email")
    password = data.get("password")

    if email == ADMIN_EMAIL and password == ADMIN_PASS:
        token = generate_token(1, "admin")
        return jsonify({"role": "admin", "message": "Login efetuado", "token": token})

    conn = connection()
    cur = conn.cursor()
    cur.execute("SELECT id, role FROM users WHERE email=? AND password=?", (email, password))
    row = cur.fetchone()
    conn.close()

    if not row:
        return jsonify({"error":"Credenciais inválidas"}), 401

    user_id, role = row
    token = generate_token(user_id, role)
    return jsonify({"role": role, "message": "Login efetuado", "token": token})


# endpoint para cadastro (usa o mesmo de antes, mas agora grava role 'user')
@app.route("/register", methods=["POST"])
def register():
    data = request.json or {}
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    if not name or not email or not password:
        return jsonify({"error":"name, email e password obrigatórios"}), 400

    conn = connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                    (name, email, password, "user"))
        conn.commit()
        user_id = cur.lastrowid
        token = generate_token(user_id=user_id, role="user", expires_minutes=120)
        return jsonify({"msg":"Usuário criado", "token": token})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

# ---------- CRUD de trilhas (admin) ----------
@app.route("/trilhas", methods=["POST"])
@token_required(role_required="admin")
def add_trilha():
    title = request.form.get("title")
    description = request.form.get("description")
    image = request.files.get("image")

    filename = None
    if image:
        safe_name = secure_filename(image.filename)
        filename = os.path.join(UPLOAD_FOLDER, safe_name)
        image.save(filename)

    conn = connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO trilhas (title, description, image) VALUES (?, ?, ?)",
                (title, description, filename))
    conn.commit()
    conn.close()
    return jsonify({"msg":"Trilha criada"})

@app.route("/trilhas", methods=["GET"])
@token_required()  # qualquer token válido (user ou admin) consegue listar
def get_trilhas():
    conn = connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, description, image FROM trilhas")
    data = cur.fetchall()
    conn.close()
    trilhas = []
    for t in data:
        trilhas.append({
            "id": t[0],
            "title": t[1],
            "description": t[2],
            "image": t[3]  # caminho absoluto salvo; o front pode exibir usando /uploads route abaixo
        })
    return jsonify(trilhas)

@app.route("/trilhas/<int:id>", methods=["PUT"])
@token_required(role_required="admin")
def update_trilha(id):
    title = request.form.get("title")
    description = request.form.get("description")
    image = request.files.get("image")

    conn = connection()
    cur = conn.cursor()
    if image:
        safe_name = secure_filename(image.filename)
        filename = os.path.join(UPLOAD_FOLDER, safe_name)
        image.save(filename)
        cur.execute("UPDATE trilhas SET title=?, description=?, image=? WHERE id=?",
                    (title, description, filename, id))
    else:
        cur.execute("UPDATE trilhas SET title=?, description=? WHERE id=?", (title, description, id))
    conn.commit()
    conn.close()
    return jsonify({"msg":"Trilha atualizada"})

@app.route("/trilhas/<int:id>", methods=["DELETE"])
@token_required(role_required="admin")
def delete_trilha(id):
    conn = connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM trilhas WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"msg":"Trilha apagada"})

# ---------- Inscrição em trilha (usuário) ----------
@app.route("/trilhas/<int:trilha_id>/inscrever", methods=["POST"])
@token_required(role_required=None)  # qualquer user autenticado pode se inscrever
def inscrever_trilha(trilha_id):
    user = getattr(request, "user", None)
    if not user:
        return jsonify({"error":"User not found in token"}), 401
    user_id = user["id"]
    # se token de admin (user_id 0), proibimos inscrever-se como admin
    if user["role"] == "admin":
        return jsonify({"error":"Admin não pode se inscrever"}), 403

    conn = connection()
    cur = conn.cursor()
    # opcional: verificar se trilha existe
    cur.execute("SELECT id FROM trilhas WHERE id=?", (trilha_id,))
    if not cur.fetchone():
        conn.close()
        return jsonify({"error":"Trilha não existe"}), 404

    cur.execute("INSERT INTO trilha_inscritos (trilha_id, user_id, created_at) VALUES (?, ?, ?)",
                (trilha_id, user_id, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({"msg":"Inscrição realizada"})

# ---------- Servir imagens (rota simples) ----------
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    # serve arquivos da pasta uploads relative ao BASE_DIR/static/uploads
    return send_from_directory(UPLOAD_FOLDER, filename)

# ---------- Rodar ----------
if __name__ == "__main__":
    print("UPLOAD_FOLDER está apontando para:", UPLOAD_FOLDER)
    app.run(debug=True)
