import re
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, marshal_with,reqparse, Resource, fields
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from google import genai
from google.genai import types
import os
import json

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

client = genai.Client(
    api_key=GEMINI_API_KEY
)
MODEL_NAME = "models/gemini-2.5-flash"

# models_pager = client.models.list()

# # Iterate to print each model
# for model in models_pager:
#     print(model.name, "-", model.display_name)


# prompt = "Tell me a joke about programmers."

# response = client.models.generate_content(
#     model="models/gemini-2.5-flash",
#     contents=prompt
# )

# print(response.text)


app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # Render PostgreSQL
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL.replace(
        "postgres://", "postgresql://"
    )
else:
    # Local SQLite (for development)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.sqlite3"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
api = Api(app)

# resp = client.models.generate_content(
#     model="gemini-2.5-flash",
#     contents="Say hello"
# )
# print(resp.text)



CORS(
    app,
    supports_credentials=True,
    resources={r"/api/*": {"origins": "*"}},
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Authorization"]
)

app.config['JWT_SECRET_KEY'] = os.environ.get("JWT_SECRET_KEY")

jwt = JWTManager(app)

# @app.route("/test-gemini")
# def test_gemini():
#     response = client.models.generate_content(
#         model="gemini-2.5-flash",
#         contents="Say hello in one sentence"
#     )
#     return {"text": response.text}
# res = client.models.generate_content(
#     model="gemini-2.5",
#     contents="Say hello in one sentence"
# )

# print(res.text)

access_keys = {
    "techsprint-2k25",
    "test-3524"
}

class Student(db.Model):
    __tablename__ = 'student'
    id = db.Column(db.String(20),primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    password = db.Column(db.String(300), nullable=False)
    age = db.Column(db.Integer)
    mobile = db.Column(db.String(15))
    year = db.Column(db.Integer, nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=False)
    # credits= db.Column(db.Integer, default=0)

    todos = db.relationship('Todo', backref='student', lazy=True)
    grades = db.relationship('Grades',backref='student',lazy=True, cascade='all, delete-orphan')
    subjects = db.relationship('Subject',backref='student', lazy=True, cascade='all, delete-orphan')
    exams = db.relationship('Exam', backref='student',lazy=True, cascade='all, delete-orphan')


# class institution(db.Model):
#     __tablename__ = 'institution'
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(80), nullable=False)


class Department(db.Model):
    __tablename__ = 'department'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True)
    # college = db.Column(db.Integer, db.ForeignKey('institution.id'))

    branches = db.relationship('Branch', backref='department', lazy=True)

class Branch(db.Model):
    __tablename__ = 'branch'
    id = db.Column(db.Integer,primary_key=True)
    dept = db.Column(db.Integer,db.ForeignKey('department.id'), nullable=False )
    name = db.Column(db.String(100), nullable=False, unique=True)

    students = db.relationship('Student', backref='branch', lazy=True)


class Subject(db.Model):
    __tablename__ = 'subject'
    id = db.Column(db.Integer,primary_key=True)
    student_id = db.Column(db.String(20), db.ForeignKey('student.id'))
    name = db.Column(db.String(30), nullable=False)

    exam = db.relationship('Exam', backref='subject',lazy=True)

class Exam(db.Model):
    __tablename__ = 'exam'
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))
    student_id = db.Column(db.String(20), db.ForeignKey('student.id'))
    date = db.Column(db.Date, nullable=False)
    study_time = db.Column(db.Time)
    difficulty = db.Column(db.String(30))

class Grades(db.Model):
    __tablename__ = 'grades'
    id = db.Column(db.Integer, primary_key=True)
    sem = db.Column(db.Integer, nullable=False )
    student_id = db.Column(db.String(20), db.ForeignKey('student.id'))
    sgpa = db.Column(db.Float, nullable=False, default=0)
    cgpa = db.Column(db.Float, nullable=False, default=0)

    sem_credits = db.Column(db.Integer, nullable=False)
    total_credits = db.Column(db.Integer, nullable=False)

