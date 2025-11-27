from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import functools # Usaremos para o decorador de admin
from flask import jsonify


# --- Configuração Básica ---
app = Flask(__name__)

# Configuração do banco de dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Use uma chave secreta real e complexa!
app.config['SECRET_KEY'] = 'uma_chave_secreta_muito_longa_e_segura_para_sessions' 

db = SQLAlchemy(app)

# Configuração do upload de arquivos
app.config["UPLOAD_FOLDER"] = "static/uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
PER_PAGE = 5 

# --- Definição dos Modelos do Banco de Dados ---

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False) # Novo campo para distinguir admin

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"User('{self.username}')"

class Imagem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_arquivo = db.Column(db.String(150), nullable=False)
    titulo = db.Column(db.String(100), nullable=False) # NOVO: Campo Titulo
    descricao = db.Column(db.String(300), nullable=False)
    # user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Para saber quem criou

    def __repr__(self):
        return f"Imagem('{self.titulo}', '{self.descricao}')"

# --- Dados de Exemplo para Eventos (Em memória) ---
inscricoes = db.Table('inscricoes',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('evento_id', db.Integer, db.ForeignKey('evento.id'), primary_key=True)
)

class Evento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(300), nullable=False)
    data = db.Column(db.String(50), nullable=False) 
    nome_arquivo = db.Column(db.String(255), nullable=True)

    # Relacionamento com a tabela de inscrições
    participantes = db.relationship('User', secondary=inscricoes, lazy='subquery',
                                    backref=db.backref('eventos_inscritos', lazy=True))

    def __repr__(self):
        return f"Evento('{self.nome}', '{self.data}')"

# --- Rota de Inicialização do Banco de Dados ---
with app.app_context():
    db.create_all() 
    # Adicione eventos de teste se a tabela estiver vazia
    if Evento.query.count() == 0:
        db.session.add(Evento(nome='Trilha Ecológica da Pedra', descricao='Subida moderada de 4h.', data='2025-12-10'))
        db.session.add(Evento(nome='Workshop de Jardins Suspensos', descricao='Aprenda a criar seu jardim.', data='2025-12-15'))
        db.session.commit()
        
# --- FUNÇÃO DECORATOR PARA RESTRINGIR ACESSO ADMIN ---
def admin_required(view_func):
    @functools.wraps(view_func)
    def wrapper(*args, **kwargs):
        # 1. Verifica se o usuário está logado
        if 'user_id' not in session:
            flash("Você precisa estar logado para acessar esta página.", 'warning')
            return redirect(url_for('login'))
        
        # 2. Verifica se o usuário é admin
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash("Acesso negado. Apenas administradores podem acessar.", 'danger')
            return redirect(url_for('index'))
            
        return view_func(*args, **kwargs)
    return wrapper

# --- Rota de Inicialização do Banco de Dados ---
# Rode o app.py UMA VEZ com esta linha descomentada para criar/atualizar o banco de dados
# # Depois, COMENTE-A novamente.
# with app.app_context():
#         db.create_all()
# # #     # Cria um usuário ADMIN padrão na primeira execução (SE NÃO EXISTIR)
#         if not User.query.filter_by(username='admin').first():
#             admin_user = User(username='admin', is_admin=True)
#             admin_user.set_password('admin123') # Troque a senha!
#             db.session.add(admin_user)
#             db.session.commit()

# --- ROTAS DE AUTENTICAÇÃO E REGISTRO ---

# app.py

# ... (Mantenha as importações, modelos e configurações anteriores) ...

