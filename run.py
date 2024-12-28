from app import create_app
from flask_cors import CORS

app = create_app()

# Permite todas as origens para rotas "/api/*"
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Inicia o servidor Flask no host 0.0.0.0, tornando-o acessível de qualquer rede
if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)