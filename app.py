from flask import Flask, render_template, redirect, url_for

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev" #banco de dados 

#rotas 
@app.route("/")
def home():
     return redirect(url_for("dashboard"))

@app.route("dashboard")
def dashboard():
     return redirect(url_for("dashboard.html"))

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/ranking")
def ranking():
    return render_template("ranking.html")

if __name__ == "__main__":
    app.run(debug=True)