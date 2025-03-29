from flask import current_app as app, request, jsonify
from .models import *
from .admin import *
from .user import *
from .database import db





@app.get("/api/home")
def api_home():
    return {"message": "Welcome to the Quiz Master App!"}






# LOGIN API
@app.post("/api/login")
def api_login():
    username = request.json.get("username")
    password = request.json.get("password")
    try:
        this_user = User.query.filter_by(username=username).first()
        if this_user:
            if this_user.password == password:
                if this_user.role == "admin":
                    return jsonify(message= "Admin loggged in successfully !!")
                else:
                    return jsonify(message= "User logged in successfully !!")
            else:
                return jsonify(error= "Invalid password"), 400
        else:
            return jsonify(error= "User not found"), 404
    except:
        return jsonify(error= "Internal Server Error"), 500






# REGISETR API
@app.post("/api/register")
def api_register():
    fullname = request.json.get("fullname")
    username = request.json.get("username")
    email = request.json.get("email")
    password = request.json.get("password")
    confirmpassword = request.json.get("confirmpassword")
    qualification = request.json.get("qualification")
    exams = request.json.get("exams")
    dateofbirth = request.json.get("dateofbirth")
    image = request.json.get("image")

    try:
        user_username = User.query.filter_by(username=username).first()
        user_email = User.query.filter_by(email=email).first()

        if user_username or user_email:
            return jsonify(error="User already exists"), 400

        if password != confirmpassword:
            return jsonify(error="Passwords do not match"), 400

        new_user = User(
            fullname=fullname,
            username=username,
            email=email,
            password=password, 
            confirmpassword=confirmpassword,
            qualification=qualification,
            exams=exams,
            dateofbirth=dateofbirth,
            image=image
        )
        db.session.add(new_user)
        db.session.commit()

        return jsonify(message="User created successfully!"), 201

    except:
        return jsonify(error="Internal Server Error"), 500









# <!---------------------- ADMIN ------------------------->
# ADMIN DASHBOARD API
@app.get("/api/admin_dashboard")
def api_admin_dashboard():
    try:
        all_users = User.query.all()
        all_subjects = Subject.query.all()
        all_quizzes = Quiz.query.all()
        new_bonus_quiz = BonusQuiz.query.all()
        all_attempts = Score.query.order_by(Score.time_stamp_of_attempt.desc()).all()

        user_scores = db.session.query(Score.user_id, db.func.sum(Score.total_scored)).group_by(Score.user_id).all()
        score_dict = {user_id: total_score for user_id, total_score in user_scores}

        users_data = []
        for user in all_users:
            total_quizzes = Score.query.filter_by(user_id=user.id).count()
            total_score = score_dict.get(user.id, 0)
            average_score = round((total_score / max(total_quizzes, 1)), 2)
            users_data.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "total_quizzes": total_quizzes,
                "average_score": average_score
            })

        return jsonify({
            "users": users_data,
            "subjects": [{"id": s.id, "name": s.name, "description": s.description} for s in all_subjects],
            "quizzes": [{"id": q.id, "chapter_id": q.chapter_id} for q in all_quizzes],
            "bonus_quizzes": [{"id": bq.id} for bq in new_bonus_quiz],
            "attempts": [{"id": a.id, "user_id": a.user_id, "score": a.total_scored} for a in all_attempts]
        })
    except:
        return jsonify(error="Internal Server Error"), 500





# <!---------------------- SUBJECTS ------------------------->
# VIEW SUBJECT API
@app.get("/api/subject/<int:subject_id>")
def api_view_subject(subject_id):
    subject = Subject.query.get(subject_id)
    if not subject:
        return jsonify(error="Subject not found"), 404

    chapters = Chapter.query.filter_by(subject_id=subject.id).all()
    subject_data = {
        "id": subject.id,
        "name": subject.name,
        "description": subject.description,
        "chapters": [{"id": c.id, "name": c.name, "description": c.description} for c in chapters]
    }

    return jsonify(subject_data), 200

# CREATE SUBJECT API
@app.post("/api/create_subject")
def api_create_subject():
    data = request.json
    subject_name = data.get("subjectname")
    description = data.get("description")

    if not subject_name or not description:
        return jsonify(error="Subject name and description are required"), 400

    try:
        new_subject = Subject(name=subject_name, description=description)
        db.session.add(new_subject)
        db.session.commit()
        return jsonify(message="Subject created successfully!"), 201
    except:
        return jsonify(error="Internal Server Error"), 500

# EDIT SUBJECT API
@app.put("/api/edit_subject/<int:subject_id>")
def api_edit_subject(subject_id):
    subject = Subject.query.get(subject_id)
    if not subject:
        return jsonify(error="Subject not found"), 404

    data = request.json
    subject.name = data.get("name", subject.name)
    subject.description = data.get("description", subject.description)

    db.session.commit()
    return jsonify(message="Subject updated successfully"), 200

# DELETE SUBJECT API
@app.delete("/api/delete_subject/<int:subject_id>")
def api_delete_subject(subject_id):
    try:
        subject = Subject.query.get(subject_id)
        if not subject:
            return jsonify(error="Subject not found"), 404

        Chapter.query.filter_by(subject_id=subject_id).delete()
        db.session.delete(subject)
        db.session.commit()
        return jsonify(message="Subject deleted successfully!"), 200
    except Exception as e:
        print("Error:", str(e))
        return jsonify(error="Internal Server Error"), 500
    


