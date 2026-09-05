from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

# Use Neon PostgreSQL on Vercel.
# Fall back to local SQLite when DATABASE_URL is not set.
database_url = os.environ.get("DATABASE_URL", "sqlite:///Projects.db")

# Some providers may return the older postgres:// prefix.
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1) 
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Projects(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    desc = db.Column(db.String(500), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"{self.sno} - {self.title}"


@app.route("/", methods=["GET", "POST"])
def hello_world():
    if request.method == "POST":
        title = request.form.get("title")
        desc = request.form.get("desc")

        if title and desc:
            projects = Projects(title=title, desc=desc)
            db.session.add(projects)
            db.session.commit()

        return redirect("/")

    allProjects = Projects.query.all()
    return render_template("index.html", allProjects=allProjects)


@app.route("/show")
def show():
    allProjects = Projects.query.all()
    print(allProjects)
    return "This is the first product!"


@app.route("/update/<int:sno>", methods=["GET", "POST"])
def update(sno):
    projects = Projects.query.filter_by(sno=sno).first()

    if projects is None:
        return "Project not found", 404

    if request.method == "POST":
        title = request.form.get("title")
        desc = request.form.get("desc")

        if title and desc:
            projects.title = title
            projects.desc = desc
            db.session.commit()

        return redirect("/")

    return render_template("update.html", projects=projects)


@app.route("/delete/<int:sno>")
def delete(sno):
    project = Projects.query.filter_by(sno=sno).first()

    if project is None:
        return "Project not found", 404

    db.session.delete(project)
    db.session.commit()
    return redirect("/")


# Create the table automatically when the application starts.
# This is useful for this small hackathon project.
with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
