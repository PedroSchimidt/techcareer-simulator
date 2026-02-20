from flask import Flask, render_template, redirect, url_for, request
from models import db, User, Stats

app = Flask(__name__)

# CONFIGURAÇÃO DO APP
app.config["SECRET_KEY"] = "dev"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# INICIALIZA O BANCO COM O APP
db.init_app(app)

# -----------------------------------
# FUNÇÃO PARA CRIAR DADOS INICIAIS
# -----------------------------------

def seed_data():
    # Se já existir usuário, não cria de novo
    if User.query.first():
        return

    # Criando usuário
    user = User(username="PedroDev")
    db.session.add(user)
    db.session.commit()

    # Criando stats ligados ao usuário
    stats = Stats(
        user_id=user.id,
        level=3,
        xp=850,
        xp_max=1200,
        salary=7500,
        reputation=68,
        stress=72
    )
    db.session.add(stats)
    db.session.commit()

# -----------------------------------
# ROTAS
# -----------------------------------

@app.route("/")
def home():
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
def dashboard():
    user = User.query.first()
    stats = Stats.query.first()

    if not user or not stats:
        return redirect(url_for("login"))

    return render_template("dashboard.html", user=user, stats=stats)
@app.route("/choose", methods=["POST"])
def choose():
    choice = request.form.get("choice")  # "A", "B" ou "C"

    stats = Stats.query.first()
    if not stats:
        return redirect(url_for("dashboard"))

    # Regras simples (depois a gente melhora)
    if choice == "A":
        stats.xp += 40
        stats.reputation += 5
        stats.stress += 10
    elif choice == "B":
        stats.xp += 20
        stats.reputation -= 2
        stats.stress += 6
    elif choice == "C":
        stats.xp -= 10
        stats.reputation -= 6
        stats.stress -= 8

    # travas para não quebrar a UI
    stats.reputation = max(0, min(100, stats.reputation))
    stats.stress = max(0, min(100, stats.stress))
    stats.xp = max(0, stats.xp)

    # Se XP passar do máximo, sobe level (simples)
    while stats.xp >= stats.xp_max:
        stats.xp -= stats.xp_max
        stats.level += 1
        stats.xp_max = int(stats.xp_max * 1.15)  # aumenta um pouco a meta
        stats.salary += 500

    db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/ranking")
def ranking():
    ranking_data = (
        db.session.query(User.username, Stats.level, Stats.salary)
        .join(Stats, Stats.user_id == User.id)
        .order_by(Stats.salary.desc())
        .all()
    )

    return render_template("ranking.html", ranking=ranking_data)

# -----------------------------------
# INICIALIZA BANCO
# -----------------------------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed_data()

    app.run(debug=True)