// java.js - NOVO CONTEÚDO

const API = "http://127.0.0.1:5000";

// alert("java.js carregou!"); // Remova o alert para produção

// --- FUNÇÕES PRINCIPAIS DE TRILHAS/EVENTOS ---

function carregarTrilhas() {
    const listaDiv = document.getElementById('lista');
    // Adiciona uma verificação para evitar o TypeError se a div 'lista' não existir
    if (!listaDiv) {
        console.warn("Elemento com ID 'lista' não encontrado. Pulando carregamento de trilhas.");
        return; 
    }

    fetch(API + '/api/eventos')
        .then(response => {
            if (!response.ok) {
                throw new Error('Erro ao carregar trilhas: ' + response.statusText);
            }
            return response.json();
        })
        .then(data => {
            listaDiv.innerHTML = '';

            if (data.length === 0) {
                listaDiv.innerHTML = '<p>Nenhuma trilha disponível no momento.</p>';
                return;
            }

            data.forEach(trilha => {
                const trilhaItem = document.createElement('div');
                let imagemHTML = '';
                if (trilha.nome_arquivo) {
                    imagemHTML = `<img src="${API}/static/uploads/${trilha.nome_arquivo}" alt="Imagem do Evento ${trilha.nome}" style="max-width: 300px; height: auto; display: block; margin-bottom: 10px;">`;
                }
                trilhaItem.innerHTML = `
                <hr>
                <h3>${trilha.nome} (${trilha.data})</h3>
                <p>${trilha.descricao}</p>
                <p>Participantes: ${trilha.inscritos_count} pessoas</p>
                
                <button onclick="inscreverUsuario(${trilha.id})">Inscrever-se na Trilha</button>
            `;
            listaDiv.appendChild(trilhaItem);
            });
        })
        .catch(error => {
            console.error('Falha no fetch:', error);
            // Verifica a existência do elemento também no catch
            const listaDivCatch = document.getElementById('lista'); 
            if (listaDivCatch) {
                listaDivCatch.innerHTML = `<p style="color: red;">Erro ao carregar trilhas: ${error.message}</p>`;
            }
        });
}

async function inscreverUsuario(eventoId) {
    const res = await fetch(`${API}/inscrever/${eventoId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    });

    if (res.ok) {
        // Recarrega a lista para atualizar a contagem de participantes
        carregarTrilhas(); 
    } else {
        alert("Erro ao tentar se inscrever. Você está logado?");
    }
}

// --- FUNÇÕES DE ADMIN (CRUD DE IMAGENS) ---

async function carregarImagens() {
    const galeria = document.getElementById("galeria"); // Busca localmente
    if (!galeria) return; // Protege contra páginas sem galeria

    const res = await fetch(API + "/imagens"); // CORREÇÃO: Usando a constante API
    const data = await res.json();

    galeria.innerHTML = "";

    data.imagens.forEach(img => {
        // CORREÇÃO: Usando nome_arquivo e titulo/descricao
        const nomeArquivo = img.nome_arquivo || img.arquivo; 
        galeria.innerHTML += `
        <div class="box">
            <img src="${API}/static/uploads/${nomeArquivo}">
            <p>Título: ${img.titulo}</p>
            <p>Descrição: ${img.descricao}</p>
            <button onclick="deletar('${img.id}')">Deletar</button>
        </div>
        `;
    });
}

async function deletar(id) {
    await fetch(`${API}/imagens/${id}`, { method: "DELETE" });
    carregarImagens();
}

// Função de inicialização do painel de administração
function inicializarAdmin() {
    const form = document.getElementById("formCadastro");
    
    if (form) { // Verifica se o formulário existe
        // Cadastrar
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            const formData = new FormData(form);

            await fetch(API + "/imagens", {
                method: "POST",
                body: formData
            });

            form.reset();
            carregarImagens();
        });
    }

    // Inicializa o carregamento das imagens (se a galeria existir)
    carregarImagens();
}

// CORREÇÃO: Chave } Faltando no final do arquivo
// (Esta chave estava incompleta no seu upload, vamos removê-la aqui) 
// Se a chave no final do seu código estiver correta (fechando a função inscreverUsuario), ignore isso.