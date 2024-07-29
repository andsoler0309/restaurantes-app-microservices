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


class VistaMenuSemana(Resource):
    @jwt_required()
    def get(self, id_usuario):
        print(id_usuario)
        usuario = Usuario.query.filter(Usuario.id == id_usuario).first()
        if usuario is None:
            return "El usuario no existe", 404
        if usuario.rol is Rol.CHEF:
            menus = MenuSemana.query.filter_by(
                id_restaurante=usuario.restaurante_id
            ).all()
        else:
            lista_restaurantes_id = [
                restaurante.id
                for restaurante in Restaurante.query.filter_by(
                    administrador_id=id_usuario
                ).all()
            ]
            menus = MenuSemana.query.filter(
                MenuSemana.id_restaurante.in_(lista_restaurantes_id)
            ).all()
        result = []
        for menu in menus:
            usuario = Usuario.query.filter_by(id=menu.id_usuario).first()
            menu_final = menu_semana_schema.dump(menu)
            menu_final["usuario"] = UsuarioSchema(only=["usuario", "rol"]).dump(usuario)
            menu_final["usuario"]["rol"] = usuario.rol.name
            result.append(menu_final)
        return result, 200

    @jwt_required()
    def post(self, id_usuario):
        usuario = Usuario.query.filter(Usuario.id == id_usuario).first()
        id_restaurante = None
        if usuario is None:
            return "El usuario no existe", 404
        if usuario.rol is Rol.CHEF:
            id_restaurante = usuario.restaurante_id
        else:
            id_restaurante = request.json["id_restaurante"]
        nombre_menu_repetido = MenuSemana.query.filter_by(
            nombre=request.json["nombre"]
        ).first()

        if nombre_menu_repetido is not None:
            return "El nombre del menu ya existe", 400
        try:
            fecha_inicial = datetime.strptime(
                request.json["fechaInicial"], "%Y-%m-%d"
            ).date()
            fecha_final = datetime.strptime(
                request.json["fechaFinal"], "%Y-%m-%d"
            ).date()
        except Exception as e:
            return str(e), 400

        diff_fecha = fecha_final - fecha_inicial
        if diff_fecha.days != 6:
            return "Las fechas no tienen la diferencia correcta", 400

        todos_menus = MenuSemana.query.filter_by(id_restaurante=id_restaurante).all()
        for menu in todos_menus:
            if (fecha_final >= menu.fecha_final >= fecha_inicial) or (
                fecha_final >= menu.fecha_inicial >= fecha_inicial
            ):
                return "Las fechas tienen conflicto con las de otro menu", 400

        nuevo_menu_semana = MenuSemana(
            nombre=request.json["nombre"],
            fecha_inicial=fecha_inicial,
            fecha_final=fecha_final,
            id_restaurante=id_restaurante,
            id_usuario=id_usuario,
        )
        for receta_id in request.json["recetas"]:
            receta_menu = MenuReceta(menu=nuevo_menu_semana.id, receta=receta_id["id"])
            nuevo_menu_semana.recetas.append(receta_menu)
        db.session.add(nuevo_menu_semana)
        db.session.commit()
        return menu_semana_schema.dump(nuevo_menu_semana), 200
