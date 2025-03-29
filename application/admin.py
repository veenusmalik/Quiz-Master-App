from flask import Flask, redirect, render_template, request, url_for
from flask import current_app as app
from .models import *
from .user import *
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sqlalchemy import func
from .controllers import *




# ADMIN DASHBOARD
@app.route("/admin")
def admin_dashboard():
    this_user = User.query.filter_by(role="admin").first()
    all_users = User.query.all()  
    all_subjects = Subject.query.all()  
    all_quizzes = Quiz.query.all()
    new_bonus_quiz = BonusQuiz.query.all()
    all_attempts = Score.query.order_by(Score.time_stamp_of_attempt.desc()).all()  

    # Preload chapters for subjects
    for subject in all_subjects:
        subject.chapters = Chapter.query.filter_by(subject_id=subject.id).all()
        for chapter in subject.chapters:
            chapter.quizzes = Quiz.query.filter_by(chapter_id=chapter.id).all()

    user_scores = db.session.query(Score.user_id, db.func.sum(Score.total_scored)).group_by(Score.user_id).all()
    score_dict = {user_id: total_score for user_id, total_score in user_scores}

    for user in all_users:
        user.total_quizzes = Score.query.filter_by(user_id=user.id).count()
        total_score = score_dict.get(user.id, 0)
        total_quizzes = max(user.total_quizzes, 1) 
        user.average_score = round((total_score / total_quizzes), 2)

    return render_template(
        "admin/admin_dashboard.html",
        this_user=this_user,
        all_users=all_users,
        all_subjects=all_subjects,
        all_quizzes=all_quizzes,  
        new_bonus_quiz=new_bonus_quiz,
        all_attempts=all_attempts 
    )







# ADMIN PROFILE
@app.route('/admin_profile')
def admin_profile():
    user = User.query.filter_by(role="admin").first()
    if not user:
        return redirect(url_for('register'))
    
    return render_template('admin/profile.html', user=user)







# ADD DELETE VIEW SUBJECT

# VIEW SUBJECT
@app.route('/view_subjects')
def admin_view_subjects():
    all_subjects = Subject.query.all()
    return render_template('admin/admin_view_subject.html', all_subjects=all_subjects)

# Create Subject
@app.route("/create_subject", methods=["GET", "POST"])
def create_subject():
    if request.method == "POST":
        subject_name = request.form["subjectname"]
        description = request.form["description"]
        if not subject_name or not description:
            return redirect("/admin")
        new_subject = Subject(name=subject_name, description=description)
        db.session.add(new_subject)
        db.session.commit()
        return redirect("/admin")  

    return render_template("admin/create_subject.html")

# View Subject
@app.route("/subject/<int:subject_id>")
def view_subject(subject_id):
    subject = Subject.query.get(subject_id)
    if not subject:
        return redirect("/admin")
    subject.chapters = Chapter.query.filter_by(subject_id=subject.id).all()
    return render_template("admin/view_subject.html", subject=subject)

# Edit Subject
@app.route("/edit_subject/<int:subject_id>", methods=["GET", "POST"])
def edit_subject(subject_id):
    subject = Subject.query.get(subject_id)
    if request.method == "POST":
        subject.name = request.form["subjectname"]
        subject.description = request.form["description"]
        db.session.commit()
        return redirect("/admin")

    return render_template("admin/edit_subject.html", subject=subject)

# Delete Subject
@app.route("/delete_subject/<int:subject_id>", methods=["GET"])
def delete_subject(subject_id):
    subject = Subject.query.get(subject_id)
    if not subject:
        return redirect("/admin")  

    Chapter.query.filter_by(subject_id=subject_id).delete()
    db.session.delete(subject)
    db.session.commit()
    return redirect("/admin")







