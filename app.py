from flask import Flask, render_template, redirect, url_for

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev" #banco de dados 

#rotas 

@app.route("/")
def home():