class Todo(db.Model):
    __tablename__ = 'todo'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), db.ForeignKey('student.id'), nullable=False)
    task = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    done = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Assignment(db.Model):
    __tablename__ = 'assignment'
    id= db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))
    title = db.Column(db.String(100))
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='Pending', nullable=False)



class StudyPlan(db.Model):
    __tablename__ = "study_plan"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), db.ForeignKey("student.id"))
    date = db.Column(db.Date, nullable=False)
    subject = db.Column(db.String(50))
    topic = db.Column(db.String(100))
    hours = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# @app.before_request
# def check_access():
#     key = request.headers.get('api-key')
#     if key not in access_keys:
#         return jsonify({"error": "Unauthorized"}), 401



# data: {'marks': 'total_credits'}
def calculate_grade(data,prev_cgpa=None,prev_credits=None):
    GRADE_POINTS = {
    "A+": 10,
    "A": 9,
    "B": 8,
    "C": 7,
    "D": 6,
    "E": 5,
    "F": 0
}
    total_points = 0
    total_credits = 0
    for grade,credits in data.items():
        if grade.upper() not in GRADE_POINTS:
            raise ValueError(f"Invalid grade: {grade}")
        
        total_points += GRADE_POINTS[grade] * credits
        total_credits += credits
    if total_credits == 0:
        raise ValueError("Total credits cannot be zero")
    sgpa = round(total_points / total_credits, 2)
    if prev_cgpa is None or prev_credits == 0:
            cgpa = sgpa
            cumulative_credits = total_credits
    else:
        cumulative_credits = prev_credits + total_credits
        cgpa = round(
            ((prev_cgpa * prev_credits) + (sgpa * total_credits)) / cumulative_credits,
            2
        )

    return sgpa,cgpa,total_credits,cumulative_credits

class login(Resource):
    def post(self):
        data = request.get_json()
        student = Student.query.filter_by(id=data["id"]).first()
        if not student:
            return {"error": "Invalid credentials"}, 401

        if not check_password_hash(student.password, data["password"]):
            return {"error": "Invalid credentials"}, 401

        # Create JWT token
        token = create_access_token(identity=student.id)

        return {
            "message": "Login successful",
            "student_id": student.id,
            "token": token  # <-- return token
        }, 200


class register(Resource):
    def get(self):
        branch = Branch.query.all()
        return jsonify([
            {
                "id": b.id,
                "name": b.name
            }
            for b in branch
        ])
    
    def post(self):
        data = request.get_json(force=True)
    
        # ---- REQUIRED FIELDS ----
        id = data.get('id')
        name = data.get('name')
        password = data.get('password')
        branch = data.get('branch')
        if not branch:
            return {"error": "Branch is required"}, 400

        year = data.get('year')
    
        # ---- OPTIONAL FIELDS ----
        age = data.get('age')
        mobile = data.get('phone')
    
        # ---- VALIDATION ----
        if not all([id, name, password, branch, year]):
            return {"error": "Missing required fields"}, 400
    
        user = Student.query.filter_by(id=id).first()
        if user:
            return {"Alert": "User Exists already, please enter new user id"}, 409
    
        # ---- CREATE USER ----
        student = Student(
            id=id,
            name=name,
            age=age,
            mobile=mobile,
            year=year,
            branch_id=branch
        )
    
        student.password = generate_password_hash(password)   # assuming you have hashing
    
        db.session.add(student)
        db.session.commit()
    
        return {"message": "Registration successful"}, 201

    def delete(self, id):
        student = Student.query.filter_by(id=id).first()

        if not student:
            return {"error": "Student not found"}, 404

        db.session.delete(student)
        db.session.commit()

        return {"message": "Student deleted completely"}, 200

        
class dashboard(Resource):
    @jwt_required()
    def get(self):
        id = get_jwt_identity()
        student = Student.query.filter_by(id=id).first()
        subjects = [{
            "id":s.id,
            "name":s.name
        } for s in student.subjects]
        exams = []

        for e in student.exams:
            if not e.subject:
                print(f"⚠ Orphan exam {e.id} skipped")
                continue

            exams.append({
                "subject": e.subject.name,
                "date": e.date.isoformat()
            })

        return {"student_id": id,"name": student.name, "year":student.year, "branch":student.branch.name, "department":student.branch.department.name ,"subjects": subjects, "exams": exams}, 200



