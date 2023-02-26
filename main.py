from flask import Flask, render_template, request, url_for, redirect, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user

app = Flask(__name__)

app.config['SECRET_KEY'] = 'any-secret-key-you-choose'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)


##CREATE TABLE IN DB
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))


# Line below only required once, when creating DB.
# with app.app_context():
#     db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(entity=User, ident=user_id)


@app.route('/')
def home():
    return render_template("index.html")


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        hashed_password = generate_password_hash(password=request.form["password"],
                                                 salt_length=8,
                                                 method="pbkdf2:sha256")
        if db.session.execute(db.select(User).filter_by(email=request.form["email"])).scalar_one_or_none() is None:

            # Check if email exists in the database, if it didn't, add the data to the database
            new_user = User(name=request.form["name"],
                            email=request.form["email"],
                            password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for("secrets", name=new_user.name))
        else:

            # If email exists, redirect user to log in
            flash(f"Email: '{request.form['email']}' already exists! Please log in instead.")
            return redirect(url_for("login"))
    return render_template("register.html")


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]

        # Check if email exists in the database, if it didn't, user_data will return None
        user_data = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()
        if user_data is None:
            flash("That email does not exist, please try again.")
        elif check_password_hash(pwhash=user_data.password, password=request.form["password"]):
            # Comparing password hash to the password hash in the database
            login_user(user_data)
            return redirect(url_for("secrets", current_user=user_data))
        else:
            flash("Password incorrect, please try again.")
    return render_template("login.html")


@app.route('/secrets')
@login_required
def secrets():
    return render_template("secrets.html", current_user=current_user)


@app.route('/logout')
@login_required
def logout():
    # logout user
    logout_user()
    return redirect(url_for("home"))


@app.route('/download')
@login_required
def download():
    # download file from a specific directory
    return send_from_directory(directory=app.static_folder, path="files/cheat_sheet.pdf")


if __name__ == "__main__":
    app.run(debug=True)
