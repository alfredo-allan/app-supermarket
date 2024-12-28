from werkzeug.security import generate_password_hash, check_password_hash
from . import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(
        db.String(128), nullable=False
    )  # Para armazenar hash da senha

    def set_senha(self, senha):
        """Define a senha do usuário com hashing."""
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        """Verifica a senha do usuário."""
        return check_password_hash(self.senha_hash, senha)

    def __repr__(self):
        return f"<User {self.nome}>"


class Lista(db.Model):
    __tablename__ = "listas"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    data = db.Column(db.DateTime, nullable=False)
    
    # Relacionamento com Item, com cascata para excluir itens associados
    itens = db.relationship("Item", backref="lista", lazy=True, cascade="all, delete-orphan")
    
    # Relação com o modelo User
    user = db.relationship("User", backref="listas")  



class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produto = db.Column(db.String(120), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    supermercado = db.Column(db.String(120), nullable=False)
    lista_id = db.Column(db.Integer, db.ForeignKey("listas.id"), nullable=False)
