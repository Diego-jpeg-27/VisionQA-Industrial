import os
import io
import base64
from flask import Blueprint, request, jsonify, render_template_string, send_file
from services.inspector import inspecionar
from repository.database import buscar_inspecoes, buscar_inspecao_por_id

# cria um blueprint para organizar as rotas
routes = Blueprint("routes", __name__)

# pastas para arquivos temporários e resultados
UPLOAD_FOLDER = "/tmp/visionqa"
RESULTADO_FOLDER = "/tmp/visionqa/resultados"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTADO_FOLDER, exist_ok=True)

# html completo da interface web 
# inclui tailwind css, javascript e a estrutura das páginas
HTML = """
<!DOCTYPE html>
<html lang="pt-br" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VisionQA | Industrial Precision</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&family=Roboto+Mono:wght@400;500&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" />
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        background: '#0c0e14',
                        surface: '#171921',
                        'surface-low': '#11131a',
                        'surface-high': '#1d1f27',
                        'surface-bright': '#292c35',
                        primary: '#6dddff',
                        'primary-dim': '#00c3eb',
                        secondary: '#00fd87',
                        error: '#ff716c',
                        outline: '#46484f',
                    },
                    fontFamily: {
                        headline: ['Space Grotesk', 'sans-serif'],
                        body: ['Inter', 'sans-serif'],
                        mono: ['Roboto Mono', 'monospace'],
                    }
                }
            }
        }
    </script>
    <style>
        .defect-ring { box-shadow: 0 0 0 2px #ff4444, 0 0 15px rgba(255, 68, 68, 0.6); }
        .scanning-line {
            position: absolute;
            width: 100%;
            height: 2px;
            background: #6dddff;
            box-shadow: 0 0 15px #6dddff;
            animation: scan 2s linear infinite;
            display: none;
        }
        @keyframes scan {
            0% { top: 0; }
            100% { top: 100%; }
        }
    </style>
</head>
<body class="bg-background text-slate-200 font-body antialiased">
    <!-- Sidebar -->
    <aside class="fixed left-0 top-0 bottom-0 w-64 bg-surface-low border-r border-outline/10 flex flex-col z-50">
        <div class="p-8 flex flex-col gap-1">
            <h1 class="text-xl font-bold text-primary font-headline tracking-tight">VisionQA</h1>
            <p class="text-[10px] uppercase tracking-widest text-slate-500 font-medium">Industrial Precision</p><br>
    
        </div>
        <nav class="flex-1 px-2 space-y-1 mt-4">
            <a href="#" class="flex items-center gap-3 px-4 py-3 bg-surface-high text-primary border-r-2 border-primary">
                <span class="material-symbols-outlined">dashboard</span>
                <span class="font-medium text-sm">Dashboard</span>
            </a>
        </nav>
     
    </aside>

    <!-- Main Content -->
    <div class="ml-64 flex-1 flex flex-col min-h-screen">
        <!-- Top Bar -->
        <header class="h-20 flex items-center justify-between px-8 sticky top-0 bg-background/80 backdrop-blur-md z-40 border-b border-outline/5">
            <div class="flex items-center gap-8">
                <div class="flex items-center gap-3 bg-surface px-4 py-2 rounded-full border border-outline/10">
                    <span class="w-2 h-2 rounded-full bg-secondary animate-pulse shadow-[0_0_8px_rgba(0,253,135,0.6)]"></span>
                    <span class="text-[10px] font-mono font-bold text-secondary uppercase tracking-widest">Sistema Ativo</span>
                </div>
            </div>
            <div class="flex items-center gap-3">
                <div class="text-right">
                    <p class="text-sm font-bold text-slate-200">Operador Industrial</p>
                    <p class="text-[10px] text-slate-500 font-mono">ID: 99201-QA</p>
                </div>
                <div class="w-10 h-10 rounded-full bg-surface-high border border-primary/20 flex items-center justify-center">
                    <span class="material-symbols-outlined text-primary">person</span>
                </div>
            </div>
        </header>

        <main class="p-8 space-y-8">
            <!-- Bento Grid -->
            <div class="grid grid-cols-12 gap-6">
                <!-- Input Card -->
                <div class="col-span-12 lg:col-span-4">
                    <div class="bg-surface rounded-xl p-6 border border-outline/5 h-full flex flex-col">
                        <h2 class="text-[10px] font-bold text-primary font-headline uppercase tracking-widest mb-6">Entrada de Inspeção</h2>
                        <div class="space-y-4 flex-1">
                            <div class="group relative bg-surface-low border-2 border-dashed border-outline/20 rounded-xl p-6 flex flex-col items-center justify-center text-center hover:border-primary/50 transition-all cursor-pointer" onclick="document.getElementById('imgRef').click()">
                                <span class="material-symbols-outlined text-3xl text-slate-500 group-hover:text-primary mb-2">cloud_upload</span>
                                <p class="text-xs font-medium text-slate-200">Imagem de Referência</p>
                                <input type="file" id="imgRef" class="hidden" accept="image/*">
                            </div>
                            <div class="group relative bg-surface-low border-2 border-dashed border-outline/20 rounded-xl p-6 flex flex-col items-center justify-center text-center hover:border-primary/50 transition-all cursor-pointer" onclick="document.getElementById('imgTeste').click()">
                                <span class="material-symbols-outlined text-3xl text-slate-500 group-hover:text-primary mb-2">biotech</span>
                                <p class="text-xs font-medium text-slate-200">Imagem de Teste</p>
                                <input type="file" id="imgTeste" class="hidden" accept="image/*">
                            </div>
                        </div>
                        <button onclick="executarInspecao()" class="mt-6 w-full py-4 bg-surface-high border border-outline/20 text-slate-200 font-bold uppercase text-[10px] tracking-widest hover:bg-surface-bright transition-all">
                            Iniciar Verificação
                        </button>
                    </div>
                </div>

                <!-- Viewer Card -->
                <div class="col-span-12 lg:col-span-5">
                    <div class="bg-surface rounded-xl p-2 border border-outline/5 relative group overflow-hidden h-full min-h-[400px]">
                        <div id="statusBadge" class="hidden absolute top-6 left-6 z-10 bg-black/60 backdrop-blur-md px-3 py-1 rounded-full border border-error/30">
                            <p id="badgeText" class="text-[10px] font-mono font-bold text-error">ANOMALIA DETECTADA</p>
                        </div>
                        <div class="relative w-full h-full bg-black rounded-lg overflow-hidden flex items-center justify-center">
                            <div id="scanLine" class="scanning-line"></div>
                            <img id="imgResultado" class="max-w-full max-h-full object-contain opacity-80" src="" alt="Aguardando inspeção...">
                            <div id="defectMarkers" class="absolute inset-0 pointer-events-none"></div>
                        </div>
                    </div>
                </div>

                <!-- Metrics Card -->
                <div class="col-span-12 lg:col-span-3 flex flex-col gap-6">
                    <div class="bg-surface rounded-xl p-8 border border-outline/5 flex flex-col justify-center items-center text-center">
                        <h2 class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">VERIFICANDO</h2>
                        <p id="verdictText" class="text-4xl font-black font-headline tracking-tighter text-slate-500">AGUARDANDO</p>
                        <div class="mt-6 h-1 w-32 bg-slate-800 rounded-full overflow-hidden">
                            <div id="verdictBar" class="h-full bg-primary w-0 transition-all duration-500"></div>
                        </div>
                    </div>
                    <div class="bg-surface rounded-xl p-6 border border-outline/5 flex-1 space-y-6">
                        <div>
                            <h3 class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Probabilidade de Defeito</h3>
                            <p id="metricProb" class="text-3xl font-mono font-medium text-slate-100 mt-1">0.000<span class="text-primary text-sm ml-1">%</span></p>
                        </div>
                        <div>
                            <h3 class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Fatias Comprometidas</h3>
                            <p id="metricSlices" class="text-3xl font-mono font-medium text-slate-100 mt-1">00</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- History Table -->
            <section class="space-y-4">
                <h2 class="text-xl font-bold font-headline tracking-tight text-slate-100 px-2">Log de Inspeções</h2>
                <div class="bg-surface rounded-xl overflow-hidden border border-outline/5">
                    <table class="w-full text-left border-collapse">
                        <thead>
                            <tr class="bg-surface-low border-b border-outline/5">
                                <th class="px-6 py-4 text-[10px] font-bold text-slate-500 uppercase tracking-widest">ID</th>
                                <th class="px-6 py-4 text-[10px] font-bold text-slate-500 uppercase tracking-widest">Arquivos</th>
                                <th class="px-6 py-4 text-[10px] font-bold text-slate-500 uppercase tracking-widest">Defeito %</th>
                                <th class="px-6 py-4 text-[10px] font-bold text-slate-500 uppercase tracking-widest">Status</th>
                                <th class="px-6 py-4 text-[10px] font-bold text-slate-500 uppercase tracking-widest">Data</th>
                                <th class="px-6 py-4 text-[10px] font-bold text-slate-500 uppercase tracking-widest text-right">Ação</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-outline/5">
                            {% for row in historico %}
                            <tr class="hover:bg-surface-high transition-colors group">
                                <td class="px-6 py-4 font-mono text-xs text-slate-200">#{{ row[0] }}</td>
                                <td class="px-6 py-4 text-xs text-slate-500">{{ row[5] }}</td>
                                <td class="px-6 py-4 font-mono text-xs text-slate-200">{{ row[1] }}%</td>
                                <td class="px-6 py-4">
                                    {% if row[2] == 'APROVADO' %}
                                    <span class="px-2 py-1 bg-green-500/10 text-secondary rounded-full text-[10px] font-black uppercase tracking-tight">APROVADO</span>
                                    {% else %}
                                    <span class="px-2 py-1 bg-red-500/10 text-error rounded-full text-[10px] font-black uppercase tracking-tight">REPROVADO</span>
                                    {% endif %}
                                </td>
                                <td class="px-6 py-4 text-xs text-slate-500">{{ row[3].strftime('%d/%m/%Y %H:%M') }}</td>
                                <td class="px-6 py-4 text-right">
                                    <button onclick="verResultado({{ row[0] }})" class="text-[10px] font-bold text-primary uppercase tracking-widest opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1 justify-end w-full">
                                        Detalhes <span class="material-symbols-outlined text-sm">chevron_right</span>
                                    </button>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </section>
        </main>
    </div>

    <!-- Modal -->
    <div id="modal" class="hidden fixed inset-0 bg-black/80 backdrop-blur-sm z-[100] flex items-center justify-center p-6">
        <div class="bg-surface border border-outline/20 rounded-2xl max-w-4xl w-full overflow-hidden shadow-2xl">
            <div class="p-6 border-b border-outline/10 flex justify-between items-center">
                <h2 class="text-xl font-bold font-headline text-primary">Resultado Detalhado #<span id="modalId"></span></h2>
                <button onclick="fecharModal()" class="text-slate-500 hover:text-white transition-colors">
                    <span class="material-symbols-outlined">close</span>
                </button>
            </div>
            <div class="p-6 bg-black flex justify-center">
                <img id="modalImg" class="max-h-[70vh] object-contain rounded-lg" src="" alt="Resultado">
            </div>
        </div>
    </div>

    <script>
        async function executarInspecao() {
            const imgRef = document.getElementById("imgRef").files[0];
            const imgTeste = document.getElementById("imgTeste").files[0];
            if (!imgRef || !imgTeste) {
                alert("Selecione as duas imagens antes de verificar.");
                return;
            }

            const scanLine = document.getElementById("scanLine");
            scanLine.style.display = "block";
            
            const form = new FormData();
            form.append("imagem_ref", imgRef);
            form.append("imagem_teste", imgTeste);

            try {
                const response = await fetch("/inspecionar", { method: "POST", body: form });
                const data = await response.json();
                
                scanLine.style.display = "none";
                
                // Update UI
                const verdictText = document.getElementById("verdictText");
                const verdictBar = document.getElementById("verdictBar");
                const statusBadge = document.getElementById("statusBadge");
                const badgeText = document.getElementById("badgeText");

                verdictText.innerText = data.status;
                verdictText.className = `text-4xl font-black font-headline tracking-tighter ${data.status === 'REPROVADO' ? 'text-error' : 'text-secondary'}`;
                verdictBar.className = `h-full transition-all duration-500 ${data.status === 'REPROVADO' ? 'bg-error w-3/4' : 'bg-secondary w-full'}`;
                
                statusBadge.classList.remove('hidden');
                badgeText.innerText = data.status === 'REPROVADO' ? `ANOMALIA: ${data.percentual_defeito}%` : 'SISTEMA OK';
                badgeText.className = `text-[10px] font-mono font-bold ${data.status === 'REPROVADO' ? 'text-error' : 'text-secondary'}`;

                document.getElementById("metricProb").innerHTML = `${data.percentual_defeito}<span class="text-primary text-sm ml-1">%</span>`;
                document.getElementById("metricSlices").innerText = String(data.fatias_com_defeito).padStart(2, '0');
                document.getElementById("imgResultado").src = "data:image/jpeg;base64," + data.imagem_resultado;
                
            } catch (e) {
                scanLine.style.display = "none";
                alert("Erro ao processar inspeção.");
            }
        }

        async function verResultado(id) {
            document.getElementById("modalId").innerText = id;
            document.getElementById("modalImg").src = `/resultado/${id}`;
            document.getElementById("modal").classList.remove("hidden");
        }

        function fecharModal() {
            document.getElementById("modal").classList.add("hidden");
        }
    </script>
</body>
</html>
"""

