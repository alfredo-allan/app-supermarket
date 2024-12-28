from flask import Blueprint, request, jsonify
from .models import User, Lista, Item
from . import db
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload


main = Blueprint("main", __name__)
from flask_cors import cross_origin


@main.route("/api/users", methods=["POST"])
@cross_origin()
def register_user():
    data = request.json
    nome = data.get("nome", "").strip()
    telefone = data.get("telefone", "").strip()
    email = data.get("email", "").strip()
    senha = data.get("senha", "").strip()

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email já registrado"}), 400

    user = User(nome=nome, telefone=telefone, email=email)
    user.set_senha(senha)  # Define o hash da senha
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Usuário registrado com sucesso!"}), 201


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


@main.route("/api/login", methods=["POST"])
@cross_origin()
def login_user():
    # Obtendo dados da requisição JSON enviada pelo frontend
    data = request.json
    nome = data.get("nome", "").strip()  # Nome enviado pelo usuário
    telefone = data.get("telefone", "").strip()  # Telefone enviado pelo usuário

    # Verifica no banco de dados se existe um usuário com o nome e telefone fornecidos
    user = User.query.filter_by(nome=nome, telefone=telefone).first()

    if user:
        # Retorna sucesso com o nome do usuário
        return (
            jsonify(
                {"message": "Login bem-sucedido!", "nome": user.nome, "id": user.id}
            ),
            200,
        )
    else:
        # Retorna erro se o usuário não for encontrado
        return jsonify({"error": "Usuário não encontrado ou dados incorretos"}), 404


@main.route("/api/listas", methods=["POST"])
@cross_origin()
def criar_lista():
    """
    Cria uma nova lista de compras associada a um usuário.
    """
    data = request.json
    user_id = data.get("userId")
    data_criacao = data.get("data")
    itens_data = data.get("itens", [])

    # Validação de campos obrigatórios
    if not user_id or not itens_data:
        return (
            jsonify({"error": "Campos obrigatórios estão faltando: userId ou itens"}),
            400,
        )

    try:
        # Criação da lista
        nova_lista = Lista(user_id=user_id, data=datetime.fromisoformat(data_criacao))

        for item in itens_data:
            # Validação de cada item
            if not all(
                k in item for k in ("produto", "valor", "quantidade", "supermercado")
            ):
                return jsonify({"error": "Dados do item incompletos."}), 400

            novo_item = Item(
                produto=item["produto"],
                valor=item["valor"],
                quantidade=item["quantidade"],
                supermercado=item["supermercado"],
                lista=nova_lista,
            )
            db.session.add(novo_item)

        # Salva a lista e os itens
        db.session.add(nova_lista)
        db.session.commit()

        return (
            jsonify({"message": "Lista criada com sucesso!", "listaId": nova_lista.id}),
            201,
        )

    except ValueError:
        return jsonify({"error": "Formato de data inválido. Use ISO 8601."}), 400
    except SQLAlchemyError as e:
        db.session.rollback()  # Reverte qualquer alteração em caso de erro
        return jsonify({"error": f"Erro no banco de dados: {str(e)}"}), 500


@main.route("/api/listas", methods=["GET"])
@cross_origin()
def listar_listas():
    """
    Retorna as listas de compras de um usuário específico, incluindo o nome do usuário.
    """
    user_id = request.args.get("userId")  # Obtém o userId dos parâmetros da URL

    if not user_id:
        return jsonify({"error": "O parâmetro userId é obrigatório."}), 400

    try:
        user_id = int(user_id)  # Valida se o userId é um número
    except ValueError:
        return jsonify({"error": "O parâmetro userId deve ser um número válido."}), 400

    # Busca as listas associadas ao userId com as relações necessárias
    listas = (
        Lista.query.options(joinedload(Lista.itens), joinedload(Lista.user))
        .filter_by(user_id=user_id)
        .all()
    )

    if not listas:
        return jsonify({"message": "Nenhuma lista encontrada para este usuário."}), 404

    # Monta a resposta com as listas do usuário
    response = [
        {
            "id": lista.id,
            "userId": lista.user_id,
            "userNome": lista.user.nome if lista.user else None,
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

    return jsonify(response), 200


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
    print(f"Recebendo requisição DELETE para excluir lista com ID: {lista_id}")

    lista = Lista.query.get(lista_id)

    if not lista:
        return jsonify({"error": "Lista não encontrada"}), 404

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
