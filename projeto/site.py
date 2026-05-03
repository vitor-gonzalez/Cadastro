from flask import Flask, render_template, request, redirect, url_for, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from db import db
from table import Usuario
import hashlib
from authlib.integrations.flask_client import OAuth
import random
import os


app = Flask(__name__)
lm = LoginManager(app)
lm.login_view = 'registrar'
app.secret_key = os.getenv("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.db"
db.init_app(app)
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'

oauth = OAuth(app)
facebook = oauth.register(
    name='facebook',
    client_id=  os.getenv("ID"),
    client_secret= os.getenv("CLIENT_KEY"),
    access_token_url='https://graph.facebook.com/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    api_base_url='https://graph.facebook.com/',
    client_kwargs={'scope': 'email'},
)

def hash(txt):
    hash_obj = hashlib.sha256(txt.encode('utf-8'))
    return hash_obj.hexdigest()




@lm.user_loader
def user_loader(id):
    usuario =   db.session.query(Usuario).filter_by(id=id).first()
    return usuario




menor_num = 1
maior_num = 100

@app.route('/guess', methods=['GET', 'POST'])
@login_required
def home():
    if "numero" not in session:
        session["numero"] = random.randint(menor_num, maior_num)
        session["tentativas"] = 0

    mensagem = ""

    if request.method == "POST":
        palpite = int(request.form["palpite"])
        session["tentativas"] += 1
        if palpite < menor_num or palpite > maior_num:
            mensagem = "Esse numero está fora do intervalo!"
        elif palpite < session["numero"]:
            mensagem = "Muito baixo!"
        elif palpite > session["numero"]:
            mensagem = "Muito alto!"
        else:
            mensagem = f"Acertou em {session['tentativas']} tentativas!"
            session.pop("numero")  # reinicia o jogo

    return render_template("home.html", mensagem=mensagem, menor_num=menor_num, maior_num=maior_num)
    

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        email = request.form['emailForm']
        senha = request.form['senhaForm']
        
        user = db.session.query(Usuario).filter_by(email=email, senha=hash(senha)).first()
        if not user:
            return render_template('login.html', falha="Email ou senha incorretos!")
        
        login_user(user)
        return redirect(url_for('home'))
    
@app.route("/login_facebook")
def login_facebook():

    return facebook.authorize_redirect(
        redirect_uri= "https://effective-stinking-stilt.ngrok-free.dev/callback"
    )

def get_db():
    return SQLAlchemy.connect("database.db")


@app.route("/callback")
def callback():
   
    
    token = facebook.authorize_access_token()
    resp = facebook.get("me?fields=id,name,email")
    user_data = resp.json()
    nome = user_data.get("name")

    facebook_id = user_data["id"]
    email = user_data.get("email")

    user = Usuario.query.filter_by(facebook_id=facebook_id).first()

    if not user:
        user = Usuario.query.filter_by(email=email).first()

        if user:
            user.facebook_id = facebook_id
            user.nome = nome
        else:
            user = Usuario(email=email, facebook_id=facebook_id, nome=nome)
            db.session.add(user)

        db.session.commit()

    login_user(user)

    return redirect(url_for("home"))




@app.route('/', methods=['GET', 'POST'])
def registrar():
    if request.method == 'GET':
        return render_template('registrar.html')
    elif request.method == 'POST':
        nome = request.form['nomeForm']
        email = request.form['emailForm']
        senha = request.form['senhaForm']
        email_exis = db.session.query(Usuario).filter_by(email=email).first()
        if email_exis:
            return render_template('registrar.html', erro="Email já existente")
        else:
            novo_usuario =Usuario(nome=nome, email=email, senha=hash(senha)) 
            db.session.add(novo_usuario)   
            db.session.commit()

            login_user(novo_usuario)

        return redirect(url_for('home'))
    
    
    
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


 

if __name__ == "__main__":  
    with app.app_context():
        
        db.create_all()
    app.run(debug=True)



