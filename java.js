const API = "http://127.0.0.1:5000";

alert("java.js carregou!");

// =================== UTIL E AUTENTICAÇÃO =======================

function saveToken(token) { localStorage.setItem("token", token); }
function getToken() { return localStorage.getItem("token"); }
function saveRole(role) { localStorage.setItem("role", role); }
function getRole() { return localStorage.getItem("role"); }

function authHeaders() {
    const t = getToken();
    if (!t) return { "Content-Type": "application/json" };
    
    // Retorna o Content-Type e o cabeçalho de Autorização
    return { 
        "Authorization": "Bearer " + t,
        "Content-Type": "application/json"
    };
}

// =================== VERIFICAÇÃO DE AUTENTICAÇÃO (CLIENTE) ✅ ====================
function checkAuth() {
    const token = getToken();
    
    // Se não há token, redireciona imediatamente para o login
    if (!token) {
        alert("Você precisa estar logado para acessar esta página.");
        window.location.href = "index.html";
        return false; // Indica falha na autenticação
    }
    
    // Se há token, permite a continuação
    return true; 
}

// =================== LOGIN ✅ ========================
async function login() {
    const email = document.querySelector("#email").value;
    const password = document.querySelector("#password").value;

    const res = await fetch(API + "/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
    });

    // 🛑 VERIFICAÇÃO DE STATUS
    if (!res.ok) {
        const errorData = await res.json();
        const errorMessage = errorData.error || "Credenciais inválidas. Tente novamente.";
        return alert(errorMessage);
    }

    const data = await res.json();
    if (data.error) return alert(data.error); 

    saveToken(data.token);
    saveRole(data.role);

    if (data.role === "admin") window.location.href = "admin.html";
    else window.location.href = "user.html";
}

// =================== CADASTRO ✅ ========================
async function register() {
    const name = document.querySelector("#reg-name").value;
    const email = document.querySelector("#reg-email").value;
    const password = document.querySelector("#reg-pass").value;

    const res = await fetch(API + "/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password })
    });

    const data = await res.json();

    if (data.error) return alert(data.error);

    alert("Usuário cadastrado com sucesso!");
    
    document.querySelector("#reg-name").value = '';
    document.querySelector("#reg-email").value = '';
    document.querySelector("#reg-pass").value = '';
}

// =================== LISTAR TRILHAS USER CORRIGIDO ✅ ====================
async function carregarTrilhas() {
    console.log("Executando carregarTrilhas()");

    // 🛑 1. VERIFICAÇÃO CLIENT-SIDE (se não tiver token, já redireciona)
    if (!checkAuth()) {
        return; 
    }
    
    const res = await fetch(API + "/trilhas", {
        method: "GET",
        headers: authHeaders()
    });

    // 🛑 2. VERIFICAÇÃO SERVER-SIDE (se o token expirou ou é inválido)
    if (!res.ok) {
        const errorData = await res.json();
        console.error("Erro ao carregar trilhas:", res.status, errorData.error);
        
        // Redireciona novamente, se for 401
        if (res.status === 401) {
             alert(`Erro de acesso (${res.status}): ${errorData.error || "Por favor, faça login novamente."}`);
            window.location.href = "index.html"; 
        }
        return; // Interrompe a execução
    }

    const data = await res.json();
    const div = document.querySelector("#lista");
    div.innerHTML = "";
    
    // 🛑 3. TRATAMENTO DO ERRO forEach is not a function
    if (Array.isArray(data)) {
        data.forEach(t => {
            div.innerHTML += `
                <div style="border:1px solid #ccc;padding:10px;margin:10px;">
                    <h3>${t.title}</h3>
                    <p>${t.description}</p>
                </div>`;
        });
    } else {
         div.innerHTML = "<p>Nenhuma trilha encontrada ou formato de dados inválido.</p>";
    }
}


// =================== LISTAR + CONTROLE ADMIN CORRIGIDO ✅ ====================
async function carregarTrilhasAdmin() {
    console.log("Executando carregarTrilhasAdmin()");
    
    // 🛑 1. VERIFICAÇÃO CLIENT-SIDE (se não tiver token, já redireciona)
    if (!checkAuth()) {
        return; 
    }

    const res = await fetch(API + "/trilhas", {
        method: "GET",
        headers: authHeaders()
    });

    // 🛑 2. VERIFICAÇÃO SERVER-SIDE (se o token expirou ou é inválido)
    if (!res.ok) {
        const errorData = await res.json();
        console.error("Erro ao carregar trilhas (Admin):", res.status, errorData.error);
        
        // Redireciona novamente, se for 401
        if (res.status === 401) {
            alert(`Erro de acesso (${res.status}): ${errorData.error || "Por favor, faça login novamente."}`);
            window.location.href = "index.html"; 
        }
        return; // Interrompe a execução
    }

    const data = await res.json();
    const div = document.querySelector("#lista");
    div.innerHTML = "";

    // 🛑 3. TRATAMENTO DO ERRO forEach is not a function
    if (Array.isArray(data)) {
        data.forEach(t => {
            div.innerHTML += `
                <div style="border:1px solid #ccc;padding:10px;margin:10px;">
                    <h3>${t.title}</h3>
                    <p>${t.description}</p>
                    <button onclick="deleteTrilha(${t.id})">Apagar</button>
                </div>`;
        });
    } else {
        div.innerHTML = "<p>Nenhuma trilha encontrada ou formato de dados inválido.</p>";
    }
}


// =================== ADMIN: CRIAR TRILHA CORRIGIDO ✅ ====================
async function createTrilha() {
    // Não precisa de checkAuth() aqui se esta função só for chamada dentro de admin.html
    

    const form = new FormData();
    form.append("title", document.querySelector("#title").value);
    form.append("description", document.querySelector("#description").value);
    form.append("image", document.querySelector("#image").files[0]);

    // Headers: Apenas Authorization, Content-Type é gerado pelo navegador para FormData
    const headers = { 
        "Authorization": "Bearer " + getToken() 
    };

    const res = await fetch(API + "/trilhas", {
        method: "POST",
        headers: headers,
        body: form
    });
    
    // 🛑 VERIFICAÇÃO DE STATUS
    if (!res.ok) {
        const errorText = await res.text(); 
        alert(`Falha ao criar trilha. Status: ${res.status}. Resposta: ${errorText}`);
        return;
    }

    await res.json(); // Consumir a resposta (mesmo que vazia)
    
    document.querySelector("#title").value = '';
    document.querySelector("#description").value = '';
    document.querySelector("#image").value = '';
    
    alert("Trilha criada com sucesso!");
    carregarTrilhasAdmin();
}

// =================== ADMIN: APAGAR CORRIGIDO ✅ ====================
async function deleteTrilha(id) {
    if (!confirm(`Tem certeza que deseja apagar a trilha com ID ${id}?`)) {
        return;
    }
    
    const res = await fetch(API + `/trilhas/${id}`, {
        method: "DELETE",
        headers: authHeaders()
    });

    // 🛑 VERIFICAÇÃO DE STATUS
    if (!res.ok) {
        const errorText = await res.text(); 
        alert(`Falha ao apagar trilha. Status: ${res.status}. Resposta: ${errorText}`);
        return;
    }
    
    alert(`Trilha ${id} apagada com sucesso!`);
    carregarTrilhasAdmin();
}