class Subjects(Resource):

    @jwt_required()
    def get(self):
        student_id = get_jwt_identity()
        student = Student.query.filter_by(id=student_id).first()

        if not student:
            return {"error": "Student not found"}, 404

        subjects = [{"id": s.id, "name": s.name} for s in student.subjects]
        return subjects, 200

    @jwt_required()
    def post(self):
        student_id = get_jwt_identity()
        student = Student.query.filter_by(id=student_id).first()

        if not student:
            return {"error": "Student not found"}, 404

        data = request.get_json()
        subjects = data.get("subjects")

        if not subjects or not isinstance(subjects, list):
            return {"error": "subjects must be a list"}, 400

        for name in subjects:
            sub = Subject(student_id=student.id, name=name)
            db.session.add(sub)

        db.session.commit()
        return {"success": "Subjects added"}, 201



class SubjectDelete(Resource):

    @jwt_required()
    def delete(self, id):
        student_id = get_jwt_identity()

        sub = Subject.query.filter_by(id=id, student_id=student_id).first()
        if not sub:
            return {"error": "Subject not found"}, 404

        db.session.delete(sub)
        db.session.commit()
        return {"success": "Subject deleted"}, 200


    
class exams(Resource):
    @jwt_required()
    def get(self):
        student_id = get_jwt_identity()

        exams = Exam.query.filter_by(student_id=student_id).order_by(Exam.date).all()

        result = []

        for e in exams:
            if not e.subject:
                continue

            result.append({
                "id": e.id,
                "subject": e.subject.name,
                "date": e.date.isoformat(),
                "difficulty": e.difficulty,
                "study_time": e.study_time.strftime("%H:%M") if e.study_time else None
            })

        return result, 200


    @jwt_required()
    def post(self):
        student_id = get_jwt_identity()
        data = request.get_json()

        required = ['sub_id', 'exam_date', 'difficulty', 'time']
        for field in required:
            if field not in data:
                return {"error": f"{field} is required"}, 400

        exam = Exam(
            student_id=student_id,
            subject_id=data['sub_id'],
            date=datetime.strptime(data['exam_date'], "%Y-%m-%d").date(),
            difficulty=data['difficulty'],
            study_time=datetime.strptime(data['time'], "%H:%M").time()
        )

        db.session.add(exam)
        db.session.commit()

        return {"success": "Exam added"}, 201

        # student = Student.query.filter_by(id=id).first()
        # if not student:
        #     return {"error": "Student not found"}, 404

        # sub_id = request.args.get('sub_id')
        # upcoming = request.args.get('upcoming')

        # query = Exam.query.filter_by(student_id=id)

        # if sub_id:
        #     query = query.filter_by(subject_id=sub_id)

        # if upcoming == "true":
        #     query = query.filter(Exam.date >= datetime.today().date())

        # exams = query.order_by(Exam.date.asc()).all()

        # result = [{
        #     "exam_id": e.id,
        #     "subject": e.subject.name,
        #     "subject_id": e.subject_id,
        #     "date": e.date.isoformat(),
        #     "difficulty": e.difficulty,
        #     "study_time": e.study_time.strftime("%H:%M") if e.study_time else None
        # } for e in exams]

        # return result, 200
    def delete(self, id):
        exam = Exam.query.get(id)


        if not exam:
            return {"error": "Exam not found"}, 404

        db.session.delete(exam)
        db.session.commit()

        return {
            "success": "Exam deleted successfully",
            "exam_id": exam.id
        }, 200