# ADD EDIT DELETE VIEW CHAPTER FOR SUBJECT
# Create Chapter
@app.route("/add_chapter/<int:subject_id>", methods=["GET", "POST"])
def add_chapter(subject_id):
    subject = Subject.query.get(subject_id)
    if request.method == "POST":
        chapter_name = request.form.get("chaptername")
        chapter_description = request.form.get("description")
        if not chapter_name or not chapter_description:
            return redirect("/admin")
        new_chapter = Chapter(name=chapter_name, description=chapter_description, subject_id=subject.id)
        db.session.add(new_chapter)
        db.session.commit()
        return redirect("/admin")  # Redirect back to admin page

    return render_template("admin/create_chapter.html", subject=subject)

# View Chapter
@app.route("/view_chapter/<int:subject_id>/<int:chapter_id>")
def view_chapter(subject_id, chapter_id):
    chapter = Chapter.query.get(chapter_id)
    subject = Subject.query.get(subject_id)

    if not chapter or not subject:
        return render_template("not_exists.html", message="Chapter, or Subject not found"), 404

    return render_template("admin/view_chapter.html", chapter=chapter, subject=subject)

# View Chapter
@app.route("/chapter/<int:chapter_id>")
def chapter(chapter_id):
    chapter = Chapter.query.get(chapter_id)  # Fetch chapter from DB
    quizzes = Quiz.query.all()
    return render_template("admin/chapter.html", chapter=chapter, quizzes=quizzes)

# Edit Chapter
@app.route("/edit_chapter/<int:chapter_id>", methods=["GET", "POST"])
def edit_chapter(chapter_id):
    chapter = Chapter.query.get(chapter_id)
    if request.method == "POST":
        chapter.name = request.form["name"]
        chapter.description = request.form["description"]
        db.session.commit()
        return redirect("/view_subjects")  # Redirect after editing
    return render_template("admin/edit_chapter.html", chapter=chapter)

# Delete Chapter  
@app.route("/delete_chapter/<int:chapter_id>", methods=["GET"])
def delete_chapter(chapter_id):
    chapter = Chapter.query.get(chapter_id)
    if not chapter:
        return redirect("/view_subjects")
    Quiz.query.filter_by(chapter_id=chapter_id).delete()
    db.session.delete(chapter)
    db.session.commit()
    
    return redirect("/view_subjects")







# ADD EDIT DELETE VIEW QUIZ FOR SUBJECT
# add quiz
@app.route('/add_quiz/<int:chapter_id>', methods=['GET', 'POST'])
def add_quiz(chapter_id):
    if request.method == 'POST':
        new_quiz = Quiz(
            chapter_id=chapter_id,
            date_of_quiz=request.form['date_of_quiz'],
            time_duration=int(request.form['time_duration']),
            remarks=request.form.get('remarks', ''),
            status=request.form.get('status', 'active')
        )
        db.session.add(new_quiz)
        db.session.commit()
        return redirect(f'/manage_quizzes/{chapter_id}')
    return render_template('admin/add_quiz.html', chapter_id=chapter_id)

# edit quiz
@app.route('/edit_quiz/<int:quiz_id>', methods=['GET', 'POST'])
def edit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if request.method == 'POST':
        quiz.date_of_quiz = request.form['date_of_quiz']
        quiz.time_duration = int(request.form['time_duration'])
        quiz.remarks = request.form.get('remarks', '')
        quiz.status = request.form.get('status', 'active')
        db.session.commit()
        return redirect(f'/manage_quizzes/{quiz.chapter_id}')
    return render_template('admin/edit_quiz.html', quiz=quiz)

# delete quiz
@app.route('/delete_quiz/<int:quiz_id>')
def delete_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    chapter_id = quiz.chapter_id
    QuizAttempt.query.filter_by(quiz_id=quiz_id).delete()
    db.session.commit()
    Question.query.filter_by(quiz_id=quiz_id).delete()
    db.session.commit()
    db.session.delete(quiz)
    db.session.commit()

    return redirect(f'/manage_quizzes/{chapter_id}')

