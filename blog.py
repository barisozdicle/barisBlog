from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
import pymongo
from pymongo import MongoClient
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash(message="Bu Sayfayi goruntulemek icin lutfen giris yapin", category="danger")
            return redirect(url_for("login"))

    return decorated_function


app = Flask(__name__)
app.secret_key = "baris"

app.config["cluster"] = MongoClient(
    "mongodb+srv://bozdicle:123@cluster1.sdkt0.mongodb.net/BlogDB?retryWrites=true&w=majority")
app.config["db"] = app.config["cluster"]["BlogDB"]
app.config["users"] = app.config["db"]["Users"]
app.config["articles"] = app.config["db"]["Articles"]


class RegisterForm(Form):
    name = StringField("Name Surname", validators=[validators.length(min=4, max=30)])
    username = StringField("Nickname", validators=[validators.length(min=4, max=30)])
    email = StringField("Email", validators=[validators.Email(message="Please Enter Valid E-Mail")])
    password = PasswordField("Password", validators=[
        validators.data_required(message="Please Assign Password"),
        validators.EqualTo(fieldname="confirm", message="Password Uyusmuyor")
    ])
    confirm = PasswordField("Parola Dogrula")


class LoginForm(Form):
    username = StringField("Kullanici Adi")
    password = StringField("Parola")


@app.route("/")
def index():
    articles = [
        {"id": 1, "title": "Deneme1", "content": "deneme1 content"},
        {"id": 2, "title": "Deneme2", "content": "deneme2 content"},
        {"id": 3, "title": "Deneme3", "content": "deneme3 content"}
    ]
    return render_template("index.html", articles=articles)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/articles")
def articles():
    count = app.config["articles"].count_documents({})

    if count > 0:
        articles = app.config["articles"].find({})
        return render_template("articles.html", articles=articles)
    else:
        return render_template("articles.html")


@app.route("/article/<string:id>")
def detail(id):
    return "Article ID : " + id


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        post = {
            "name": "{}".format(name),
            "email": "{}".format(email),
            "username": "{}".format(username),
            "password": "{}".format(password)
        }

        app.config["users"].insert_one(post)
        # TODO messages.html de ki category calismiyor. Success ise yesil gorunmesi lazimdi
        flash(message="Basariyla Kayit Olundu", category="success")

        return redirect(url_for("login"))
    else:
        return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data

        count = app.config["users"].count_documents({"username": "{}".format(username)})

        if count > 0:
            real_password = app.config["users"].find_one({"username": "{}".format(username)})['password']
            if sha256_crypt.verify(password_entered, real_password):
                flash(message="Basariyla giris yaptiniz", category="success")
                session["logged_in"] = True
                session["username"] = username

                return redirect(url_for("index"))
            else:
                flash(message="Parolanizi Yanlis Girdiniz", category="danger")
                return redirect(url_for("login"))
        else:
            flash(message="Boyle bir kullanici bulunmuyor.", category="danger")
            return redirect(url_for("login"))

    return render_template("login.html", form=form)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route("/dashboard")
@login_required
def dashboard():
    query = app.config["articles"].find({"username": "{}".format(session["username"])})
    return render_template("dashboard.html")


@app.route("/addArticle", methods=["GET", "POST"])
def add_article():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data
        post = {
            "title": "{}".format(title),
            "author": "{}".format(session["username"]),
            "content": "{}".format(content)
        }

        app.config["articles"].insert_one(post)

        flash(message="Makale Basariyla Eklendi", category="success")
        return redirect(url_for("dashboard"))

    return render_template("addArticle.html", form=form)


class ArticleForm(Form):
    title = StringField("Makale Basligi", validators=[validators.Length(min=5, max=100)])
    content = TextAreaField("Makale Icerigi", validators=[validators.Length(min=10)])


if __name__ == "__main__":
    app.run(debug=True)
