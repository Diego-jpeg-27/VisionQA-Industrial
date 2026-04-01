import time
import psycopg2
from flask import Flask
from interface.routes import routes

# cria a aplicação flask
app = Flask(__name__)

# registra as rotas definidas no blueprint
app.register_blueprint(routes)


def aguardar_banco(tentativas=10, espera=3):
    """aguarda o postgresql ficar disponível antes de criar as tabelas"""
    from repository.database import criar_tabelas
    for i in range(tentativas):
        try:
            criar_tabelas()  # cria as tabelas se não existirem
            print("tabelas criadas/verificadas com sucesso.")
            return
        except psycopg2.OperationalError:
            print(f"banco indisponível, tentativa {i+1}/{tentativas}...")
            time.sleep(espera)
    print("não foi possível conectar ao banco.")


if __name__ == "__main__":
    aguardar_banco()          # time ate o banco ficar OK
    app.run(host="0.0.0.0", port=5000, debug=True)   # inicia o servidor