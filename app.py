"""Secure, horizontally scalable Project Tracker application."""
from __future__ import annotations
import os, socket
from datetime import datetime
from functools import wraps
import bcrypt, pyotp
from flask import Flask, abort, jsonify, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(32), nullable=False, default="viewer")
    totp_secret = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    def set_password(self, password): self.password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    def check_password(self, password): return bcrypt.checkpw(password.encode(), self.password_hash.encode())

class Projects(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    desc = db.Column(db.String(500), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

def db_url(value):
    if value.startswith("postgres://"): return value.replace("postgres://", "postgresql+psycopg://", 1)
    if value.startswith("postgresql://"): return value.replace("postgresql://", "postgresql+psycopg://", 1)
    return value

def current_user():
    return db.session.get(User, session["user_id"]) if session.get("user_id") else None

def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = current_user()
            if not user: return jsonify({"error": "authentication required"}), 401
            if user.role not in roles: return jsonify({"error": "insufficient role"}), 403
            return view(*args, **kwargs)
        return wrapped
    return decorator

def project_json(p):
    return {"sno": p.sno, "title": p.title, "desc": p.desc, "date_created": p.date_created.isoformat()}

def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(SECRET_KEY=os.environ.get("SECRET_KEY", "change-me-in-production"), SQLALCHEMY_DATABASE_URI=db_url(os.environ.get("DATABASE_URL", "sqlite:///Projects.db")), SQLALCHEMY_TRACK_MODIFICATIONS=False, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax", SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "false").lower() == "true")
    if test_config: app.config.update(test_config)
    db.init_app(app)

    @app.get("/health/instance")
    def health_instance(): return jsonify({"status": "healthy", "instance": socket.gethostname()})

    @app.post("/api/auth/login")
    def api_login():
        data = request.get_json(silent=True) or {}; user = User.query.filter_by(username=data.get("username", "")).first(); otp = str(data.get("totp", "")).replace(" ", "")
        if not user or not user.check_password(str(data.get("password", ""))) or not pyotp.TOTP(user.totp_secret).verify(otp, valid_window=1): return jsonify({"error": "invalid username, password, or one-time code"}), 401
        session.clear(); session["user_id"] = user.id; session["role"] = user.role
        return jsonify({"message": "authenticated", "role": user.role})

    @app.post("/api/auth/logout")
    def api_logout(): session.clear(); return jsonify({"message": "logged out"})

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            user = User.query.filter_by(username=request.form.get("username", "")).first(); otp = request.form.get("totp", "").replace(" ", "")
            if user and user.check_password(request.form.get("password", "")) and pyotp.TOTP(user.totp_secret).verify(otp, valid_window=1):
                session.clear(); session["user_id"] = user.id; session["role"] = user.role; return redirect(url_for("home"))
            return render_template("login.html", error="Invalid credentials or one-time code"), 401
        return render_template("login.html")

    @app.get("/logout")
    def logout(): session.clear(); return redirect(url_for("login"))

    @app.route("/", methods=["GET", "POST"])
    def home():
        user = current_user()
        if request.method == "POST":
            if not user or user.role not in {"supervisor", "admin"}: abort(403)
            title, desc = request.form.get("title"), request.form.get("desc")
            if title and desc: db.session.add(Projects(title=title, desc=desc)); db.session.commit()
            return redirect(url_for("home"))
        return render_template("index.html", allProjects=Projects.query.order_by(Projects.sno).all(), user=user)

    @app.route("/update/<int:sno>", methods=["GET", "POST"])
    @role_required("supervisor", "admin")
    def update(sno):
        p = db.session.get(Projects, sno)
        if not p: return "Project not found", 404
        if request.method == "POST":
            title, desc = request.form.get("title"), request.form.get("desc")
            if title and desc: p.title, p.desc = title, desc; db.session.commit()
            return redirect(url_for("home"))
        return render_template("update.html", projects=p)

    @app.post("/delete/<int:sno>")
    @role_required("supervisor", "admin")
    def delete(sno):
        p = db.session.get(Projects, sno)
        if not p: return "Project not found", 404
        db.session.delete(p); db.session.commit(); return redirect(url_for("home"))

    @app.get("/api/projects")
    def api_get_projects(): return jsonify([project_json(p) for p in Projects.query.order_by(Projects.sno).all()])
    @app.get("/api/projects/<int:sno>")
    def api_get_project(sno):
        p = db.session.get(Projects, sno); return jsonify(project_json(p)) if p else (jsonify({"error": "Project not found"}), 404)
    @app.post("/api/projects")
    @role_required("supervisor", "admin")
    def api_create_project():
        data = request.get_json(silent=True) or {}
        if not data.get("title") or not data.get("desc"): return jsonify({"error": "Title and description are required"}), 400
        p = Projects(title=data["title"], desc=data["desc"]); db.session.add(p); db.session.commit(); return jsonify({"message": "Project created successfully", "project": project_json(p)}), 201
    @app.put("/api/projects/<int:sno>")
    @role_required("supervisor", "admin")
    def api_update_project(sno):
        p, data = db.session.get(Projects, sno), request.get_json(silent=True) or {}
        if not p: return jsonify({"error": "Project not found"}), 404
        if not data.get("title") or not data.get("desc"): return jsonify({"error": "Title and description are required"}), 400
        p.title, p.desc = data["title"], data["desc"]; db.session.commit(); return jsonify({"message": "Project updated successfully", "project": project_json(p)})
    @app.delete("/api/projects/<int:sno>")
    @role_required("supervisor", "admin")
    def api_delete_project(sno):
        p = db.session.get(Projects, sno)
        if not p: return jsonify({"error": "Project not found"}), 404
        db.session.delete(p); db.session.commit(); return jsonify({"message": "Project deleted successfully"})

    @app.cli.command("seed-supervisor")
    def seed_supervisor():
        username, password = os.environ.get("ADMIN_USERNAME"), os.environ.get("ADMIN_PASSWORD")
        if not username or not password: raise RuntimeError("Set ADMIN_USERNAME and ADMIN_PASSWORD; never commit them.")
        if User.query.filter_by(username=username).first(): raise RuntimeError("User already exists")
        user = User(username=username, role="supervisor", totp_secret=pyotp.random_base32()); user.set_password(password); db.session.add(user); db.session.commit(); print(f"TOTP secret for {username}: {user.totp_secret}")
    with app.app_context(): db.create_all()
    return app

app = create_app()
if __name__ == "__main__": app.run(host="0.0.0.0", port=5000)
