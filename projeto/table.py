from db import db
from flask_login import UserMixin # guarda os metodos/funcionalidades

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    facebook_id = db.Column(db.String())
    nome = db.Column(db.String(30))
    email = db.Column(db.String(30), unique=True)
    senha = db.Column(db.String())
    