# Rotas de Registro e Login unificadas
@app.route("/login", methods=["GET", "POST"])
def login(): # Nome genérico para a função

    if request.method == "POST":
        # Identifica se a requisição veio do formulário de LOGIN ou REGISTRO
        action = request.form.get('action') # Usaremos um campo oculto no HTML para isso

        if action == 'login':
            # --- Lógica de LOGIN ---
            username = request.form.get("login_username")
            password = request.form.get("login_password")
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                session['user_id'] = user.id
                session['is_admin'] = user.is_admin
                flash(f"Login bem-sucedido. Bem-vindo(a) {username}!", 'success')
                return redirect(url_for('admin' if user.is_admin else 'index'))
            else:
                flash("Nome de usuário ou senha inválidos para o login.", 'danger')
        
        elif action == 'registro':
            # --- Lógica de REGISTRO ---
            username = request.form.get("register_username")
            password = request.form.get("register_password")
            
            if User.query.filter_by(username=username).first():
                flash("Este nome de usuário já está em uso para o registro.", 'warning')
            else:
                new_user = User(username=username)
                new_user.set_password(password)
                db.session.add(new_user)
                db.session.commit()
                flash("Cadastro realizado com sucesso! Faça login.", 'success')
                # Opcional: Logar o usuário automaticamente
                # session['user_id'] = new_user.id
                # session['is_admin'] = new_user.is_admin
                
    return render_template("login.html")

# Remove a rota @app.route("/registro") se ela existir

@app.route("/logout")
def logout():
    session.pop('user_id', None)
    session.pop('is_admin', None)
    flash("Você foi desconectado(a).", 'info')
    return redirect(url_for('index'))

# --- ROTAS PRINCIPAIS ---
@app.route("/inscrever/<int:evento_id>", methods=["POST"])
def inscrever_evento(evento_id):
    # Verifica se o usuário está logado
    if 'user_id' not in session:
        flash("Você precisa estar logado para se inscrever.", 'warning')
        return redirect(url_for('autenticacao')) 

    evento = Evento.query.get_or_404(evento_id)
    user = User.query.get(session['user_id'])
    
    # Verifica se já está inscrito
    if user in evento.participantes:
        flash("Você já está inscrito neste evento.", 'info')
    else:
        evento.participantes.append(user)
        db.session.commit()
        flash(f"Inscrição no evento '{evento.nome}' realizada com sucesso!", 'success')
    
    return redirect(url_for('user'))

@app.route("/api/eventos", methods=["GET"])
def listar_eventos_api():
    eventos_db = Evento.query.all()
    # Converte os objetos Evento para uma lista de dicionários
    eventos_json = [
        {
            "id": evento.id,
            "nome": evento.nome,
            "descricao": evento.descricao,
            "data": evento.data,
            "nome_arquivo": evento.nome_arquivo,
            # Retorna apenas a contagem de participantes para o usuário
            "inscritos_count": len(evento.participantes), 
        } 
        for evento in eventos_db
    ]
    return jsonify(eventos_json)
@app.route("/user")
def user():
    return render_template("user.html")

@app.route("/")
def index():
    imagens = Imagem.query.all() # Ou paginar aqui também, se necessário
    eventos = Evento.query.all()
    return render_template("index.html", imagens=imagens, eventos=eventos)

# --- ROTAS DE ADMINISTRAÇÃO (AGORA PROTEGIDAS) ---

@app.route("/admin")
@admin_required # PROTEÇÃO: APENAS ADMIN PODE ACESSAR
def admin():
    page = request.args.get('page', 1, type=int)
    imagens_paginadas = Imagem.query.paginate(page=page, per_page=PER_PAGE, error_out=False)
    
    eventos = Evento.query.all()


    return render_template(
        "admin.html", 
        imagens=imagens_paginadas,
        eventos=eventos
    )



# ... (Dentro da seção de ROTAS DE ADMINISTRAÇÃO PROTEGIDAS) ...