# manage quizzes
@app.route('/manage_quizzes/<int:chapter_id>')
def manage_quizzes(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    return render_template('admin/manage_quizzes.html', chapter=chapter)







# ADD EDIT DELETE VIEW QUESTIONS FOR QUIZ
# add question
@app.route('/add_question/<int:quiz_id>', methods=['GET', 'POST'])
def add_question(quiz_id):
    if request.method == 'POST':
        new_question = Question(
            quiz_id=quiz_id,
            question_statement=request.form['question_statement'],
            option1=request.form['option1'],
            option2=request.form['option2'],
            option3=request.form['option3'],
            option4=request.form['option4'],
            correct_option_1=int(request.form['correct_option_1']),
            correct_option_2=int(request.form.get('correct_option_2', 0))  
        )
        db.session.add(new_question)
        db.session.commit()
        return redirect(f'/manage_questions/{quiz_id}')
    return render_template('admin/add_question.html', quiz_id=quiz_id)

# edit question
@app.route('/edit_question/<int:question_id>', methods=['GET', 'POST'])
def edit_question(question_id):
    question = Question.query.get_or_404(question_id)
    if request.method == 'POST':
        question.question_statement = request.form['question_statement']
        question.option1 = request.form['option1']
        question.option2 = request.form['option2']
        question.option3 = request.form['option3']
        question.option4 = request.form['option4']
        question.correct_option_1 = int(request.form['correct_option_1'])
        
        # Handle optional second correct answer
        correct_option_2 = request.form.get('correct_option_2')
        question.correct_option_2 = int(correct_option_2) if correct_option_2 else None

        db.session.commit()
        return redirect(f'/manage_questions/{question.quiz_id}')
    return render_template("admin/edit_question.html", question=question)

# delete question
@app.route('/delete_question/<int:question_id>')
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    quiz_id = question.quiz_id
    db.session.delete(question)
    db.session.commit()
    return redirect(f'/manage_questions/{quiz_id}')

# manage questions
@app.route('/manage_questions/<int:quiz_id>')
def manage_questions(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    return render_template('admin/manage_questions.html', quiz=quiz)







# ADMIN CAN VIEW USER AND HIS PERFORMANCE AND ALL USERS 
# admin can view user
@app.route('/admin_view_user')
def admin_view_user():
    all_users = User.query.filter(User.role != "admin").all()
    
    user_performance = []
    
    for user in all_users:
        scores = Score.query.filter_by(user_id=user.id).all()
        total_quizzes = QuizAttempt.query.filter_by(user_id=user.id).count()
        total_score = db.session.query(db.func.sum(QuizAttempt.score)).filter_by(user_id=user.id).scalar() or 0
        max_possible_score = total_quizzes * 100  # Assuming each quiz is out of 100
        average_score = (total_score / max_possible_score * 100) if max_possible_score > 0 else 0        
        user_performance.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "total_quizzes": total_quizzes,
            "average_score": round(average_score, 2)
        })
    
    return render_template('admin/admin_view_user.html', all_users=user_performance, all_subjects=Subject.query.all())

# admin can view user details
@app.route('/view_user_details/<int:user_id>')
def view_user_details(user_id):
    user = User.query.get_or_404(user_id)
    
    # Fetch all quiz attempts for this user
    quiz_attempts = QuizAttempt.query.filter_by(user_id=user.id).all()

    return render_template('admin/view_user_details.html', user=user, quiz_attempts=quiz_attempts)

# view all users
@app.route('/view_all_users')
def view_all_users():
    all_users = User.query.filter(User.role != "admin").all()  # Get all non-admin users
    return render_template('admin/view_all_users.html', all_users=all_users)