@routes.route("/")
def index():
    # busca os dados do banco
    historico = buscar_inspecoes() 
    return render_template_string(HTML, historico=historico)

@routes.route("/inspecionar", methods=["POST"])
def inspecionar_route():
    # pega os arquivos enviados pelo formulário
    img_ref = request.files["imagem_ref"]
    img_teste = request.files["imagem_teste"]
    
    # salva os arquivos temporariamente na pasta de upload
    caminho_ref = os.path.join(UPLOAD_FOLDER, img_ref.filename)
    caminho_teste = os.path.join(UPLOAD_FOLDER, img_teste.filename)
    img_ref.save(caminho_ref)
    img_teste.save(caminho_teste)
   
    # chama o serviço de inspeçao
    resultado = inspecionar(caminho_ref, caminho_teste, img_ref.filename, img_teste.filename)

    # converte a imagem resultado para base64, envio via JSON
    buffer = io.BytesIO()
    resultado["imagem_resultado"].save(buffer, format="JPEG")
    img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    
    # retorna os dados em JSON para o front
    return jsonify({
        "inspecao_id": resultado["inspecao_id"],
        "percentual_defeito": resultado["percentual_defeito"],
        "status": resultado["status"],
        "fatias_com_defeito": resultado["fatias_com_defeito"],
        "imagem_resultado": img_base64
    })

@routes.route("/resultado/<int:inspecao_id>")
def ver_resultado(inspecao_id):
    # busca o nome do arquivo no bd
    nome_arquivo = buscar_inspecao_por_id(inspecao_id) 
    if not nome_arquivo:
        return "Resultado não encontrado", 404
    caminho = os.path.join(RESULTADO_FOLDER, nome_arquivo)
    if not os.path.exists(caminho):
        return "Arquivo não encontrado", 404
    # return a imagem
    return send_file(caminho, mimetype="image/jpeg")