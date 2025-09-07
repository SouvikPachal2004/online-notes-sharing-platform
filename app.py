from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime

# --------- CONFIG ---------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "ppt", "pptx", "txt", "jpg", "jpeg", "png"}

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-secret-key"  # TODO: set strong secret in production
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "notes.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"


# --------- MODELS ---------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.relationship("Note", backref="author", lazy=True, cascade="all, delete")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    downloads = db.Column(db.Integer, default=0)

    def file_ext(self):
        return os.path.splitext(self.filename)[1].lower().replace(".", "")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --------- HELPERS ---------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


DEFAULT_CATEGORIES = [
    "Mathematics",
    "Computer Science",
    "Physics",
    "Chemistry",
    "Biology",
    "Humanities",
    "Other",
]


# --------- ROUTES ---------
@app.route("/")
def index():
    q = request.args.get("q", "", type=str).strip()
    category = request.args.get("category", "", type=str).strip()
    sort = request.args.get("sort", "recent", type=str)

    notes_query = Note.query

    if q:
        like = f"%{q}%"
        notes_query = notes_query.filter(
            db.or_(Note.title.ilike(like), Note.description.ilike(like))
        )

    if category:
        notes_query = notes_query.filter_by(category=category)

    if sort == "popular":
        notes_query = notes_query.order_by(Note.downloads.desc(), Note.upload_date.desc())
    else:
        notes_query = notes_query.order_by(Note.upload_date.desc())

    notes = notes_query.limit(30).all()

    return render_template("index.html", notes=notes, categories=DEFAULT_CATEGORIES, q=q, selected_category=category, sort=sort)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").lower().strip()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("All fields are required.", "error")
            return redirect(url_for("register"))

        if User.query.filter_by(email=email).first():
            flash("Email already registered. Please log in.", "error")
            return redirect(url_for("login"))

        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").lower().strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Welcome back!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid email or password.", "error")
            return redirect(url_for("login"))
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "success")
    return redirect(url_for("index"))


@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "").strip()
        file = request.files.get("file")

        if not title or not category or not file:
            flash("Title, category and file are required.", "error")
            return redirect(url_for("upload"))

        if category not in DEFAULT_CATEGORIES:
            flash("Invalid category.", "error")
            return redirect(url_for("upload"))

        if not allowed_file(file.filename):
            flash("File type not allowed.", "error")
            return redirect(url_for("upload"))

        safe_name = secure_filename(file.filename)
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        stored_name = f"{current_user.id}_{timestamp}_{safe_name}"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], stored_name)
        file.save(filepath)

        note = Note(
            user_id=current_user.id,
            title=title,
            description=description,
            category=category,
            filename=stored_name,
        )
        db.session.add(note)
        db.session.commit()
        flash("Note uploaded successfully.", "success")
        return redirect(url_for("index"))

    return render_template("upload.html", categories=DEFAULT_CATEGORIES)


@app.route("/notes")
def notes_list():
    # Convenience route to list (same as index but with pagination placeholder)
    return redirect(url_for("index"))


@app.route("/download/<int:note_id>")
def download(note_id):
    note = Note.query.get_or_404(note_id)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], note.filename)
    if not os.path.exists(file_path):
        abort(404)

    # increment downloads
    note.downloads = (note.downloads or 0) + 1
    db.session.commit()

    return send_from_directory(app.config["UPLOAD_FOLDER"], note.filename, as_attachment=True)


@app.route("/profile")
@login_required
def profile():
    user_notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.upload_date.desc()).all()
    return render_template("profile.html", notes=user_notes)


@app.route("/delete/<int:note_id>", methods=["POST"])
@login_required
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        abort(403)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], note.filename)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        pass
    db.session.delete(note)
    db.session.commit()
    flash("Note deleted.", "success")
    return redirect(url_for("profile"))


@app.errorhandler(404)
def not_found(e):
    return render_template(
        "base.html",
        content="<div class='p-6 text-center'><h2 class='text-2xl font-semibold'>404 - Not Found</h2><p class='mt-2 text-muted'>The page you are looking for does not exist.</p></div>"
    ), 404


# --- Initialize database at startup (Flask 3.x compatible) ---
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
