import random
from datetime import datetime, timezone, timedelta
from flask import Flask, render_template, redirect, url_for, request, flash, session
from models import db, User, Stats, DecisionLog

app = Flask(__name__)

BRASILIA = timezone(timedelta(hours=-3))


def format_brasilia(dt):
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    br = dt.astimezone(BRASILIA)
    return br.strftime("%d/%m %H:%M")


app.jinja_env.filters["brasilia"] = format_brasilia

app.config["SECRET_KEY"] = "dev"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# -----------------------------
# DESAFIOS (XP AUMENTADO)
# -----------------------------
challenges = [
    {
        "id": 1,
        "title": "Incidente em produção",
        "prompt": "O servidor caiu em produção. O que você faz?",
        "a": {"text": "Revisar logs e métricas", "xp": 70, "rep": 8, "stress": 12},
        "b": {"text": "Reiniciar o servidor", "xp": 40, "rep": -2, "stress": 8},
        "c": {"text": "Esperar alguém resolver", "xp": -25, "rep": -6, "stress": -5}
    },
    {
        "id": 2,
        "title": "Pull Request gigante",
        "prompt": "Você recebeu um PR enorme.",
        "a": {"text": "Pede testes", "xp": 60, "rep": 7, "stress": 10},
        "b": {"text": "Aprova rápido", "xp": 30, "rep": -4, "stress": 6},
        "c": {"text": "Ignora", "xp": -20, "rep": -7, "stress": -2}
    },
    {
        "id": 3,
        "title": "Bug crítico",
        "prompt": "Cliente encontrou um bug grave!",
        "a": {"text": "Corrigir imediatamente", "xp": 80, "rep": 10, "stress": 15},
        "b": {"text": "Colocar na backlog", "xp": 35, "rep": -5, "stress": 5},
        "c": {"text": "Ignorar", "xp": -30, "rep": -10, "stress": -6}
    }
]

# -----------------------------
# SEED
# -----------------------------
def seed_data():
    if User.query.first():
        return

    user = User(username="PedroDev")
    db.session.add(user)
    db.session.commit()

    stats = Stats(
        user_id=user.id,
        level=1,
        xp=0,
        xp_max=300,
        salary=3500,
        reputation=60,
        stress=50
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

    if not user or not stats:
        return redirect(url_for("login"))

    logs = (
        DecisionLog.query
        .filter_by(user_id=user_id)
        .order_by(DecisionLog.created_at.desc())
        .limit(5)
        .all()
    )

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

    if not choice:
        flash("Escolha inválida.", "danger")
        return redirect(url_for("dashboard"))

    stats = Stats.query.filter_by(user_id=user_id).first()

    if not stats:
        return redirect(url_for("login"))

    challenge = next((c for c in challenges if c["id"] == challenge_id), None)

    if not challenge:
        flash("Desafio não encontrado.", "danger")
        return redirect(url_for("dashboard"))

    selected_option = challenge.get(choice.lower())

    if not selected_option:
        flash("Opção inválida.", "danger")
        return redirect(url_for("dashboard"))

    delta_xp = selected_option["xp"]
    delta_rep = selected_option["rep"]
    delta_stress = selected_option["stress"]

    # BONUS XP
    if delta_xp > 0:
        delta_xp += 10

    stats.xp += delta_xp
    stats.reputation += delta_rep
    stats.stress += delta_stress

    stats.reputation = max(0, min(100, stats.reputation))
    stats.stress = max(0, min(100, stats.stress))
    stats.xp = max(0, stats.xp)

    # LEVEL UP MELHORADO
    while stats.xp >= stats.xp_max:
        stats.xp -= stats.xp_max
        stats.level += 1
        stats.xp_max = int(stats.xp_max * 1.10)
        stats.salary += 800

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

    flash(f"Escolha {choice}: XP {delta_xp}", "info")

    return redirect(url_for("dashboard"))


@app.route("/reset", methods=["POST"])
def reset():
    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("login"))

    stats = Stats.query.filter_by(user_id=user_id).first()

    if not stats:
        return redirect(url_for("dashboard"))

    DecisionLog.query.filter_by(user_id=user_id).delete()

    stats.level = 1
    stats.xp = 0
    stats.xp_max = 300
    stats.salary = 3500
    stats.reputation = 60
    stats.stress = 50

    db.session.commit()

    flash("Progresso resetado.", "info")
    return redirect(url_for("dashboard"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user and password == "123":
            session["user_id"] = user.id
            return redirect(url_for("dashboard"))

        flash("Login inválido.", "danger")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")

        if User.query.filter_by(username=username).first():
            flash("Usuário já existe.", "danger")
            return redirect(url_for("register"))

        new_user = User(username=username)
        db.session.add(new_user)
        db.session.commit()

        stats = Stats(
            user_id=new_user.id,
            level=1,
            xp=0,
            xp_max=300,
            salary=3500,
            reputation=60,
            stress=50
        )

        db.session.add(stats)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
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