# 4. CRIAR Evento
@app.route("/admin/criar_evento", methods=["POST"])
@admin_required
def criar_evento():
    nome = request.form.get("nome")
    descricao = request.form.get("descricao")
    data = request.form.get("data") # Novo campo para a data/hora
    arquivo = request.files.get("imagem")
    nome_arquivo = None
    if arquivo and arquivo.filename:
        # 1. Salva o arquivo no disco (pasta static/uploads)
        nome_seguro = secure_filename(arquivo.filename)
        caminho = os.path.join(app.config["UPLOAD_FOLDER"], nome_seguro)
        arquivo.save(caminho)
        
        # 2. Armazena o nome do arquivo para o DB
        nome_arquivo = nome_seguro

    novo_evento = Evento(
        nome=nome, 
        descricao=descricao, 
        data=data,
        nome_arquivo=nome_arquivo)
    db.session.add(novo_evento)
    db.session.commit()
    flash("Evento criado com sucesso!", 'success')
    return redirect(url_for("admin"))

# 5. APAGAR Evento
@app.route("/admin/apagar_evento/<int:evento_id>", methods=["POST"])
@admin_required
def apagar_evento(evento_id):
    evento_para_apagar = Evento.query.get_or_404(evento_id)
    db.session.delete(evento_para_apagar)
    db.session.commit()
    flash("Evento apagado com sucesso!", 'success')
    return redirect(url_for("admin"))



# # 2. EDITAR (GET e POST) - Com Titulo e Descricao separados
# @app.route("/admin/editar_imagem/<int:img_id>", methods=["GET", "POST"])
# @admin_required # PROTEÇÃO: APENAS ADMIN PODE USAR
# # 6. EDITAR Evento - Rota GET (Para exibir o formulário)
# @app.route("/admin/editar_evento/<int:evento_id>", methods=["GET"])
# @admin_required
# def editar_evento(evento_id):
#     evento_para_editar = Evento.query.get_or_404(evento_id)
#     return render_template("editar_evento.html", evento=evento_para_editar)


# 7. EDITAR Evento - Rota POST (Para processar o envio)
@app.route("/admin/editar_evento/<int:evento_id>", methods=["POST"])
@admin_required
def processar_edicao_evento(evento_id):
    evento_para_editar = Evento.query.get_or_404(evento_id)
    
    # 1. Atualiza os campos de texto
    evento_para_editar.nome = request.form.get("nome")
    evento_para_editar.descricao = request.form.get("descricao")
    evento_para_editar.data = request.form.get("data")
    
    # 2. Processa o novo arquivo de imagem (se houver)
    novo_arquivo = request.files.get("imagem")

    if novo_arquivo and novo_arquivo.filename:
        # Verifica e apaga o arquivo antigo, se existir
        if evento_para_editar.nome_arquivo:
            caminho_antigo = os.path.join(app.config["UPLOAD_FOLDER"], evento_para_editar.nome_arquivo)
            if os.path.exists(caminho_antigo):
                os.remove(caminho_antigo)
        
        # Salva o novo arquivo
        nome_seguro = secure_filename(novo_arquivo.filename)
        caminho_novo = os.path.join(app.config["UPLOAD_FOLDER"], nome_seguro)
        novo_arquivo.save(caminho_novo)
        
        # Atualiza o nome no banco de dados
        evento_para_editar.nome_arquivo = nome_seguro
        
    # 3. Commit e Redirecionamento
    db.session.commit() 
    flash("Evento editado com sucesso!", 'success')
    return redirect(url_for("admin"))

# 3. APAGAR Imagem (POST)
@app.route("/admin/apagar_imagem/<int:img_id>", methods=["POST"])
@admin_required # PROTEÇÃO: APENAS ADMIN PODE USAR
def apagar_imagem(img_id):
    imagem_para_apagar = Imagem.query.get_or_404(img_id)
    
    # 1. Apaga o arquivo do disco
    caminho_arquivo = os.path.join(app.config["UPLOAD_FOLDER"], imagem_para_apagar.nome_arquivo)
    if os.path.exists(caminho_arquivo):
        os.remove(caminho_arquivo)
    
    # 2. Apaga o registro do banco de dados
    db.session.delete(imagem_para_apagar)
    db.session.commit()
    
    return redirect(url_for("admin"))

# ... (outras rotas de evento/inscrição) ...

if __name__ == "__main__":
    app.run(debug=True)