# admin_view_user : search button
@app.route('/search_users', methods=['GET'])
def search_users():
    query = request.args.get('query', '').strip()
    key = request.args.get('key', '')

    # Subquery to calculate total quizzes and average score
    stats_subquery = db.session.query(
        QuizAttempt.user_id,
        db.func.count(QuizAttempt.id).label('total_quizzes'),
        db.func.coalesce(db.func.avg(QuizAttempt.score), 0).label('average_score')
    ).group_by(QuizAttempt.user_id).subquery()

    base_query = db.session.query(
        User.id, 
        User.username, 
        User.email, 
        stats_subquery.c.total_quizzes, 
        stats_subquery.c.average_score
    ).outerjoin(stats_subquery, User.id == stats_subquery.c.user_id)

    if key == "user":  
        base_query = base_query.filter(User.username.ilike(f"%{query}%"))
    elif key == "quizzes" and query.isdigit():
        base_query = base_query.filter(stats_subquery.c.total_quizzes == int(query))

    users = base_query.all()
    users_list = [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "total_quizzes": u.total_quizzes or 0,  
            "average_score": round(u.average_score or 0, 2) 
        }
        for u in users
    ]

    return render_template('admin/admin_view_user.html', all_users=users_list)

# view_user_details: search button
@app.route('/user/<int:user_id>')
def search_view_user_details(user_id):
    user = User.query.get_or_404(user_id)
    quiz_attempts = QuizAttempt.query.filter_by(user_id=user_id).all()
    search_query = request.args.get('query', '').strip()
    search_key = request.args.get('key', '')

    if search_query:
        if search_key == "marks":
            quiz_attempts = [attempt for attempt in quiz_attempts if search_query in str(attempt.correct_answers)]
        elif search_key == "date":
            quiz_attempts = [attempt for attempt in quiz_attempts if search_query in str(attempt.attempt_time)]

    return render_template("admin/view_user_details.html", user=user, quiz_attempts=quiz_attempts)







# BONUS QUIZ
# create bonus quiz
@app.route('/create_bonus_quiz', methods=['GET', 'POST'])
def create_bonus_quiz():
    if request.method == 'POST':
        quiz_name = request.form['quiz_name']
        description = request.form['quiz_description']
        date_of_quiz = request.form['quiz_date']  
        time_duration = request.form['quiz_duration']
        reward_points = request.form['quiz_reward']
        status = request.form['quiz_status']

        new_bonus_quiz = BonusQuiz(
            name=quiz_name,
            description=description,
            date_of_quiz=date_of_quiz,
            time_duration=time_duration,
            reward_points=reward_points,
            status=status
        )
        db.session.add(new_bonus_quiz)
        db.session.commit()

        return redirect(url_for('admin_dashboard'))

    return render_template('bonus/create_bonus_quiz.html')

# admin can view bonus quiz
@app.route("/admin_view_bonus", methods=["GET"])
def admin_view_bonus():
    new_bonus_quiz = BonusQuiz.query.all()  
    return render_template("admin/admin_view_bonus.html", new_bonus_quiz=new_bonus_quiz)

# edit bonus quiz
@app.route('/edit_bonus_quiz/<int:quiz_id>', methods=['GET', 'POST'])
def edit_bonus_quiz(quiz_id):
    bonus_quiz = BonusQuiz.query.get_or_404(quiz_id)

    if request.method == 'POST':
        bonus_quiz.name = request.form['quiz_name']
        bonus_quiz.description = request.form['quiz_description']
        bonus_quiz.date_of_quiz = request.form['quiz_date']
        bonus_quiz.time_duration = int(request.form['quiz_duration'])
        bonus_quiz.reward_points = int(request.form['quiz_reward'])
        bonus_quiz.status = request.form['quiz_status']

        db.session.commit()
        return redirect(url_for('admin_dashboard'))

    return render_template('bonus/edit_bonus_quiz.html', bonus_quiz=bonus_quiz)

@app.route('/delete_bonus_quiz/<int:quiz_id>', methods=['GET','POST'])
def delete_bonus_quiz(quiz_id):
    try:
        # Attempt to remove any bonus score records associated with the quiz
        deleted_scores = db.session.query(BonusScore).filter(BonusScore.bonus_quiz_id == quiz_id).delete()
        db.session.commit()  # Commit after deleting scores

        # Attempt to delete the bonus quiz
        bonus_quiz = BonusQuiz.query.get(quiz_id)
        if bonus_quiz:
            db.session.query(BonusQuestion).filter(BonusQuestion.bonus_quiz_id == quiz_id).delete()
            db.session.delete(bonus_quiz)
            db.session.commit()  # Commit after deleting the quiz
        else:
            return f"Bonus quiz with ID {quiz_id} not found.", 404
        
        # Redirect to the admin panel or the quizzes list page after successful deletion
        return redirect('/admin')

    except Exception as e:
        db.session.rollback()  # Rollback the session in case of an error
        print(f"Error deleting bonus quiz: {e}")  # Log the error for debugging
        return f"An error occurred while deleting the quiz: {e}", 500 

