import psycopg2  # biblioteca para conectar no PostgreSQL
import os        # ler variáveis de ambiente

# conecta no banco de dados usando as configurações do ambiente
def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "visionqa"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres")
    )

# cria as tabelas se elas não existirem
def criar_tabelas():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS imagens (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            largura INT NOT NULL,
            altura INT NOT NULL,
            tipo VARCHAR(20) NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS fatias (
            id SERIAL PRIMARY KEY,
            imagem_id INT REFERENCES imagens(id),
            thread_id INT NOT NULL,
            y_inicio INT NOT NULL,
            y_fim INT NOT NULL,
            media_r FLOAT NOT NULL,
            media_g FLOAT NOT NULL,
            media_b FLOAT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS inspecoes (
            id SERIAL PRIMARY KEY,
            imagem_referencia_id INT REFERENCES imagens(id),
            imagem_teste_id INT REFERENCES imagens(id),
            percentual_defeito FLOAT NOT NULL,
            status VARCHAR(20) NOT NULL,
            imagem_resultado VARCHAR(255),
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

# salva uma imagem no banco e retorna o ID gerado
def salvar_imagem(nome, largura, altura, tipo):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO imagens (nome, largura, altura, tipo) VALUES (%s, %s, %s, %s) RETURNING id",
        (nome, largura, altura, tipo)
    )
    imagem_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return imagem_id

# salva uma fatia (trecho horizontal) da imagem no banco
def salvar_fatia(imagem_id, thread_id, y_inicio, y_fim, media_r, media_g, media_b):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO fatias (imagem_id, thread_id, y_inicio, y_fim, media_r, media_g, media_b) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (imagem_id, thread_id, y_inicio, y_fim, media_r, media_g, media_b)
    )
    conn.commit()
    cur.close()
    conn.close()

# salva uma inspeção e retorna o ID gerado
def salvar_inspecao(imagem_referencia_id, imagem_teste_id, percentual_defeito, status, imagem_resultado):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO inspecoes (imagem_referencia_id, imagem_teste_id, percentual_defeito, status, imagem_resultado) VALUES (%s, %s, %s, %s, %s) RETURNING id",
        (imagem_referencia_id, imagem_teste_id, percentual_defeito, status, imagem_resultado)
    )
    inspecao_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return inspecao_id

# busca todas as inspeções com os nomes das imagens relacionadas
def buscar_inspecoes():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT i.id, i.percentual_defeito, i.status, i.criado_em,
               ref.nome AS referencia, tst.nome AS teste, i.imagem_resultado
        FROM inspecoes i
        JOIN imagens ref ON ref.id = i.imagem_referencia_id
        JOIN imagens tst ON tst.id = i.imagem_teste_id
        ORDER BY i.criado_em DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

# busca uma inspeção específica pelo ID e retorna o caminho da imagem resultado
def buscar_inspecao_por_id(inspecao_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT imagem_resultado FROM inspecoes WHERE id = %s", (inspecao_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None