class score(Resource):
    def post(self):
        data = request.get_json()
        id = data['id']
        # student = Student.query.filter_by(id=id).first()
        grades = Grades.query.filter_by(student_id=id).order_by(Grades.sem.desc()).first()
        total_credits = grades.total_credits
        if grades:
            next_sem = grades.sem+1
            prev_cgpa=grades.cgpa
        else:
            next_sem = 1
            prev_cgpa = None
        subjects = data['subjects']

        # Convert to required helper format
        # {'marks': 'credits'}
        scores = {
            s['marks']: s['credits']
            for s in subjects
        }

        sgpa, cgpa, total_credits_sem, cumulative_credits = calculate_grade(scores,prev_cgpa,total_credits)
        # student.credits = cumulative_credits
        gr = Grades(sem=next_sem, student_id=id, sgpa=sgpa,cgpa=cgpa,sem_credits=total_credits_sem, total_credits=cumulative_credits)
        db.session.add(gr)
        db.session.commit()
        return {"success":'entered data successfully'},200
    def get(self,student_id):
        grades = Grades.query.filter_by(student_id=id).all()
        scores = {g.sem : {"sgpa":g.sgpa,"cgpa":g.cgpa} for g in grades}
        return scores, 200
    
    def delete(self,student_id,sem):
        latest = Grades.query.filter_by(student_id=id).order_by(Grades.sem.desc).first()
        if not latest:
            return {"error": "No grades found"}, 404
        if latest.sem != sem:
            return {"error": "Only latest semester info can be deleted"}, 400
        db.session.delete(latest)
        db.session.commit()
        return {"message":"deleted successfully"}, 200
    

class TodoResource(Resource):
    # GET all todos for a student
    def get(self, student_id):
        student = Student.query.filter_by(id=student_id).first()
        if not student:
            return {"error": "Student not found"}, 404
        
        todos = [{
            "id": t.id,
            "task": t.task
        } for t in student.todos]
        return {"todos": todos}, 200

    # POST a new todo for a student
    def post(self, student_id):
        data = request.get_json()
        if "task" not in data:
            return {"error": "task is required"}, 400
        
        student = Student.query.filter_by(id=student_id).first()
        if not student:
            return {"error": "Student not found"}, 404
            
        # ADDED PART!!!!!!!!!!!!!!!!!!!
        todo = Todo(
    task=data["task"], 
    description=data.get("description"), # If you add it
    student_id=student.id
    # Ensure you add 'date' to the Todo model or handle it here
)
        db.session.add(todo)
        db.session.commit()
        return {"success": "Todo added", "id": todo.id}, 201

class TodoDetail(Resource):
    # GET a specific todo by id
    def get(self, todo_id):
        todo = Todo.query.get(todo_id)
        if not todo:
            return {"error": "Todo not found"}, 404
        return {"id": todo.id, "task": todo.task, "student_id": todo.student_id}, 200

    # PUT / PATCH to update a todo
    def put(self, todo_id):
        data = request.get_json()
        todo = Todo.query.get(todo_id)
        if not todo:
            return {"error": "Todo not found"}, 404
        if "task" in data:
            todo.task = data["task"]
        db.session.commit()
        return {"success": "Todo updated"}, 200

    # DELETE a todo
    def delete(self, todo_id):
        todo = Todo.query.get(todo_id)
        if not todo:
            return {"error": "Todo not found"}, 404
        db.session.delete(todo)
        db.session.commit()
        return {"success": "Todo deleted"}, 200

class Profile(Resource):
    @jwt_required()
    def get(self):
        student_id = get_jwt_identity()
        student = Student.query.filter_by(id=student_id).first()

        if not student:
            return {"error": "Student not found"}, 404

        branch = student.branch
        department = branch.department if branch else None

        return {
            "id": student.id,
            "name": student.name,
            "mobile": student.mobile,
            "year": student.year,

            # branch info
            "branch_id": branch.id if branch else None,
            "branch": branch.name if branch else None,

            # derived department (READ ONLY)
            "department": department.name if department else None
        }, 200

    @jwt_required()
    def put(self):
        student_id = get_jwt_identity()
        student = Student.query.filter_by(id=student_id).first()

        if not student:
            return {"error": "Student not found"}, 404

        data = request.get_json() or {}

        # ✅ Partial updates (safe)
        if "name" in data:
            student.name = data["name"]

        if "mobile" in data:
            student.mobile = data["mobile"]

        if "year" in data:
            student.year = data["year"]

        if "branch_id" in data:
            student.branch_id = data["branch_id"]

        db.session.commit()
        return {"success": "Profile updated"}, 200

