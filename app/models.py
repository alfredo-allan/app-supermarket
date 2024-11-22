from . import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f"<User {self.nome}>"


class Lista(db.Model):
    __tablename__ = "listas"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False
    ) 
    data = db.Column(db.DateTime, nullable=False)
    itens = db.relationship("Item", backref="lista", lazy=True)
    user = db.relationship("User", backref="listas")  # Relação com o modelo User


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produto = db.Column(db.String(120), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    supermercado = db.Column(db.String(120), nullable=False)
    lista_id = db.Column(
        db.Integer, db.ForeignKey("listas.id"), nullable=False
    ) 
