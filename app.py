from flask import Flask, render_template, redirect, url_for, request, flash
from models import db, User, Stats, DecisionLog

app = Flask(__name__)

app.config["SECRET_KEY"] = "dev"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


def seed_data():
    """Cria um usuário e stats iniciais se o banco estiver vazio."""
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
        stress=72,
    )
    db.session.add(stats)
    db.session.commit()


@app.route("/")
def home():
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    user = User.query.first()
    stats = Stats.query.first()
    logs = DecisionLog.query.order_by(DecisionLog.created_at.desc()).limit(5).all()

    if not user or not stats:
        return redirect(url_for("login"))

    return render_template("dashboard.html", user=user, stats=stats, logs=logs)


@app.route("/choose", methods=["POST"])
def choose():
    choice = request.form.get("choice")  # "A", "B" ou "C"

    user = User.query.first()
    stats = Stats.query.first()
    if not user or not stats:
        flash("Usuário/Stats não encontrados. Recarregue o app.", "info")
        return redirect(url_for("dashboard"))

    # deltas (impacto da decisão)
    delta_xp = 0
    delta_rep = 0
    delta_stress = 0
    msg = ""

    if choice == "A":
        delta_xp, delta_rep, delta_stress = 40, 5, 10
        msg = "Escolha A: +40 XP, +5 Reputação, +10 Stress."
    elif choice == "B":
        delta_xp, delta_rep, delta_stress = 20, -2, 6
        msg = "Escolha B: +20 XP, -2 Reputação, +6 Stress."
    elif choice == "C":
        delta_xp, delta_rep, delta_stress = -10, -6, -8
        msg = "Escolha C: -10 XP, -6 Reputação, -8 Stress."
    else:
        flash("Escolha inválida.", "info")
        return redirect(url_for("dashboard"))

    # aplica alterações
    stats.xp += delta_xp
    stats.reputation += delta_rep
    stats.stress += delta_stress

    # travas para não quebrar UI
    stats.reputation = max(0, min(100, stats.reputation))
    stats.stress = max(0, min(100, stats.stress))
    stats.xp = max(0, stats.xp)

    # level up simples
    while stats.xp >= stats.xp_max:
        stats.xp -= stats.xp_max
        stats.level += 1
        stats.xp_max = int(stats.xp_max * 1.15)
        stats.salary += 500

    # salva histórico
    log = DecisionLog(
        user_id=user.id,
        choice=choice,
        delta_xp=delta_xp,
        delta_reputation=delta_rep,
        delta_stress=delta_stress,
    )
    db.session.add(log)

    db.session.commit()
    flash(msg, "info")
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
        .limit(10)
        .all()
    )
    return render_template("ranking.html", ranking=ranking_data)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed_data()
    app.run(debug=True)