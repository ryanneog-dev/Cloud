import pyotp
from app import Projects, User, create_app, db

def test_authentication_and_rbac(tmp_path):
    app = create_app({"TESTING": True, "SECRET_KEY": "test", "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}"})
    with app.app_context():
        db.drop_all(); db.create_all()
        user = User(username="supervisor", role="supervisor", totp_secret="JBSWY3DPEHPK3PXP")
        user.set_password("CorrectHorseBatteryStaple!")
        db.session.add(user); db.session.commit()
        assert user.password_hash != "CorrectHorseBatteryStaple!"
        assert user.password_hash.startswith("$2")
    client = app.test_client()
    assert client.post("/api/projects", json={"title":"A","desc":"B"}).status_code == 401
    assert client.post("/api/auth/login", json={"username":"supervisor","password":"wrong","totp":"000000"}).status_code == 401
    login = client.post("/api/auth/login", json={"username":"supervisor","password":"CorrectHorseBatteryStaple!","totp":pyotp.TOTP("JBSWY3DPEHPK3PXP").now()})
    assert login.status_code == 200
    created = client.post("/api/projects", json={"title":"Peak shift","desc":"Factory project"})
    assert created.status_code == 201
    ident = created.get_json()["project"]["sno"]
    assert client.put(f"/api/projects/{ident}", json={"title":"Updated","desc":"Updated"}).status_code == 200
    assert client.delete(f"/api/projects/{ident}").status_code == 200

def test_read_api_and_health(tmp_path):
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'read.db'}"})
    with app.app_context(): db.drop_all(); db.create_all(); db.session.add(Projects(title="Read", desc="Only")); db.session.commit()
    client = app.test_client()
    assert client.get("/health/instance").get_json()["status"] == "healthy"
    assert len(client.get("/api/projects").get_json()) == 1