class BranchList(Resource):
    def get(self):
        branches = Branch.query.all()
        return [
            {
                "id": b.id,
                "name": b.name,
                "department": b.department.name
            }
            for b in branches
        ], 200






    

def build_gemini_prompt(daily_hours, exams):
    return f"""
You are an expert academic planner.

RULES:
- Prioritize exams with fewer days left
- Hard exams get more hours
- Never exceed daily_hours
- Include revision before exams
- Output ONLY valid JSON
- No explanations
- No markdown

Daily available hours: {daily_hours}

Exams:
{json.dumps(exams, indent=2)}

JSON FORMAT ONLY:
{{
  "plan": [
    {{
      "date": "YYYY-MM-DD",
      "tasks": [
        {{
          "subject": "string",
          "topic": "string",
          "hours": number
        }}
      ]
    }}
  ]
}}
"""


def extract_json(text):
    if not text or not text.strip():
        raise ValueError("Empty AI response")

    # Remove markdown if present
    text = re.sub(r"```json|```", "", text).strip()

    # Extract first JSON block
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("No JSON found in AI response")

    return json.loads(match.group())

def fallback_plan(daily_hours):
    return {
        "plan": [
            {
                "date": date.today().isoformat(),
                "tasks": [
                    {
                        "subject": "TEST",
                        "topic": "Backend connected",
                        "hours": daily_hours
                    }
                ]
            }
        ]
    }


@app.before_request
def log_every_request():
    print("➡️ Incoming:", request.method, request.path)



class AIPlanner(Resource):
    @jwt_required()
    def get(self):
        student_id = get_jwt_identity()

        plans = StudyPlan.query.filter_by(student_id=student_id)\
            .order_by(StudyPlan.date.asc())\
            .all()

        if not plans:
            return {"plan": []}, 200

        result = {}
        for p in plans:
            day = p.date.isoformat()
            result.setdefault(day, []).append({
                "subject": p.subject,
                "topic": p.topic,
                "hours": p.hours
            })

        formatted = [
            {"date": d, "tasks": t}
            for d, t in result.items()
        ]

        return {"plan": formatted}, 200
    
    @jwt_required()
    def post(self):
        data = request.get_json()
        if not data or "daily_hours" not in data:
            return {"error": "daily_hours required"}, 400

        try:
            daily_hours = int(data["daily_hours"])
        except ValueError:
            return {"error": "daily_hours must be a number"}, 400

        student_id = get_jwt_identity()

        exams_db = Exam.query.filter_by(student_id=student_id).all()
        if not exams_db:
            return fallback_plan(daily_hours), 200

        exams = []
        today = date.today()

        for e in exams_db:
            if not e.subject:
                continue

            exams.append({
                "subject": e.subject.name,
                "difficulty": e.difficulty,
                "exam_date": e.date.isoformat(),
                "days_left": (e.date - today).days
            })


        prompt = build_gemini_prompt(daily_hours, exams)

        # ---------- AI CALL ----------
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )

            ai_text = response.text
            ai_data = extract_json(ai_text)

        except Exception as e:
            print("❌ AI ERROR:", e)
            ai_data = fallback_plan(daily_hours)

        # ---------- NORMALIZE ----------
        if "plan" not in ai_data:
            ai_data = fallback_plan(daily_hours)

        final_plan = ai_data["plan"]

        # ---------- SAVE TO DB ----------
        StudyPlan.query.filter_by(student_id=student_id).delete()

        for day in final_plan:
            for task in day["tasks"]:
                db.session.add(
                    StudyPlan(
                        student_id=student_id,
                        date=date.fromisoformat(day["date"]),
                        subject=task["subject"],
                        topic=task["topic"],
                        hours=task["hours"]
                    )
                )

        db.session.commit()

        # ---------- RETURN ----------
        return {"plan": final_plan}, 200
    
 # Cleanup orphan exams on startup   









        
# AI CHATBOT
# AI CHATBOT - FIXED VERSION

DANGER_KEYWORDS = [
    "kill myself", "end my life", "suicide",
    "give up on life", "can't go on",
    "worthless", "no reason to live"
]

