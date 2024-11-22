from flask import Blueprint, request, jsonify
from .models import User, Lista, Item
from . import db
from datetime import datetime

main = Blueprint("main", __name__)


@main.route("/api/users", methods=["POST"])
def create_user():
    data = request.json
    new_user = User(
        nome=data.get("nome"), telefone=data.get("telefone"), email=data.get("email")
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "Usuário criado com sucesso!"}), 201


@main.route("/api/users", methods=["GET"])
def get_users():
    users = User.query.all()
    return (
        jsonify(
            [
                {
                    "id": user.id,
                    "nome": user.nome,
                    "telefone": user.telefone,
                    "email": user.email,
                }
                for user in users
            ]
        ),
        200,
    )


@main.route("/api/listas", methods=["POST"])
def criar_lista():
    """
    Cria uma nova lista de compras associada a um usuário.
    """
    data = request.json
    user_id = data.get("userId")
    data_criacao = data.get("data")  # Aceitar a data enviada pelo frontend
    itens_data = data.get("itens", [])

    if not user_id or not itens_data:
        return jsonify({"error": "Campos obrigatórios estão faltando."}), 400

    # Criação da lista com a data enviada pelo frontend
    nova_lista = Lista(user_id=user_id, data=datetime.fromisoformat(data_criacao))
    for item in itens_data:
        novo_item = Item(
            produto=item["produto"],
            valor=item["valor"],
            quantidade=item["quantidade"],
            supermercado=item["supermercado"],
            lista=nova_lista,
        )
        db.session.add(novo_item)

    db.session.add(nova_lista)
    db.session.commit()
    return (
        jsonify({"message": "Lista criada com sucesso!", "listaId": nova_lista.id}),
        201,
    )


@main.route("/api/listas", methods=["GET"])
def listar_listas():
    """
    Retorna todas as listas de compras cadastradas, incluindo o nome do usuário.
    """
    listas = Lista.query.all()
    return (
        jsonify(
            [
                {
                    "id": lista.id,
                    "userId": lista.user_id,
                    "userNome": lista.user.nome,  # Incluímos o nome do usuário
                    "data": lista.data.isoformat(),
                    "itens": [
                        {
                            "id": item.id,
                            "produto": item.produto,
                            "valor": item.valor,
                            "quantidade": item.quantidade,
                            "supermercado": item.supermercado,
                        }
                        for item in lista.itens
                    ],
                }
                for lista in listas
            ]
        ),
        200,
    )


@main.route("/api/listas/<int:lista_id>", methods=["PUT"])
def atualizar_lista(lista_id):
    """
    Atualiza uma lista existente com novos itens ou modifica os existentes.
    """
    data = request.json
    lista = Lista.query.get_or_404(lista_id)

    lista.user_id = data.get("userId", lista.user_id)
    lista.data = datetime.fromisoformat(data.get("data", lista.data.isoformat()))

    # Atualizar ou adicionar itens
    itens_data = data.get("itens", [])
    for item_data in itens_data:
        if "id" in item_data:  # Item existente
            item = Item.query.get(item_data["id"])
            if item:
                item.produto = item_data["produto"]
                item.valor = item_data["valor"]
                item.quantidade = item_data["quantidade"]
                item.supermercado = item_data["supermercado"]
        else:  # Novo item
            novo_item = Item(
                produto=item_data["produto"],
                valor=item_data["valor"],
                quantidade=item_data["quantidade"],
                supermercado=item_data["supermercado"],
                lista=lista,
            )
            db.session.add(novo_item)

    db.session.commit()
    return jsonify({"message": "Lista atualizada com sucesso!"}), 200


@main.route("/api/listas/<int:lista_id>", methods=["DELETE"])
def excluir_lista(lista_id):
    """
    Exclui uma lista existente e todos os seus itens.
    """
    lista = Lista.query.get_or_404(lista_id)
    db.session.delete(lista)
    db.session.commit()
    return jsonify({"message": "Lista excluída com sucesso!"}), 200


@main.route("/api/listas/usuario/<int:user_id>", methods=["GET"])
def listar_listas_usuario(user_id):
    """
    Retorna todas as listas criadas por um usuário específico.
    """
    listas = Lista.query.filter_by(user_id=user_id).all()
    if not listas:
        return jsonify({"message": "Nenhuma lista encontrada para este usuário."}), 404

    return (
        jsonify(
            [
                {
                    "id": lista.id,
                    "userId": lista.user_id,
                    "data": lista.data.isoformat(),
                    "itens": [
                        {
                            "id": item.id,
                            "produto": item.produto,
                            "valor": item.valor,
                            "quantidade": item.quantidade,
                            "supermercado": item.supermercado,
                        }
                        for item in lista.itens
                    ],
                }
                for lista in listas
            ]
        ),
        200,
    )


@main.route("/api/listas/supermercado/<string:supermercado>", methods=["GET"])
def listar_listas_supermercado(supermercado):
    """
    Retorna todas as listas contendo itens de um supermercado específico.
    """
    listas = Lista.query.join(Item).filter(Item.supermercado == supermercado).all()
    if not listas:
        return (
            jsonify({"message": "Nenhuma lista encontrada para este supermercado."}),
            404,
        )

    return (
        jsonify(
            [
                {
                    "id": lista.id,
                    "userId": lista.user_id,
                    "data": lista.data.isoformat(),
                    "itens": [
                        {
                            "id": item.id,
                            "produto": item.produto,
                            "valor": item.valor,
                            "quantidade": item.quantidade,
                            "supermercado": item.supermercado,
                        }
                        for item in lista.itens
                        if item.supermercado == supermercado
                    ],
                }
                for lista in listas
            ]
        ),
        200,
    )


@main.route("/api/itens/<string:produto>", methods=["GET"])
def listar_itens_por_produto(produto):
    """
    Retorna todas as listas que contêm um determinado produto.
    """
    itens = Item.query.filter(Item.produto.ilike(f"%{produto}%")).all()
    if not itens:
        return jsonify({"message": "Nenhum item encontrado para este produto."}), 404

    return (
        jsonify(
            [
                {
                    "listaId": item.lista_id,
                    "produto": item.produto,
                    "valor": item.valor,
                    "quantidade": item.quantidade,
                    "supermercado": item.supermercado,
                }
                for item in itens
            ]
        ),
        200,
    )
