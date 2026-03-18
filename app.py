import os
import re
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, url_for

from model import Category, Lesson, Progress, User, db


load_dotenv()

app = Flask(__name__)


def _database_uri():
    uri = os.getenv("DATABASE_URL", "sqlite:///skilldrop.db")
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    return uri


app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "skilldrop-dev-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = _database_uri()
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


CATEGORY_THEMES = {
    "Electrician": {
        "accent": "sun",
        "description": "Quick safety and wiring basics for everyday fixes.",
    },
    "Plumber": {
        "accent": "aqua",
        "description": "Easy repair lessons for leaks, pipes, and fittings.",
    },
    "Driver": {
        "accent": "violet",
        "description": "Road, vehicle, and trip habits that save time and fuel.",
    },
    "Construction": {
        "accent": "orange",
        "description": "Fast site-ready lessons for tools, safety, and workflow.",
    },
}

DEMO_DATA = [
    {
        "name": "Electrician",
        "icon": "⚡",
        "lessons": [
            {
                "title": "Switch Off Main Before Repair",
                "duration": "45 sec",
                "steps": [
                    "Find the main power switch and turn it off.",
                    "Use a tester to check that no current is flowing.",
                    "Wear dry gloves before touching any wire.",
                    "Repair the loose point and tighten it fully.",
                ],
            },
            {
                "title": "Check a Loose Plug Point",
                "duration": "55 sec",
                "steps": [
                    "Turn off power from the room circuit.",
                    "Open the face plate using an insulated screwdriver.",
                    "Tighten the live, neutral, and earth screws carefully.",
                    "Close the plate and test with a small appliance.",
                ],
            },
        ],
    },
    {
        "name": "Plumber",
        "icon": "🔧",
        "lessons": [
            {
                "title": "Fix a Leaking Tap Fast",
                "duration": "60 sec",
                "steps": [
                    "Close the water valve below the sink.",
                    "Remove the tap handle and take out the cartridge or washer.",
                    "Replace the worn washer or cartridge with the correct size.",
                    "Tighten the handle, open the valve, and check for leaks.",
                ],
            },
            {
                "title": "Clear a Slow Drain",
                "duration": "40 sec",
                "steps": [
                    "Remove visible dirt or hair from the drain cover.",
                    "Pour hot water slowly into the pipe.",
                    "Use a plunger with short strong pushes.",
                    "Rinse again and confirm the water flows smoothly.",
                ],
            },
        ],
    },
    {
        "name": "Driver",
        "icon": "🚚",
        "lessons": [
            {
                "title": "Daily Vehicle Safety Check",
                "duration": "50 sec",
                "steps": [
                    "Walk around the vehicle and inspect tires for damage.",
                    "Check mirrors, lights, and horn before starting.",
                    "Look at fuel, engine oil, and coolant levels.",
                    "Test the brakes slowly before joining traffic.",
                ],
            },
            {
                "title": "Save Fuel on City Routes",
                "duration": "35 sec",
                "steps": [
                    "Start smoothly and avoid sudden acceleration.",
                    "Keep a steady speed in lower traffic areas.",
                    "Switch off the engine during long idle stops.",
                    "Plan the route to avoid repeated U-turns and jams.",
                ],
            },
        ],
    },
    {
        "name": "Construction",
        "icon": "🏗️",
        "lessons": [
            {
                "title": "Wear PPE Before Site Entry",
                "duration": "30 sec",
                "steps": [
                    "Put on helmet, gloves, shoes, and safety vest.",
                    "Check if straps and buckles are tight.",
                    "Make sure tools are carried safely and not loose.",
                    "Enter the site only after supervisor clearance.",
                ],
            },
            {
                "title": "Lift Cement Bags Safely",
                "duration": "45 sec",
                "steps": [
                    "Stand close to the bag with feet shoulder-width apart.",
                    "Bend your knees and keep your back straight.",
                    "Hold the bag close to your body while lifting.",
                    "Turn with your feet, not with your waist.",
                ],
            },
        ],
    },
]

