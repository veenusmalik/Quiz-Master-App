from flask import Flask, redirect, render_template, request, url_for
from flask import current_app as app
from .models import *
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sqlalchemy import func
from .admin import *

# USER DASHBOARD
@app.route("/user_dashboard/<username>")
def user_dashboard(username):
    user = User.query.filter_by(username=username, role="user").first()
    all_users = User.query.all() 
    all_subjects = Subject.query.all()  
    this_user = User.query.filter_by(username=username).first()
    if not user:
        return "User not found", 400  
    print(f"Total subjects found: {len(all_subjects)}")  
    for subject in all_subjects:
        subject.chapters = Chapter.query.filter_by(subject_id=subject.id).all()
        for chapter in subject.chapters:
            chapter.quizzes = Quiz.query.filter_by(chapter_id=chapter.id).all()
    # Calculate total quizzes attempted
    total_quizzes = Score.query.filter_by(user_id=user.id).count()
    
    # Calculate average score
    total_score = db.session.query(db.func.sum(Score.total_scored)).filter(Score.user_id == user.id).scalar() or 0
    print(f"User: {user.username}, Total Quizzes: {total_quizzes}") 
    average_score = round(total_score / max(total_quizzes, 1), 2) 

    print(f"User: {user.username}, Total Quizzes: {total_quizzes}, Average Score: {average_score}")  
    return render_template(
        "user/user_dashboard.html",
        user=user,
        all_subjects=all_subjects, all_users = all_users, average_score=average_score,
        this_user = this_user
    )






