-- armazena metadados das imagens
CREATE TABLE IF NOT EXISTS imagens (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    largura INT NOT NULL,
    altura INT NOT NULL,
    tipo VARCHAR(20) NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- armazena dados de análise por fatias
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

-- registra inspeções e resultados
CREATE TABLE IF NOT EXISTS inspecoes (
    id SERIAL PRIMARY KEY,
    imagem_referencia_id INT REFERENCES imagens(id),
    imagem_teste_id INT REFERENCES imagens(id),
    percentual_defeito FLOAT NOT NULL,
    status VARCHAR(20) NOT NULL,
    imagem_resultado VARCHAR(255),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);