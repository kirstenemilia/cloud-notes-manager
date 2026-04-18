from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from extensions import db
from models import NoteModel, UserModel
from flask_restful import Resource, Api, reqparse, fields, marshal_with, abort
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "instance", "database.db")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path
db.init_app(app)
api = Api(app)

app.config["JWT_SECRET_KEY"] = "dev-secret-key"
jwt = JWTManager(app)

note_args = reqparse.RequestParser()
note_args.add_argument('title', type=str, required=True, help="Title required")
note_args.add_argument('content', type=str, required=True, help="Content required")

auth_args = reqparse.RequestParser()
auth_args.add_argument('username', type=str, required=True)
auth_args.add_argument('password', type=str, required=True)

noteFields = {
    'id': fields.Integer,
    'title': fields.String,
    'content': fields.String,
}

class Notes(Resource):

    @jwt_required()
    @marshal_with(noteFields)
    def get(self):
        user_id = get_jwt_identity()
        return NoteModel.query.filter_by(user_id=user_id).all()

    @jwt_required()
    @marshal_with(noteFields)
    def post(self):
        user_id = get_jwt_identity()
        args = note_args.parse_args()

        note = NoteModel(
            title=args["title"],
            content=args["content"],
            user_id=user_id
        )

        db.session.add(note)
        db.session.commit()
        return note, 201


class Note(Resource):

    @jwt_required()
    @marshal_with(noteFields)
    def get(self, id):
        user_id = get_jwt_identity()
        note = NoteModel.query.filter_by(id=id, user_id=user_id).first()
        if not note:
            abort(404, "Note not found")
        return note

    @jwt_required()
    @marshal_with(noteFields)
    def patch(self, id):
        user_id = get_jwt_identity()
        args = note_args.parse_args()

        note = NoteModel.query.filter_by(id=id, user_id=user_id).first()
        if not note:
            abort(404, "Note not found")

        if args["title"]:
            note.title = args["title"]
        if args["content"]:
            note.content = args["content"]

        db.session.commit()
        return note

    @jwt_required()
    def delete(self, id):
        user_id = get_jwt_identity()
        note = NoteModel.query.filter_by(id=id, user_id=user_id).first()
        if not note:
            abort(404, "Note not found")

        db.session.delete(note)
        db.session.commit()
        return "", 204


class Register(Resource):
    def post(self):
        args = auth_args.parse_args()

        if UserModel.query.filter_by(username=args["username"]).first():
            return {"message": "User already exists"}, 400

        user = UserModel(username=args["username"])
        user.set_password(args["password"])

        db.session.add(user)
        db.session.commit()

        return {"message": "User created"}, 201


class Login(Resource):
    def post(self):
        args = auth_args.parse_args()

        user = UserModel.query.filter_by(username=args["username"]).first()

        if not user or not user.check_password(args["password"]):
            return {"message": "Invalid credentials"}, 401

        token = create_access_token(identity=str(user.id))

        return {"access_token": token}, 200


api.add_resource(Notes, '/api/notes/')
api.add_resource(Note, '/api/notes/<int:id>')
api.add_resource(Register, '/api/register')
api.add_resource(Login, '/api/login')


@app.route('/')
def home():
    return '<h1>Flask REST API </h1>'


if __name__ == '__main__':
    app.run(debug=True)