def is_severe_distress(text: str) -> bool:
    text = text.lower()
    return any(word in text for word in DANGER_KEYWORDS)

def build_prompt(student, todos, exams, assignments, grades, user_message):
    upcoming_exams = [
        f"- {e.subject.name} on {e.date}"
        for e in exams if e.date >= date.today()
    ]
    pending_todos = [f"- {t.task}" for t in todos]
    assignments_due = [
        f"- {a.title} due on {a.due_date}"
        for a in assignments
    ]
    cgpa = grades[0].cgpa if grades else "Not available"
    
    return f"""
You are an academic mentor helping a college student regain focus and confidence.

Rules:
- Do NOT act as a therapist or doctor.
- Focus on study pressure, planning, motivation, and small actions.
- Give a complete, coherent response in 4-6 sentences.
- Always finish your thoughts completely.

Student Info:
Name: {student.name}, Year: {student.year}, Branch: {student.branch.name}, CGPA: {cgpa}

Upcoming Exams: {', '.join(upcoming_exams) if upcoming_exams else "None"}
Pending Tasks: {', '.join(pending_todos) if pending_todos else "None"}
Assignments: {', '.join(assignments_due) if assignments_due else "None"}

Student says: "{user_message}"

Respond like a calm academic coach with complete sentences.
"""

def get_gemini_response(prompt: str) -> str:
    try:
        response = client.models.generate_content(
    model=MODEL_NAME,
    contents=prompt,
    config={
        "temperature": 0.2,
        "max_output_tokens": 800,
        "response_mime_type": "application/json"
    }
)

        
        # Check if response was blocked
        if not response.candidates:
            print("Response blocked by safety filters")
            return "I'm here to support you. Let's take a deep breath and look at one small thing we can finish today to get your momentum back."
        
        # Get the first candidate
        candidate = response.candidates[0]
        
        # Check if content exists
        if not candidate.content or not candidate.content.parts:
            print("No content in response")
            return "I can see you're looking for support. Sometimes starting is the hardest part—let's pick your easiest task and just do 5 minutes of it."
        
        # Extract text from all parts and join them
        reply_parts = []
        for part in candidate.content.parts:
            if hasattr(part, 'text') and part.text:
                reply_parts.append(part.text)
        
        reply = ' '.join(reply_parts).strip()
        
        # Handle empty response
        if not reply:
            print("Empty response after processing")
            return "I understand you're reaching out. Let's focus on one small achievable goal today that can help build your momentum."
        
        # Log the response length for debugging
        print(f"Gemini response length: {len(reply)} characters")
        
        return reply
        
    except Exception as e:
        print(f"Gemini Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return "I'm here to help you navigate your academic journey. Let's start by identifying one task from your list that we can tackle together right now."

class ChatbotResource(Resource):
    @jwt_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("message", type=str, required=True)
        args = parser.parse_args()
        
        student_id = get_jwt_identity()
        student = Student.query.get(student_id)
        
        if not student:
            return {"error": "Student not found"}, 404
        
        # Distress Check
        if is_severe_distress(args["message"]):
            return {
                "reply": "I'm sorry you're feeling this way. Please reach out to a trusted friend or professional. For now, let's try to focus on just one small task together."
            }, 200
        
        # Fetch Context
        todos = Todo.query.filter_by(student_id=student_id, done=False).all()
        exams = Exam.query.filter(
            Exam.student_id == student_id, 
            Exam.date >= date.today()
        ).all()
        assignments = Assignment.query.join(Subject).filter(
            Subject.student_id == student_id, 
            Assignment.status != "Completed"
        ).all()
        grades = Grades.query.filter_by(
            student_id=student_id
        ).order_by(Grades.sem.desc()).all()
        
        # Build prompt
        prompt = build_prompt(student, todos, exams, assignments, grades, args["message"])
        
        # Get AI response
        reply = get_gemini_response(prompt)
        
        # Log for debugging
        print(f"Sending reply with {len(reply)} characters")
        
        # Return response with explicit encoding
        return {
            "reply": reply
        }, 200, {'Content-Type': 'application/json; charset=utf-8'}

# ROADMAP GENERATOR - FIXED BACKEND


class RoadmapResource(Resource):
    @jwt_required()
    def post(self):
        data = request.get_json()
        topic = data.get("topic")
        level = data.get("level", "beginner")

        if not topic:
            return {"error": "Topic is required"}, 400

        prompt = f"""
You are a learning mentor.

Create a HIGH-LEVEL learning roadmap.

Topic: {topic}
Level: {level}

Rules:
- Max 3 phases only
- Each phase max 5 topics
- Short topic names
- Educational only

Return ONLY valid JSON.
Finish all strings.

JSON format:
{{
  "title": "{topic}",
  "level": "{level}",
  "phases": [
    {{
      "phase": "Phase 1",
      "duration": "X weeks",
      "topics": ["topic1", "topic2"]
    }}
  ]
}}
"""

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config={
                "temperature": 0.1,
                "max_output_tokens": 1024
            }
        )

        raw = extract_text(response)
        raw = fix_common_json_issues(raw)

        try:
            return json.loads(raw), 200
        except Exception as e:
            return {
                "error": "AI response incomplete",
                "raw": raw,
                "details": str(e)
            }, 500


