# usa uma imagem oficial do python versão 3.11 
FROM python:3.11-slim

# define o diretório de trabalho dentro do contêiner
WORKDIR /app

# copia o arquivo de dependências para dentro do contêiner
COPY requirements.txt .

# instala as bibliotecas listadas no requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# copia todo o conteúdo da pasta atual para dentro do contêiner
COPY . .

# expõe a porta 5000 para acesso externo
EXPOSE 5000

# comando que será executado quando o contêiner iniciar
CMD ["python", "main.py"]