MOCK_AI_RESPONSES = {
    "en": {
        "leaking tap": [
            "Turn off the water valve first.",
            "Open the tap and remove the top handle.",
            "Replace the worn washer or cartridge.",
            "Tighten the tap, open water, and test again.",
        ],
        "shock": [
            "Turn off the main power immediately.",
            "Do not touch wet wires with bare hands.",
            "Use an insulated tester before repair.",
            "Call a trained electrician if the issue continues.",
        ],
        "puncture": [
            "Park safely on a flat surface.",
            "Use the jack and lift the vehicle slowly.",
            "Remove the damaged tire and fit the spare.",
            "Tighten nuts in a cross pattern before driving.",
        ],
        "cement bag": [
            "Stand close to the load before lifting.",
            "Bend your knees and keep the back straight.",
            "Lift with your legs and keep the bag near your body.",
            "Ask for help if the load feels too heavy.",
        ],
    },
    "hi": {
        "leaking tap": [
            "सबसे पहले पानी की वाल्व बंद करें।",
            "टैप का हैंडल खोलें और पुराना वॉशर निकालें।",
            "नया वॉशर या कार्ट्रिज लगाएं।",
            "टैप बंद करके पानी चालू करें और लीक चेक करें।",
        ],
        "shock": [
            "पहले मेन पावर बंद करें।",
            "गीले हाथों से तार को न छुएं।",
            "इंसुलेटेड टेस्टर से लाइन चेक करें।",
            "समस्या रहे तो इलेक्ट्रिशियन को बुलाएं।",
        ],
        "puncture": [
            "गाड़ी को सुरक्षित और समतल जगह पर रोकें।",
            "जैक लगाकर वाहन को धीरे उठाएं।",
            "खराब टायर निकालें और स्पेयर टायर लगाएं।",
            "नट्स को बराबर कसें और फिर आगे बढ़ें।",
        ],
        "cement bag": [
            "बैग के पास खड़े हों और संतुलन बनाएं।",
            "घुटने मोड़ें, पीठ सीधी रखें।",
            "बैग को शरीर के पास रखकर उठाएं।",
            "बहुत भारी लगे तो मदद लें।",
        ],
    },
}

DEFAULT_AI_RESPONSE = {
    "en": [
        "Start with safety and switch off power, water, or engine if needed.",
        "Check the tool or part carefully before touching it.",
        "Follow small steps one by one and test slowly.",
        "If the problem feels risky, call a trained worker nearby.",
    ],
    "hi": [
        "पहले सुरक्षा रखें और जरूरत हो तो पावर, पानी या इंजन बंद करें।",
        "उपकरण या पार्ट को ध्यान से देखें।",
        "छोटे-छोटे स्टेप में काम करें और धीरे टेस्ट करें।",
        "जोखिम लगे तो पास के प्रशिक्षित व्यक्ति से मदद लें।",
    ],
}

LANGUAGE_LABELS = {"en": "English", "hi": "Hindi"}

BADGES = [
    {"title": "Safety Starter", "detail": "Complete 3 lessons to unlock"},
    {"title": "Fast Fixer", "detail": "Finish 5 repair lessons"},
    {"title": "Site Ready", "detail": "Weekly streak badge"},
]

JOBS = [
    {"title": "Helper Electrician", "location": "Bengaluru", "pay": "₹16k - ₹20k"},
    {"title": "Delivery Driver", "location": "Hyderabad", "pay": "₹18k - ₹24k"},
    {"title": "Plumbing Technician", "location": "Pune", "pay": "₹20k - ₹28k"},
]


def get_or_create_demo_user():
    user = User.query.first()
    if user:
        return user

    user = User(name="Ravi Kumar", language_preference="en")
    db.session.add(user)
    db.session.flush()
    return user


def seed_demo_data():
    if Category.query.count() > 0:
        return

    get_or_create_demo_user()

    lessons_by_title = {}
    for category_payload in DEMO_DATA:
        category = Category(name=category_payload["name"], icon=category_payload["icon"])
        db.session.add(category)
        db.session.flush()

        for lesson_payload in category_payload["lessons"]:
            lesson = Lesson(
                title=lesson_payload["title"],
                duration=lesson_payload["duration"],
                steps=lesson_payload["steps"],
                category_id=category.id,
            )
            db.session.add(lesson)
            db.session.flush()
            lessons_by_title[lesson.title] = lesson

    user = User.query.first()
    if user and lessons_by_title:
        starter_lessons = [
            "Switch Off Main Before Repair",
            "Fix a Leaking Tap Fast",
        ]
        for title in starter_lessons:
            lesson = lessons_by_title.get(title)
            if lesson:
                db.session.add(Progress(user_id=user.id, lesson_id=lesson.id, completed=True))

    db.session.commit()


def lesson_count():
    return Lesson.query.count()