# add bonus question
@app.route('/add_bonus_question/<int:bonus_quiz_id>', methods=['GET', 'POST'])
def add_bonus_question(bonus_quiz_id):
    bonus_quiz = BonusQuiz.query.get_or_404(bonus_quiz_id)

    if request.method == 'POST':
        question_text = request.form['question']
        option1 = request.form['option1']
        option2 = request.form['option2']
        option3 = request.form['option3']
        option4 = request.form['option4']
        correct_option = request.form['correct_option']

        new_question = BonusQuestion(
            bonus_quiz_id=bonus_quiz_id,
            question_statement=question_text,
            option1=option1,
            option2=option2,
            option3=option3,
            option4=option4,
            correct_option=correct_option
        )
        db.session.add(new_question)
        db.session.commit()
        return redirect(url_for('manage_bonus_questions', bonus_quiz_id=bonus_quiz_id))

    return render_template('bonus/add_bonus_question.html', bonus_quiz=bonus_quiz)

# edit bonus question
@app.route('/edit_bonus_question/<int:bonus_question_id>', methods=['GET', 'POST'])
def edit_bonus_question(bonus_question_id):
    bonus_question = BonusQuestion.query.get_or_404(bonus_question_id)
    question_statement = request.form.get("question_statement")


    if request.method == 'POST':
        question_text = request.form.get('question_text')
        option_1 = request.form.get('option_1')
        option_2 = request.form.get('option_2')
        option_3 = request.form.get('option_3')
        option_4 = request.form.get('option_4')
        correct_option = request.form.get('correct_option')

        bonus_question.question_statement = question_text
        bonus_question.option1 = option_1
        bonus_question.option2 = option_2
        bonus_question.option3 = option_3
        bonus_question.option4 = option_4
        bonus_question.correct_option = correct_option
        bonus_question.question_statement = question_statement

        
        db.session.commit()
        return redirect(url_for('manage_bonus_questions', bonus_quiz_id=bonus_question.bonus_quiz_id))

    return render_template('bonus/edit_bonus_question.html', bonus_question=bonus_question)

# delete bonus question
@app.route('/delete_bonus_question/<int:bonus_question_id>', methods=['GET','POST'])
def delete_bonus_question(bonus_question_id):
    bonus_question = BonusQuestion.query.get_or_404(bonus_question_id)
    bonus_quiz_id = bonus_question.bonus_quiz_id  # Store the quiz ID for redirection

    try:
        db.session.delete(bonus_question)  # Directly delete the question
        db.session.commit()  # Commit the deletion
    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        print(f"Error while deleting bonus question: {e}")

    return redirect(url_for('manage_bonus_questions', bonus_quiz_id=bonus_quiz_id))



# manage bonus questions
@app.route('/manage_bonus_questions/<int:bonus_quiz_id>')
def manage_bonus_questions(bonus_quiz_id):
    bonus_quiz_id = BonusQuiz.query.get_or_404(bonus_quiz_id)
    bonus_questions = BonusQuestion.query.filter_by(bonus_quiz_id=bonus_quiz_id.id).all()
    return render_template('bonus/manage_bonus_questions.html', bonus_quiz_id=bonus_quiz_id,bonus_questions=bonus_questions)







