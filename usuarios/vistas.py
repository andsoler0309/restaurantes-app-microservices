import json

from flask import request
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from flask_restful import Resource
import hashlib
from datetime import datetime
from sqlalchemy.orm import joinedload

from modelos import (
    db,
    Ingrediente,
    IngredienteSchema,
    RecetaIngrediente,
    RecetaIngredienteSchema,
    Receta,
    RecetaSchema,
    Usuario,
    UsuarioSchema,
    Restaurante,
    RestauranteSchema,
    Rol,
    MenuSemana,
    MenuSemanaSchema,
    MenuReceta,
)

ingrediente_schema = IngredienteSchema()
receta_ingrediente_schema = RecetaIngredienteSchema()
receta_schema = RecetaSchema()
usuario_schema = UsuarioSchema()
restaurante_schema = RestauranteSchema()
menu_semana_schema = MenuSemanaSchema()


class VistaSignIn(Resource):
    def post(self):
        usuario = Usuario.query.filter(
            Usuario.usuario == request.json["usuario"]
        ).first()
        if usuario is None:
            contrasena_encriptada = hashlib.md5(
                request.json["contrasena"].encode("utf-8")
            ).hexdigest()
            nuevo_usuario = Usuario(
                usuario=request.json["usuario"],
                contrasena=contrasena_encriptada,
                rol=Rol.ADMINISTRADOR,
            )
            db.session.add(nuevo_usuario)
            db.session.commit()
            token_de_acceso = create_access_token(identity=nuevo_usuario.id)
            return {"mensaje": "usuario creado exitosamente", "id": nuevo_usuario.id}
        else:
            return "El usuario ya existe", 404

    def put(self, id_usuario):
        usuario = Usuario.query.get_or_404(id_usuario)
        usuario.contrasena = request.json.get("contrasena", usuario.contrasena)
        db.session.commit()
        return usuario_schema.dump(usuario)

    def delete(self, id_usuario):
        usuario = Usuario.query.get_or_404(id_usuario)
        db.session.delete(usuario)
        db.session.commit()
        return "", 204


class VistaLogIn(Resource):
    def post(self):
        contrasena_encriptada = hashlib.md5(
            request.json["contrasena"].encode("utf-8")
        ).hexdigest()
        usuario = Usuario.query.filter(
            Usuario.usuario == request.json["usuario"],
            Usuario.contrasena == contrasena_encriptada,
        ).first()
        db.session.commit()
        print(str(hashlib.md5("admin".encode("utf-8")).hexdigest()))
        if usuario is None:
            return "El usuario no existe", 404
        else:
            token_de_acceso = create_access_token(identity=usuario.id)
            return {
                "mensaje": "Inicio de sesión exitoso",
                "token": token_de_acceso,
                "id": usuario.id,
                "rol": usuario.rol.name,
            }