def completed_progress_for(user_id):
    return Progress.query.filter_by(user_id=user_id, completed=True).all()


def progress_summary(user):
    completed_records = completed_progress_for(user.id)
    completed_ids = {record.lesson_id for record in completed_records}
    total_lessons = lesson_count()
    completed_count = len(completed_ids)
    percent = int((completed_count / total_lessons) * 100) if total_lessons else 0
    streak = max(3, completed_count + 2)

    return {
        "completed_count": completed_count,
        "completed_ids": completed_ids,
        "total_lessons": total_lessons,
        "percent": percent,
        "streak": streak,
    }


def normalize_query(text):
    return re.sub(r"[^a-zA-Z0-9\u0900-\u097F\s]", "", (text or "").strip().lower())


def chatbot_steps(question, language):
    normalized = normalize_query(question)
    responses = MOCK_AI_RESPONSES.get(language, MOCK_AI_RESPONSES["en"])

    for key, steps in responses.items():
        if key in normalized:
            return key, steps

    for key, steps in responses.items():
        key_tokens = set(key.split())
        query_tokens = set(normalized.split())
        if key_tokens and key_tokens.intersection(query_tokens):
            return key, steps

    return "general", DEFAULT_AI_RESPONSE.get(language, DEFAULT_AI_RESPONSE["en"])


@app.context_processor
def inject_globals():
    return {"current_year": datetime.utcnow().year}


@app.route("/")
def home():
    user = get_or_create_demo_user()
    db.session.commit()

    categories = Category.query.order_by(Category.id).all()
    featured_lessons = Lesson.query.order_by(Lesson.id).limit(6).all()
    summary = progress_summary(user)

    return render_template(
        "home.html",
        user=user,
        categories=categories,
        featured_lessons=featured_lessons,
        summary=summary,
        category_themes=CATEGORY_THEMES,
        badges=BADGES,
        jobs=JOBS,
        language_labels=LANGUAGE_LABELS,
    )


@app.route("/category/<int:category_id>")
def category_detail(category_id):
    user = get_or_create_demo_user()
    category = Category.query.get_or_404(category_id)
    summary = progress_summary(user)

    return render_template(
        "category.html",
        category=category,
        user=user,
        summary=summary,
        completed_ids=summary["completed_ids"],
        category_themes=CATEGORY_THEMES,
    )


@app.route("/lesson/<int:lesson_id>")
def lesson_detail(lesson_id):
    user = get_or_create_demo_user()
    lesson = Lesson.query.get_or_404(lesson_id)
    summary = progress_summary(user)
    theme = CATEGORY_THEMES.get(lesson.category.name, {})

    return render_template(
        "lesson.html",
        lesson=lesson,
        user=user,
        is_completed=lesson.id in summary["completed_ids"],
        summary=summary,
        theme=theme,
    )


@app.route("/complete/<int:lesson_id>", methods=["POST"])
def complete_lesson(lesson_id):
    user = get_or_create_demo_user()
    lesson = Lesson.query.get_or_404(lesson_id)

    progress = Progress.query.filter_by(user_id=user.id, lesson_id=lesson.id).first()
    if not progress:
        progress = Progress(user_id=user.id, lesson_id=lesson.id, completed=True)
        db.session.add(progress)
    else:
        progress.completed = True

    db.session.commit()
    summary = progress_summary(user)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
        return jsonify(
            {
                "success": True,
                "lesson_id": lesson.id,
                "summary": {
                    "completed_count": summary["completed_count"],
                    "total_lessons": summary["total_lessons"],
                    "percent": summary["percent"],
                    "streak": summary["streak"],
                },
            }
        )

    return redirect(url_for("lesson_detail", lesson_id=lesson.id))


@app.route("/chatbot", methods=["POST"])
def chatbot():
    payload = request.get_json(silent=True) or request.form
    question = (payload.get("question") or "").strip()
    language = payload.get("language", "en")

    key, steps = chatbot_steps(question, language)
    headline = {
        "en": "Try these simple steps",
        "hi": "इन आसान स्टेप्स को आजमाएं",
    }.get(language, "Try these simple steps")

    return jsonify(
        {
            "success": True,
            "headline": headline,
            "language": language,
            "matched_topic": key,
            "steps": steps,
        }
    )


with app.app_context():
    db.create_all()
    seed_demo_data()


if __name__ == "__main__":
    app.run(debug=True)