# ADMIN SUMMARY
@app.route("/admin_summary", methods=["GET"])
def admin_summary():
    total_users = User.query.filter_by(role='user').count()
    total_admins = User.query.filter_by(role='admin').count()
    total_subjects = Subject.query.count()
    total_quizzes = Quiz.query.count()
    total_bonus_quizzes = BonusQuiz.query.count()

    subjects_data = []
    subject_names = []
    quiz_counts = []
    
    subjects = Subject.query.all()
    for subject in subjects:
        chapters_count = len(subject.chapters)
        quizzes_count = sum(len(chapter.quizzes) for chapter in subject.chapters)
        subjects_data.append({'name': subject.name, 'chapters': chapters_count, 'quizzes': quizzes_count})
        subject_names.append(subject.name)
        quiz_counts.append(quizzes_count)

    # Calculate average score for each quiz
    quiz_scores = {}
    quizzes = Quiz.query.all()
    
    for quiz in quizzes:
        attempts = quiz.quiz_attempts
        if attempts:
            avg_score = sum(attempt.score for attempt in attempts) / len(attempts)
            quiz_scores[quiz.id] = round(avg_score, 2)
        else:
            quiz_scores[quiz.id] = 0  # If no attempts, set avg score to 0

    # Identify user with the least attempted quizzes and calculate their average score
    users = User.query.filter_by(role="user").all()
    user_attempt_counts = {}
    user_avg_scores = {}

    for user in users:
        attempts = user.quiz_attempts
        user_attempt_counts[user.username] = len(attempts)
        
        if attempts:
            avg_score = sum(attempt.score for attempt in attempts) / len(attempts)
            user_avg_scores[user.username] = round(avg_score, 2)
        else:
            user_avg_scores[user.username] = 0  # If no attempts, set avg score to 0

    least_attempts_user = min(user_attempt_counts, key=user_attempt_counts.get, default="No User")

    summary = {
        'total_users': total_users,
        'total_admins': total_admins,
        'total_subjects': total_subjects,
        'total_quizzes': total_quizzes,
        'total_bonus_quizzes': total_bonus_quizzes,
        'subjects_data': subjects_data,
        'quiz_scores': quiz_scores,
        'least_attempts_user': least_attempts_user,
        'user_avg_scores': user_avg_scores
    }

    # Generate Pie Chart for User Distribution
    labels = ['Users', 'Admins']
    sizes = [total_users, total_admins]
    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', colors=['yellow', 'pink'])
    plt.title("User Distribution")
    plt.savefig("static/user_distribution.png")
    plt.close()

    # Generate Bar Chart for Quizzes per Subject
    plt.figure(figsize=(10, 6))
    plt.bar(subject_names, quiz_counts, color='lightblue')
    plt.xlabel("Subjects")
    plt.ylabel("Number of Quizzes")
    plt.title("Quizzes per Subject")
    plt.xticks(rotation=0)
    plt.savefig("static/quiz_distribution.png")
    plt.close()

    # Generate Bar Chart for Quiz Attempt Distribution
    quiz_names = []
    attempt_counts = []

    for quiz in quizzes:
        attempt_count = len(quiz.quiz_attempts)
        quiz_names.append(f"Quiz {quiz.id}")  
        attempt_counts.append(attempt_count)

    if quiz_names:
        plt.figure(figsize=(10, 6))
        plt.bar(quiz_names, attempt_counts, color='orange')
        plt.xlabel("Quizzes")
        plt.ylabel("Users Attempted")
        plt.title("Quiz Attempt Distribution")
        plt.xticks(rotation=0)
        plt.savefig("static/quiz_attempts.png")
        plt.close()

    # Generate Bar Chart for User Quiz Attempts
    if users:
        user_names = list(user_attempt_counts.keys())
        attempts = list(user_attempt_counts.values())

        plt.figure(figsize=(10, 6))
        plt.bar(user_names, attempts, color='cyan')
        plt.xlabel("Users")
        plt.ylabel("Quizzes Attempted")
        plt.title("User Quiz Attempts")
        plt.xticks(rotation=0, fontsize=10)
        plt.savefig("static/user_attempts.png")
        plt.close()

    return render_template("admin/admin_summary.html", summary=summary)
