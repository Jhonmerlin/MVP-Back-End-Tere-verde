# Requisitos do sistema

https://docs.google.com/spreadsheets/d/1HoebeT2iS1RBxs65d2klnQbZbcWsvxVICNMHOKAE7xY/edit?usp=sharing

# Autores

- Jonathan bandeira barboza
- Wallace dos santos Pinto

# 🚀 Gerenciador de Trilhas e Eventos

Este projeto é uma plataforma para auxiliar o agendamento de trilhas em Teresópolis, permitindo a visualização de trilhas/cursos e a inscrição em eventos.

# 🛠️ Tecnologias Utilizadas
O projeto utiliza uma arquitetura simples com Python no backend e JavaScript/HTML/CSS no frontend.

Backend: Python 🐍

Framework: Flask (para rotas e servidor web)

ORM/DB: Flask-SQLAlchemy (para gerenciar o banco de dados SQLite)

Frontend: HTML5, CSS3, JavaScript (para interações dinâmicas e consumo da API)

Banco de Dados: SQLite (banco de dados leve e embutido)

## 📦 O que é Necessário para Rodar a Aplicação
Para executar o projeto, você precisará ter o Python 3 instalado e as bibliotecas listadas abaixo.

1. Criar o Ambiente Virtual (Recomendado)
Crie um ambiente virtual para isolar as dependências do projeto:

Bash

python -m venv venv
2. Ativar o Ambiente
Windows:

Bash

.\venv\Scripts\activate
macOS / Linux:

Bash

source venv/bin/activate
3. Instalar as Dependências as seguintes bibliotecas que são usadas no arquivo app.py:

Plaintext
Flask
Flask-SQLAlchemy
Werkzeug

Em seguida, instale-as usando o pip:

Bash

pip install -r requirements.txt

▶️ Como Usar a Plataforma
Siga os passos abaixo para iniciar e interagir com a aplicação.

# 1. Iniciar o Servidor
Após instalar as dependências e ativar o ambiente virtual, inicie o servidor Flask:

Bash

python app.py
## O servidor será iniciado em modo de desenvolvimento (por padrão, em http://127.0.0.1:5000/).

### 2. Acesso e Funcionalidades
Acesse o endereço principal no seu navegador (http://127.0.0.1:5000/).

###  👩‍💻 Área do Usuário (Participante)
Cadastro/Login: Vá para a rota /login para criar uma conta ou fazer login.

O usuário deverá se cadastrar para participar das trilhas/eventos.

Poderá criar uma conta para se inscrever nos eventos.

Visualização de Trilhas: A página principal (index) e a rota /user listam os eventos/trilhas disponíveis.

A lista de trilhas é carregada via API usando o script java.js.

Inscrição: O usuário pode se inscrever nas trilhas/eventos através do botão na interface, o que dispara uma requisição POST para a rota /inscrever/<id>.

### 👑 Área do Administrador

Login Separado: O administrador tem uma tela de login unificada com o usuário, mas o login bem-sucedido direciona para a área de admin.

Acesso Inicial: Se não houver usuários, crie um usuário, defina-o manualmente como is_admin=True no banco de dados e reinicie o servidor. Se o seu código de exemplo for descomentado, ele criará um admin padrão.


Acesso Restrito: Não será possível acessar a área /admin sem estar logado e ter o status de administrador, devido ao decorator @admin_required.

### Gerenciamento (CRUD): A área /admin permite:

CRUD de Trilhas/Módulos/Conteúdos: O administrador deve ter uma interface para Criar, Ler, Atualizar e Deletar (CRUD) trilhas, módulos e conteúdos.

Gerenciamento de Eventos: Criar, editar e apagar eventos.

Gerenciamento de Imagens: Upload e exclusão de imagens (para as trilhas).
