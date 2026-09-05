from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///Projects.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Projects(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    desc = db.Column(db.String(500), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"{self.sno} - {self.title}"

@app.route('/', methods=['GET','POST'])
def hello_world():
    if request.method=='POST':
        title = (request.form['title'])
        desc = (request.form['desc'])

        projects = Projects(title=title, desc=desc)
        db.session.add(projects)
        db.session.commit()
    allProjects = Projects.query.all()
    return render_template('index.html', allProjects = allProjects)
    

@app.route('/show')
def show():
    allProjects = Projects.query.all()
    print(allProjects)
    return 'This is the first product!'

@app.route('/update/<int:sno>', methods=['GET','POST'])
def update(sno):
    if request.method=='POST':
        title = (request.form['title'])
        desc = (request.form['desc'])
        projects = Projects.query.filter_by(sno=sno).first()
        projects.title = title
        projects.desc = desc
        db.session.add(projects)
        db.session.commit()
        return redirect("/")

    projects = Projects.query.filter_by(sno=sno).first()
    return render_template('update.html', projects = projects)

@app.route('/delete/<int:sno>')
def delete(sno):
    allProjects = Projects.query.filter_by(sno=sno).first()
    db.session.delete(allProjects)
    db.session.commit()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)