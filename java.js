const API = "http://localhost:5000";

alert("java.js carregou!");

// =================== UTIL =======================
function saveToken(token) { localStorage.setItem("token", token); }
function getToken() { return localStorage.getItem("token"); }
function saveRole(role) { localStorage.setItem("role", role); }
function getRole() { return localStorage.getItem("role"); }

function authHeaders() {
    const t = getToken();
    if (!t) return {};
    return { "Authorization": "Bearer " + t };
}

// =================== LOGIN ========================
async function login() {
    const email = document.querySelector("#email").value;
    const password = document.querySelector("#password").value;

    const res = await fetch(API + "/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
    });

    const data = await res.json();

    if (data.error) return alert(data.error);

    saveToken(data.token);
    saveRole(data.role);

    if (data.role === "admin") window.location.href = "admin.html";
    else window.location.href = "user.html";
}

// =================== CADASTRO ========================
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

    alert("Usuário cadastrado!");
}

// =================== LISTAR TRILHAS USER ====================
async function carregarTrilhas() {
    console.log("Executando carregarTrilhas()");
    const res = await fetch(API + "/trilhas", {
        method: "GET",
        headers: authHeaders()
    });

    const data = await res.json();
    const div = document.querySelector("#lista");
    div.innerHTML = "";

    data.forEach(t => {
        div.innerHTML += `
            <div style="border:1px solid #ccc;padding:10px;margin:10px;">
                <h3>${t.title}</h3>
                <p>${t.description}</p>
            </div>`;
    });
}

// =================== LISTAR + CONTROLE ADMIN ====================
async function carregarTrilhasAdmin() {
    console.log("Executando carregarTrilhasAdmin()");
    const res = await fetch(API + "/trilhas", {
        method: "GET",
        headers: authHeaders()
    });

    const data = await res.json();
    const div = document.querySelector("#lista");
    div.innerHTML = "";

    data.forEach(t => {
        div.innerHTML += `
            <div style="border:1px solid #ccc;padding:10px;margin:10px;">
                <h3>${t.title}</h3>
                <p>${t.description}</p>
                <button onclick="deleteTrilha(${t.id})">Apagar</button>
            </div>`;
    });
}

// =================== ADMIN: CRIAR TRILHA ====================
async function createTrilha() {
    const form = new FormData();
    form.append("title", document.querySelector("#title").value);
    form.append("description", document.querySelector("#description").value);
    form.append("image", document.querySelector("#image").files[0]);

    const res = await fetch(API + "/trilhas", {
        method: "POST",
        headers: authHeaders(),
        body: form
    });

    const data = await res.json();
    alert("Trilha criada!");
    carregarTrilhasAdmin();
}

// =================== ADMIN: APAGAR ====================
async function deleteTrilha(id) {
    const res = await fetch(API + `/trilhas/${id}`, {
        method: "DELETE",
        headers: authHeaders()
    });
    carregarTrilhasAdmin();
}
