from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)

    stats = db.relationship("Stats", backref="user", uselist=False)

class Stats(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True)

    level = db.Column(db.Integer, default=1)
    xp = db.Column(db.Integer, default=0)
    xp_max = db.Column(db.Integer, default=100)

    salary = db.Column(db.Integer, default=2000)
    reputation = db.Column(db.Integer, default=50)
    stress = db.Column(db.Integer, default=10)