api.add_resource(RoadmapResource, "/api/roadmap")
api.add_resource(ChatbotResource, "/api/chatbot")
api.add_resource(BranchList, "/api/branches")
api.add_resource(login, '/api/login/')
api.add_resource(register, '/api/register/', '/api/register/<string:id>')
api.add_resource(dashboard, '/api/dashboard/')
api.add_resource(Subjects, "/api/subjects/")
api.add_resource(SubjectDelete, "/api/subjects/<int:id>/")
api.add_resource(exams, '/api/exams/','/api/exams/<int:id>')
api.add_resource(score, '/api/score/', '/api/score/<string:student_id>/', '/api/student/<string:student_id>/<int:sem>')
api.add_resource(TodoResource, '/api/todo/<string:student_id>')
api.add_resource(TodoDetail, '/api/todo/detail/<int:todo_id>')
api.add_resource(Profile, "/api/profile/me")
api.add_resource(AIPlanner, "/api/ai/planner/")






def add_depts_branches():
    if Department.query.count() == 0:
        d1= Department(name='COMPUTER SCIENCE AND ENGINEERING')
        d2 = Department(name='ELECTRONICS AND COMMUNICATION ENGINEERING')
        d3 = Department(name="DATA ENGINEERING")
        d4= Department(name='CIVIL ENGINEERING')
        d5= Department(name='CHEMICAL ENGINEERING')
        d6= Department(name='ELECTRICAL AND ELECTRONICS ENGINEERING')
        d7= Department(name='MECHANICAL ENGINEERING')
        d8= Department(name='INFORMATION ENGINEERING AND COMMUNICATION TECHNOLOGY')
        d9= Department(name='MANAGEMENT STUDIES')
        db.session.add_all([d1,d2,d3,d4,d5,d6,d7,d8,d9])
        db.session.commit()

        b1 = Branch(name='cse', dept=d1.id)
        b2 = Branch(name='ece', dept=d2.id)
        b3= Branch(name= 'cic', dept=d3.id)
        b4= Branch(name= 'csm', dept=d3.id)
        b5= Branch(name= 'csd', dept=d3.id)
        b6= Branch(name= 'civil', dept=d4.id)
        b7= Branch(name= 'chem', dept=d5.id)
        b8= Branch(name= 'eee', dept=d6.id)
        b9 = Branch(name='mech',dept=d7.id)
        b10 = Branch(name ='it', dept=d8.id)
        b11 = Branch(name ='csit', dept=d8.id)
        b12 = Branch(name ='mba', dept=d9.id)
        db.session.add_all([b1,b2,b3,b4,b5,b6,b7,b8,b9,b10,b11,b12])
        db.session.commit()

    
with app.app_context():
    db.create_all()
    add_depts_branches()

    orphan_exams = Exam.query.filter(Exam.subject == None).all()
    for e in orphan_exams:
        db.session.delete(e)
    db.session.commit()

if __name__ == "__main__":
    app.run(debug=True)

