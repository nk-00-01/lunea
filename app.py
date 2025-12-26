from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, marshal_with,reqparse, Resource, fields
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite3'
db = SQLAlchemy(app)
api = Api(app)


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
    name = db.Column(db.String(50), unique=True)
    # college = db.Column(db.Integer, db.ForeignKey('institution.id'))

    branches = db.relationship('Branch', backref='department', lazy=True)

class Branch(db.Model):
    __tablename__ = 'branch'
    id = db.Column(db.Integer,primary_key=True)
    dept = db.Column(db.Integer,db.ForeignKey('department.id'), nullable=False )
    name = db.Column(db.String(30), nullable=False, unique=True)

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
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    done = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Assignment(db.Model):
    __tablename__ = 'assignment'
    id= db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))
    title = db.Column(db.String(100))
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum('Pending', 'Submitted'), default='Pending', nullable=False)

@app.before_request
def check_access():
    key = request.headers.get('api-key')
    if key not in access_keys:
        return jsonify({"error": "Unauthorized"}), 401



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
    # LOGIN
    def post(self): 
        data = request.get_json()
        id = data['id']
        pwd = data['password']       
        user = Student.query.filter_by(id=id).first()
        if not user:
            return {"Alert": "User does not exist, Please do register"},404
        if not check_password_hash(user.password,pwd):
            return {"Alert": "Incorrect Password, please try again"}, 401
        return {"Success": "Login successful"}, 200

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
        data = request.get_json()
        id = data['id']
        user = Student.query.filter_by(id=id).first()
        if  user:
            return jsonify({"Alert": "User Exists already, please enter new user id"}),404
        name = data['name']
        age = data['age'] if data['age'] else None
        mobile = data['phone'] if data['phone'] else None
        pwd = data['password']
        branch =data['branch']
        year = data['year']

        hashed_pwd = generate_password_hash(pwd)
        user = Student(id=id,name=name, age=age,mobile=mobile, password=hashed_pwd,branch_id=branch,year=year)
        db.session.add(user)
        db.session.commit()
        return jsonify({"success": "registration successful"})
    def delete(self, id):
        student = Student.query.filter_by(id=id).first()

        if not student:
            return {"error": "Student not found"}, 404

        db.session.delete(student)
        db.session.commit()

        return {"message": "Student deleted completely"}, 200

        
class dashboard(Resource):
    def get(self,id):
        student = Student.query.filter_by(id=id).first()
        subjects = [{
            "id":s.id,
            "name":s.name
        } for s in student.subjects]
        exams = [{
            "subject":e.subject.name,
            "date":e.date.isoformat()
        } for e in student.exams]
        return {"name": student.name, "year":student.year, "branch":student.branch.name, "department":student.branch.department.name ,"subjects": subjects, "exams": exams}, 200

class subject(Resource):
    def get(self,id):
        student = Student.query.filter_by(id=id).first()
        subjects = [{
            "id":s.id,
            "name":s.name
        } for s in student.subjects]
        return subjects,200

    def post(self):
        data = request.get_json()
        id =data['id']
        student = Student.query.filter_by(id=id).first()
        sub_name = data['sub_name']
        sub = Subject(student_id=student.id, name=sub_name)
        db.session.add(sub)
        db.session.commit()
        return {"success":"subject added"}, 200
    def put(self):
        data = request.get_json()
        sub_id = data.get('subject_id')
        new_name = data.get('name')
        if not sub_id or not new_name:
            return {"error": "subject_id and name are required"}, 400

        sub = Subject.query.get(sub_id)
        if not sub:
            return {"error": "Subject not found"}, 404

        sub.name = new_name
        db.session.commit()
        return {"success": "Subject updated"}, 200

    def delete(self):
        data = request.get_json()
        sub_id = data.get('subject_id')
        if not sub_id:
            return {"error": "subject_id is required"}, 400

        sub = Subject.query.get(sub_id)
        if not sub:
            return {"error": "Subject not found"}, 404

        db.session.delete(sub)
        db.session.commit()
        return {"success": "Subject deleted"}, 200

class exams(Resource):
    def post(self):
        data = request.get_json()
        id =data['id']
        student = Student.query.filter_by(id=id).first()

        # 1️⃣ Required fields check
        required = ['id', 'sub_id', 'exam_date', 'difficulty', 'time']
        for field in required:
            if field not in data:
                return {"error": f"{field} is required"}, 400
            
        sub_id = data['sub_id']
        date = data['exam_date']
        exam_date = datetime.strptime(date, "%Y-%m-%d").date()
        difficulty = data['difficulty']
        time = data['time']
        study_time = datetime.strptime(time, "%H:%M").time()
        exam = Exam(student_id=student.id, subject_id=sub_id,date=exam_date,difficulty=difficulty,study_time=study_time)
        db.session.add(exam)
        db.session.commit()
        return {"success":"Exam added"}, 200
    def get(self, id):
        student = Student.query.filter_by(id=id).first()
        if not student:
            return {"error": "Student not found"}, 404

        sub_id = request.args.get('sub_id')
        upcoming = request.args.get('upcoming')

        query = Exam.query.filter_by(student_id=id)

        if sub_id:
            query = query.filter_by(subject_id=sub_id)

        if upcoming == "true":
            query = query.filter(Exam.date >= datetime.today().date())

        exams = query.order_by(Exam.date.asc()).all()

        result = [{
            "exam_id": e.id,
            "subject": e.subject.name,
            "subject_id": e.subject_id,
            "date": e.date.isoformat(),
            "difficulty": e.difficulty,
            "study_time": e.study_time.strftime("%H:%M") if e.study_time else None
        } for e in exams]

        return result, 200
    def delete(self, exam_id):
        exam = Exam.query.get(exam_id)

        if not exam:
            return {"error": "Exam not found"}, 404

        db.session.delete(exam)
        db.session.commit()

        return {
            "success": "Exam deleted successfully",
            "exam_id": exam_id
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
    def get(self,id):
        grades = Grades.query.filter_by(student_id=id).all()
        scores = {g.sem : {"sgpa":g.sgpa,"cgpa":g.cgpa} for g in grades}
        return scores, 200
    
    def delete(self,id,sem):
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
        
        todo = Todo(task=data["task"], student_id=student.id)
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
    

    





api.add_resource(login, '/api/login/')
api.add_resource(register, '/api/register/', '/api/register/<string:id>')
api.add_resource(dashboard, '/api/dashboard/<string:id>')
api.add_resource(subject, '/api/subject/<string:id>', '/api/subject/')
api.add_resource(exams, '/api/exams/','/api/exams/<string:id>','/api/exams/<int:id>')
api.add_resource(score, '/api/score/', '/api/score/<string:student_id>/', '/api/student/<string:student_id>/<int:sem>')
api.add_resource(TodoResource, '/api/todo/<string:student_id>')
api.add_resource(TodoDetail, '/api/todo/detail/<int:todo_id>')



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

    
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        add_depts_branches()
    app.run(debug=True)