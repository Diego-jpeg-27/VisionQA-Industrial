# VisionQA-Industrial 
Identificando alterações em produtos industriais com visão computacional.

**Sistemas Distribuídos – IFPE Campus Igarassu (2026)**

---

Esta atividade começou com um objetivo simples: fazer dois processos se comunicarem utilizando contêineres Docker. Decidi transformar isso em algo com propósito real: um sistema capaz de inspecionar visualmente produtos da produção industrial, que detecta defeitos com precisão e registra tudo em um banco de dados.

A ideia surgiu durante a criação do código que utiliza leitura de bitmap (pixels). Queria utilizá-lo para resolver um problema real, um sistema que automatiza essa inspeção ao comparar uma imagem de referência (utilizada como padrão) para rastrear qualquer alteração na imagem do produto a ser testado.

---

## O que o sistema faz

O usuário acessa uma interface, importa a imagem padrão do produto e a imagem que deseja inspecionar. Ao clicar em verificar, o sistema processa as duas imagens de forma concorrente usando múltiplas threads, compara cada pixel individualmente usando distância euclidiana RGB, agrupa as diferenças em regiões contíguas e desenha um bounding box vermelho ao redor de cada defeito encontrado. O resultado aparece na tela com a imagem anotada, o percentual de defeito e o status final: **APROVADO** ou **REPROVADO**. Cada inspeção é salva no banco e pode ser revisitada a qualquer momento pelo histórico.

---

## Arquitetura

O projeto foi organizado em **Layered Architecture (Arquitetura em Camadas)**
## Estrutura do Projeto

O código está organizado em camadas, separando responsabilidades:

- **interface/** – rotas Flask e interface web (HTML/JS).
- **services/** – lógica principal: processamento com threads (`processor.py`) e detecção de defeitos (`inspector.py`).
- **repository/** – acesso ao banco de dados (Repository Pattern).
- **models/** – classes simples (dataclasses) que representam as entidades.
- **db/** – script SQL para criação das tabelas.

Foi aplicado o **Repository Pattern** no arquivo `database.py`, centralizando todas as operações SQL em um único lugar e desacoplando o restante do sistema do PostgreSQL.

As rotas Flask foram organizadas utilizando o **Blueprint Pattern**, separando as responsabilidades de roteamento da inicialização da aplicação.

---

## Interface e Comunicação

A interface web foi desenvolvida com **HTML**, **JavaScript** e estilizada com **Tailwind CSS** via CDN.

---

### API REST

A comunicação entre frontend e backend é feita através de uma **API REST** construída com Flask. O frontend consome os endpoints de forma assíncrona usando `fetch()`, atualizando a interface dinamicamente sem recarregar a página.

O resultado da inspeção é retornado em **Base64** diretamente no JSON, permitindo exibir a imagem anotada na interface sem a necessidade de uma requisição adicional. Tornando mais fluida e reduzindo a latência.

---

## Modelo de Dados

As inspeções ficam registradas no PostgreSQL com três tabelas principais:

- `imagens`: armazena cada imagem enviada (nome, dimensões, tipo).
- `fatias`: guarda a média RGB de cada fatia processada por thread (dados brutos para auditoria).
- `inspecoes`: relaciona as imagens, percentual de defeito, status e caminho da imagem anotada.

Isso permite revisitar qualquer inspeção e até mesmo analisar o comportamento das fatias ao longo do tempo.

## Técnicas e Conceitos Aplicados

### Programação Concorrente com Multithreading
A imagem é dividida em fatias horizontais, e cada fatia é processada por uma thread separada usando o módulo `threading` do Python.  
Vale a pena entender que estamos falando de **concorrência**, não de paralelismo real. As threads rodam dentro de um único processo e são gerenciadas pelo sistema operacional. Por causa do GIL do Python, elas não executam código ao mesmo tempo. Mas, na prática, essa organização concorrente já traz ganho, porque o trabalho envolve operações de I/O com a imagem.

**Distância Euclidiana RGB**
A comparação entre pixels usa distância euclidiana no espaço de cores RGB:
```
d = √((R1-R2)² + (G1-G2)² + (B1-B2)²)
```
Quanto maior a distância, mais diferente é aquele pixel em relação à referência.

**Filtragem Gaussiana (GaussianBlur)**
Antes de comparar, ambas as imagens passam por um filtro gaussiano com raio 1. Isso suaviza variações mínimas de compressão e iluminação, eliminando falsos positivos antes mesmo da comparação.

**Algoritmo de Componentes Conectados**
Pixels defeituosos próximos são agrupados em regiões contíguas usando o algoritmo `ndimage.label` do SciPy, com conectividade 8 (considera os 8 vizinhos de cada pixel). Regiões menores que 50 pixels são descartadas como ruído. Apenas regiões significativas são consideradas defeitos reais.

**Bounding Box por Região**
Para cada defeito real detectado, o sistema calcula o menor retângulo que o envolve (bounding box) usando as coordenadas mínimas e máximas da região, e o desenha na imagem com número e nível de severidade.

**Sistemas Distribuídos com Docker**
Dois contêineres independentes se comunicam via rede interna Docker: um executa a aplicação Python/Flask e outro executa o PostgreSQL. O `docker-compose.yml` orquestra a inicialização, variáveis de ambiente e volume persistente de dados.

---

## O que aprendi

Me fez entender na prática o que significa sistemas distribuídos, dois processos reais rodando em ambientes isolados, se comunicando através de uma rede interna. Aprendi a diferença entre concorrência e paralelismo na prática. Aprendi também que a precisão em visão computacional não é só sobre comparar pixels, é sobre filtrar ruído, agrupar regiões e tomar decisões com base em evidências.

---

## Tecnologias

<div align="left">
  <img src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white&style=for-the-badge" height="32" alt="python" />
  <img width="8" />
  <img src="https://img.shields.io/badge/Flask-000000?logo=flask&logoColor=white&style=for-the-badge" height="32" alt="flask" />
  <img width="8" />
  <img src="https://img.shields.io/badge/HTML5-E34F26?logo=html5&logoColor=white&style=for-the-badge" height="32" alt="html5" />
  <img width="8" />
  <img src="https://img.shields.io/badge/JavaScript-F7DF1E?logo=javascript&logoColor=black&style=for-the-badge" height="32" alt="javascript" />
  <img width="8" />
  <img src="https://img.shields.io/badge/Tailwind_CSS-38B2AC?logo=tailwind-css&logoColor=white&style=for-the-badge" height="32" alt="tailwindcss" />
  <img width="8" />
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white&style=for-the-badge" height="32" alt="postgresql" />
  <img width="8" />
  <img src="https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white&style=for-the-badge" height="32" alt="docker" />
  <img width="8" />
  <img src="https://img.shields.io/badge/Pillow-8A2BE2?style=for-the-badge&logo=python&logoColor=white" height="32" alt="pillow" />
  <img width="8" />
  <img src="https://img.shields.io/badge/NumPy-013243?logo=numpy&logoColor=white&style=for-the-badge" height="32" alt="numpy" />
  <img width="8" />
  <img src="https://img.shields.io/badge/SciPy-8CAAE6?logo=scipy&logoColor=white&style=for-the-badge" height="32" alt="scipy" />
  <img width="8" />
  <img src="https://img.shields.io/badge/psycopg2-336791?style=for-the-badge&logo=postgresql&logoColor=white" height="32" alt="psycopg2" />
</div>

---

## Desenvolvedor

- [Diego Nunes](https://github.com/Diego-jpeg-27)

---