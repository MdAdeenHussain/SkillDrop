from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    language_preference = db.Column(db.String(10), nullable=False, default="en")

    progress = db.relationship("Progress", back_populates="user", cascade="all, delete-orphan")


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    icon = db.Column(db.String(20), nullable=False)

    lessons = db.relationship("Lesson", back_populates="category", cascade="all, delete-orphan")


class Lesson(db.Model):
    __tablename__ = "lessons"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    duration = db.Column(db.String(30), nullable=False)
    steps = db.Column(db.JSON, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)

    category = db.relationship("Category", back_populates="lessons")
    progress = db.relationship("Progress", back_populates="lesson", cascade="all, delete-orphan")


class Progress(db.Model):
    __tablename__ = "progress"
    __table_args__ = (
        db.UniqueConstraint("user_id", "lesson_id", name="uq_progress_user_lesson"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey("lessons.id"), nullable=False)
    completed = db.Column(db.Boolean, nullable=False, default=False)

    user = db.relationship("User", back_populates="progress")
    lesson = db.relationship("Lesson", back_populates="progress")
