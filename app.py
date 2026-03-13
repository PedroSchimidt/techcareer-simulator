import random
from flask import Flask, render_template, redirect, url_for, request, flash, session
from models import db, User, Stats, DecisionLog

app = Flask(__name__)

app.config["SECRET_KEY"] = "dev"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# -----------------------------
# DESAFIOS DINÂMICOS
# -----------------------------
challenges = [
    {
        "id": 1,
        "title": "Incidente em produção",
        "prompt": "O servidor caiu em produção. O que você faz?",
        "a": {
            "text": "Revisar logs e métricas",
            "xp": 40,
            "rep": 5,
            "stress": 10
        },
        "b": {
            "text": "Reiniciar o servidor imediatamente",
            "xp": 20,
            "rep": -2,
            "stress": 6
        },
        "c": {
            "text": "Tomar um café e esperar alguém falar",
            "xp": -10,
            "rep": -6,
            "stress": -8
        }
    },
    {
        "id": 2,
        "title": "Pull Request gigante",
        "prompt": "Você recebeu um PR enorme e sem testes. O que faz?",
        "a": {
            "text": "Pede ajustes e sugere testes",
            "xp": 35,
            "rep": 6,
            "stress": 8
        },
        "b": {
            "text": "Aprova rápido para não atrasar a sprint",
            "xp": 15,
            "rep": -4,
            "stress": 5
        },
        "c": {
            "text": "Ignora e deixa para depois",
            "xp": -12,
            "rep": -7,
            "stress": -3
        }
    },
    {
        "id": 3,
        "title": "Bug crítico do cliente",
        "prompt": "Um cliente relatou um bug crítico em produção. Como você reage?",
        "a": {
            "text": "Reproduz o bug e cria um hotfix",
            "xp": 45,
            "rep": 8,
            "stress": 12
        },
        "b": {
            "text": "Responde que vai olhar depois",
            "xp": 10,
            "rep": -5,
            "stress": 2
        },
        "c": {
            "text": "Fecha o ticket sem investigar",
            "xp": -15,
            "rep": -10,
            "stress": -4
        }
    }
]


# -----------------------------
# DADOS INICIAIS
# -----------------------------
def seed_data():
    if User.query.first():
        return

    user = User(username="PedroDev")
    db.session.add(user)
    db.session.commit()

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


# -----------------------------
# ROTAS
# -----------------------------
@app.route("/")
def home():
    session.clear()
    return render_template("home.html")


@app.route("/dashboard")
def dashboard():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))
    user = User.query.get(user_id)
    stats = Stats.query.filter_by(user_id=user_id).first()
    logs = (
    DecisionLog.query
    .filter_by(user_id=user_id)
    .order_by(DecisionLog.created_at.desc())
    .limit(5)
    .all()
)

    if not user or not stats:
        return redirect(url_for("login"))

    current_challenge = random.choice(challenges)

    achievements = []

    if len(logs) >= 1:
        achievements.append("Primeiro passo")
    if stats.level >= 4:
        achievements.append("Em ascensão")
    if stats.reputation >= 80:
        achievements.append("Boa reputação")
    if stats.stress >= 95:
        achievements.append("Burnout")
    if stats.xp >= stats.xp_max * 0.8:
        achievements.append("Quase lá")

    return render_template(
        "dashboard.html",
        user=user,
        stats=stats,
        logs=logs,
        current_challenge=current_challenge,
        achievements=achievements
    )


@app.route("/choose", methods=["POST"])
def choose():
    choice = request.form.get("choice")
    challenge_id = request.form.get("challenge_id", type=int)

    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("login"))

    stats = Stats.query.filter_by(user_id=user_id).first()
    challenge = next((c for c in challenges if c["id"] == challenge_id), None)
    
    if not challenge:
        flash("Desafio não encontrado.", "info")
        return redirect(url_for("dashboard"))

    selected_option = challenge[choice.lower()]

    delta_xp = selected_option["xp"]
    delta_rep = selected_option["rep"]
    delta_stress = selected_option["stress"]

    stats.xp += delta_xp
    stats.reputation += delta_rep
    stats.stress += delta_stress

    # limites para não quebrar a interface
    stats.reputation = max(0, min(100, stats.reputation))
    stats.stress = max(0, min(100, stats.stress))
    stats.xp = max(0, stats.xp)

    # level up
    while stats.xp >= stats.xp_max:
        stats.xp -= stats.xp_max
        stats.level += 1
        stats.xp_max = int(stats.xp_max * 1.15)
        stats.salary += 500

    log = DecisionLog(
    user_id=stats.user_id,
    choice=choice,
    delta_xp=delta_xp,
    delta_reputation=delta_rep,
    delta_stress=delta_stress,
    challenge_title=challenge["title"]
)
    db.session.add(log)

    db.session.commit()

    flash(
        f"Escolha {choice}: XP {delta_xp}, Reputação {delta_rep}, Stress {delta_stress}.",
        "info"
    )

    return redirect(url_for("dashboard"))

@app.route("/reset", methods=["POST"])
def reset():
    stats = Stats.query.first()

    if not stats:
        return redirect(url_for("dashboard"))

    # apaga histórico
    DecisionLog.query.delete()

    # reseta os atributos
    stats.level = 3
    stats.xp = 850
    stats.xp_max = 1200
    stats.salary = 7500
    stats.reputation = 68
    stats.stress = 72

    db.session.commit()

    flash("Progresso resetado com sucesso.", "info")
    return redirect(url_for("dashboard"))


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user and password == "123":  # login provisório

            session["user_id"] = user.id

            flash("Login realizado com sucesso!", "success")
            return redirect(url_for("dashboard"))

        flash("Usuário ou senha inválidos.", "danger")

    return render_template("login.html")

@app.route("/logout")
def logout():

    session.clear()

    flash("Logout realizado.", "info")
    return redirect(url_for("home"))


@app.route("/ranking")
def ranking():
    ranking_data = (
        db.session.query(User.username, Stats.level, Stats.salary)
        .join(Stats, Stats.user_id == User.id)
        .order_by(Stats.salary.desc())
        .limit(10)
        .all()
    )
    return render_template("ranking.html", ranking=ranking_data)



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed_data()
    app.run(debug=True)