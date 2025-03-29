from flask import Flask, redirect, render_template, request, url_for
from flask import current_app as app
from .models import *
from .admin import *
from .user import *
from datetime import datetime


# HOME PAGE
@app.route("/", methods=["GET","POST"])
def home():
    return render_template("home.html")


# LOGIN PAGE
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form.get("role").strip().lower()  
        username = request.form.get("username").strip()
        password = request.form.get("password").strip()

        this_user = User.query.filter_by(username=username).first() 
        
        if this_user:
            if this_user.password == password:  
                if this_user.role == role:  
                    if role == "user":
                        return redirect(url_for("user_dashboard", username=username))
                    elif role == "admin":
                        return redirect(url_for("admin_dashboard", username=username))
                else:
                    return render_template("role_mismatch.html")  
            else:
                return render_template("invalid_password.html")
        else:
            return render_template("not_exists.html")
    return render_template("login.html")


# LOGOUT PAGE
@app.route('/logout')
def logout():
    return redirect('/login')



# REGISTRATION PAGE
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirmpassword = request.form.get("confirmpassword")
        fullname = request.form.get("fullname")
        qualification = request.form.get("qualification")
        dateofbirth = request.form.get("dateofbirth")

        selected_exams = request.form.getlist("exams")
        other_exam = request.form.get("other_exam")
        if other_exam:
            selected_exams.append(other_exam)
        exams_str = ", ".join(selected_exams)

        user_name = User.query.filter_by(username=username).first()
        user_email = User.query.filter_by(email=email).first()

        if password != confirmpassword:
            return render_template("register.html", invalid="PASSWORD CONFIRMATION NOT SATISFIED. RE-ENTER PASSWORD.")
        
        if user_name or user_email:
            return render_template("already_exists.html")

        # Default profile image
        image_filename = "default.jpg"  
            
        if "image" in request.files:
            image_file = request.files["image"]
                
            if image_file and allowed_file(image_file.filename):
                image_filename = f"{username}.jpg"  # Save with username as filename
                image_path = f"static/images/user/{image_filename}"
                image_file.save(image_path)  

        new_user = User(
            username=username,
            email=email,
            password=password,
            confirmpassword=confirmpassword,
            fullname=fullname,
            qualification=qualification,
            dateofbirth=dateofbirth,
            exams=exams_str,
            image=image_filename,  # Store filename in DB, not full path
            role="user"
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect("/login")

    return render_template("register.html")


# TERMS PAGE
@app.route('/terms')
def terms():
    return render_template('terms.html')


# PRIVACY PAGE
@app.route("/privacy")
def privacy():
    return render_template("privacy_policy.html")


# LEADERBOARD
@app.route('/leaderboard/<username>')
def leaderboard(username):
    users = User.query.filter(User.role != "admin").order_by(User.points.desc()).all()

    leagues = {
        "🏆 Legend": [],
        "🏅 Elite": [],
        "🥈 Pro": [],
        "🥉 Intermediate": [],
        "🎓 Beginner": []
    }

    def get_league(points):
        if points > 1000:
            return "🏆 Legend"
        elif points > 500:
            return "🏅 Elite"
        elif points >= 300:
            return "🥈 Pro"
        elif points >= 100:
            return "🥉 Intermediate"
        else:
            return "🎓 Beginner"

    for user in users:
        league = get_league(user.points)
        leagues[league].append(user)
    this_user = User.query.filter_by(username=username).first()  
    if not this_user:
        return "User not found", 400  
    username = this_user.username  
    this_user = User.query.filter_by(username=username).first()
    return render_template("leaderboard/leaderboard.html", leagues=leagues,this_user=this_user)