# USER PROFILE PAGE
@app.route('/profile/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return redirect(url_for('register'))
    
    return render_template('user/profile.html', user=user)







# VIEW SUBJECT
@app.route("/user_view_subject/<username>/<int:subject_id>")
def user_view_subject(username, subject_id):
    user = User.query.filter_by(username=username).first()  
    subject = Subject.query.get(subject_id)
    
    if not user or not subject:
        return redirect(url_for("user_dashboard", username=username))  
    
    subject.chapters = Chapter.query.filter_by(subject_id=subject.id).all()
    
    return render_template("user/user_view_subject.html", subject=subject, user=user)

# VIEW CHAPTER
@app.route("/user_view_chapter/<username>/<int:chapter_id>")
def user_view_chapter(username, chapter_id):
    user = User.query.filter_by(username=username).first() 
    chapter = Chapter.query.get(chapter_id)

    if not user or not chapter:
        return redirect(url_for("user_dashboard", username=username))  

    subject = Subject.query.get(chapter.subject_id)  

    return render_template("user/user_view_chapter.html", chapter=chapter, subject=subject, user=user)







# REGULAR QUIZ
# user attempting quiz and user score 
@app.route('/user_quizzes/<username>')
def user_quizzes(username):
    user = User.query.filter_by(username=username).first_or_404()
    quizzes = Quiz.query.all() 
    return render_template('user/user_quizzes.html', this_user=user, quizzes=quizzes, user=user)

# view the quiz
@app.route('/view_quiz/<int:quiz_id>/<string:username>')
def view_quiz(quiz_id,username):
    quiz = Quiz.query.get_or_404(quiz_id)
    user = User.query.filter_by(username=username).first_or_404()
    questions = Question.query.filter_by(quiz_id=quiz.id).all()
    return render_template('admin/view_quiz.html', quiz=quiz, questions=questions,user=user)

# start the quiz 
@app.route('/quiz_list')
def quiz_list():
    quizzes = Quiz.query.filter_by(status="active").all()
    username = "example_user"  
    this_user = User.query.filter_by(username=username).first()

    return render_template("quiz/quiz_list.html", quizzes=quizzes, this_user=this_user)

# attempting the quiz
@app.route('/start_quiz/<int:quiz_id>/<string:username>')
def start_quiz(quiz_id, username):
    print(f"Quiz ID: {quiz_id}, Username: {username}")
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    user = User.query.filter_by(username=username).first()
    if not user:
        print(f"User not found: {username}")  
        return f"User '{username}' not found.", 400

    return render_template("quiz/quiz_attempt.html", quiz=quiz, questions=questions, user=user)

# submitting quiz
@app.route('/submit_quiz/<int:quiz_id>', methods=["POST"])
def submit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
    username = request.form.get("username")
    user = User.query.filter_by(username=username).first()
    
    if not user:
        return "User not found", 400

    total_correct = 0
    total_questions = len(quiz.questions)
    
    for question in quiz.questions:
        selected_answer = request.form.get(f"question_{question.id}", "Not Answered")
        if selected_answer == str(question.correct_option_1) or selected_answer == str(question.correct_option_2):
            total_correct += 1
        user_answer = UserAnswers(
            user_id=user.id,  
            quiz_id=quiz.id,
            question_id=question.id,
            selected_answer=selected_answer
        )
        db.session.add(user_answer)
    
    quiz_score = round((total_correct / total_questions) * 100, 2) if total_questions > 0 else 0
    
    quiz_attempt = QuizAttempt(
        user_id=user.id,
        quiz_id=quiz.id,
        total_questions=total_questions,
        correct_answers=total_correct,
        score=quiz_score,
        percentage_score=quiz_score
    )
    db.session.add(quiz_attempt)

    # Increase User Points by 100
    user.points += 100
    db.session.commit()

    return render_template("quiz/thank_you.html", username=user.username, quiz_id=quiz.id)

# result of regular quiz
@app.route('/quiz_result/<string:username>/<int:quiz_id>')
def quiz_result(username, quiz_id):
    user = User.query.filter_by(username=username).first()
    if not user:
        return redirect(url_for("home"))  

    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return redirect(url_for("home"))

    past_scores = QuizAttempt.query.filter_by(user_id=user.id).order_by(QuizAttempt.id.desc()).all()
    latest_attempt = QuizAttempt.query.filter_by(user_id=user.id, quiz_id=quiz_id).order_by(QuizAttempt.id.desc()).first()

    return render_template(
        "quiz/quiz_result.html",
        username=username,
        quiz=quiz,
        past_scores=past_scores,
        latest_attempt=latest_attempt
    )







# BONUS QUIZ
# bonus quiz page
@app.route('/bonus_quiz_list/<string:username>')
def bonus_quiz_list(username):
    bonus_quizzes = BonusQuiz.query.filter_by(status="active").all()
    user = User.query.filter_by(username=username).first()
    
    if not user:
        return "User not found", 404  

    return render_template("bonus/bonus_quiz_list.html", quizzes=bonus_quizzes, this_user=user)

# start the bonus quiz 
@app.route("/start_bonus_quiz/<int:quiz_id>/<username>")
def start_bonus_quiz(quiz_id, username):
    quiz = BonusQuiz.query.get(quiz_id)
    if not quiz:
        return "Quiz not found", 404

    questions = quiz.questions 
    user = User.query.filter_by(username=username).first()  

    return render_template("bonus/bonus_quiz_attempt.html", quiz=quiz, questions=questions, this_user=user)

# submitting the bonus quiz and rendering the score
@app.route('/submit_bonus_quiz/<int:quiz_id>', methods=["POST"])
def submit_bonus_quiz(quiz_id):
    quiz = BonusQuiz.query.get_or_404(quiz_id)
    
    username = request.form.get("username")
    print(f"Received username: {username}")  
    
    user = User.query.filter_by(username=username).first()
    
    if not user:
        print("User not found in the database")  
        return "User not found", 400  
    
    total_correct = 0
    total_questions = len(quiz.questions)

    for question in quiz.questions:
        selected_answer = request.form.get(f"question_{question.id}", "Not Answered")
        print(f"Question ID: {question.id}, Selected: {selected_answer}, Correct: {question.correct_option}")  

        if str(selected_answer).strip() == str(question.correct_option).strip():  
            total_correct += 1

        user_answer = UserAnswers(
            user_id=user.id,  
            quiz_id=quiz.id,
            question_id=question.id,
            selected_answer=selected_answer
        )
        db.session.add(user_answer)

    print(f"Total Questions: {total_questions}, Total Correct: {total_correct}")  

    if total_questions > 0:
        bonus_quiz_score = int((total_correct / total_questions) * 100)
    else:
        bonus_quiz_score = 0  

    existing_bonus_score = BonusScore.query.filter_by(user_id=user.id, bonus_quiz_id=quiz.id).first()
    if existing_bonus_score:
        existing_bonus_score.total_scored = bonus_quiz_score
        existing_bonus_score.reward_earned = quiz.reward_points
    else:
        bonus_score = BonusScore(
            user_id=user.id,
            bonus_quiz_id=quiz.id,
            total_scored=bonus_quiz_score,
            reward_earned=quiz.reward_points
        )
        db.session.add(bonus_score)

    user.points += quiz.reward_points  
    db.session.commit()

    return redirect(url_for('bonus_quiz_result', user_id=user.id, quiz_id=quiz_id))

# result of bonus quiz
@app.route("/bonus_quiz_result/<int:user_id>/<int:quiz_id>")
def bonus_quiz_result(user_id, quiz_id):
    user = User.query.get(user_id)  # Fetch the user
    score = BonusScore.query.filter_by(user_id=user_id, bonus_quiz_id=quiz_id).first()

    user_answers = (
        db.session.query(UserAnswers, BonusQuestion, BonusQuiz)
        .join(BonusQuestion, UserAnswers.question_id == BonusQuestion.id)
        .join(BonusQuiz, UserAnswers.quiz_id == BonusQuiz.id)
        .filter(UserAnswers.user_id == user_id, UserAnswers.quiz_id == quiz_id)
        .all()
    )

    if not user:
        return "User not found", 400  

    return render_template("bonus/bonus_quiz_result.html", score=score, this_user=user, user_answers=user_answers, quiz_id=quiz_id)







# VIEW PAST SCORES
@app.route('/past_scores/<string:username>')
def past_scores(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return redirect(url_for("home"))

    past_scores = QuizAttempt.query.filter_by(user_id=user.id).order_by(QuizAttempt.id.desc()).all()

    return render_template("user/past_scores.html", past_scores=past_scores, user=user)







# USER SUMMARY
@app.route("/user_summary/<int:user_id>", methods=["GET"])
def user_summary(user_id):
    user = User.query.get_or_404(user_id)
    quiz_attempts = QuizAttempt.query.filter_by(user_id=user_id).all()

    if not quiz_attempts:
        summary = {
            "total_attempted": 0,
            "avg_score": 0,
            "best_quiz": "N/A",
            "worst_quiz": "N/A"
        }
        img_filename = None  # No image if no attempts
    else:
        scores = [attempt.score for attempt in quiz_attempts]
        best_quiz = max(quiz_attempts, key=lambda q: q.score).quiz_id
        worst_quiz = min(quiz_attempts, key=lambda q: q.score).quiz_id

        summary = {
            "total_attempted": len(quiz_attempts),
            "avg_score": round(sum(scores) / len(scores), 2),
            "best_quiz": best_quiz,
            "worst_quiz": worst_quiz
        }

        # Generate performance graph
        img_filename = f"user_quiz_scores_{user_id}.png"
        img_path = f"static/{img_filename}"
        plot_user_performance(quiz_attempts, user.username, img_path)

    return render_template("user/user_summary.html", user=user, summary=summary, img_filename=img_filename,past_scores=quiz_attempts)

def plot_user_performance(quiz_attempts, username, img_path):
    quiz_ids = [attempt.quiz_id for attempt in quiz_attempts]
    scores = [attempt.score for attempt in quiz_attempts]

    plt.figure(figsize=(8, 5))
    plt.bar(quiz_ids, scores, color='green', width=0.4)
    
    plt.xlabel("Quiz ID")
    plt.ylabel("Score")
    plt.title(f"Quiz Scores of {username}")
    plt.xticks(quiz_ids)  
    plt.ylim(0, 100)  

    plt.savefig(img_path)
    plt.close() 