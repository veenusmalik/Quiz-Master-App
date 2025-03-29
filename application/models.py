from datetime import datetime
from .database import db 
import random 

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(), unique=True, nullable=False)
    email = db.Column(db.String(), unique=True, nullable=False)
    password = db.Column(db.String(), nullable=False) 
    # Ensure passwords are hashed!
    confirmpassword = db.Column(db.String(), nullable=False)
    fullname = db.Column(db.String(), nullable=False)
    qualification = db.Column(db.String(), nullable=False)
    exams = db.Column(db.String(200), nullable = False)
    dateofbirth = db.Column(db.String(20), nullable = False)
    image = db.Column(db.String(255), nullable = False)
    role = db.Column(db.String(), default='user')  # user or admin
    points = db.Column(db.Integer, default=0)
    scores = db.relationship("Score", backref="user")  # One user can have multiple quiz scores
    user_answers = db.relationship("UserAnswers", backref="user")  # ✅ One user can have multiple answers

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=False)
    chapters = db.relationship("Chapter", backref="subject")  # One subject can have multiple chapters

class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subject.id"), nullable=False)
    name = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=False)
    quizzes = db.relationship("Quiz", backref="chapter")  # One chapter can have multiple quizzes

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    date_of_quiz = db.Column(db.String(), nullable=False)
    time_duration = db.Column(db.Integer, nullable=False)  # In minutes
    remarks = db.Column(db.String(250), nullable=True)
    status = db.Column(db.String(), default="active")  # active/completed
    questions = db.relationship("Question", backref="quiz")  # One quiz can have multiple questions
    scores = db.relationship("Score", backref="quiz")  # One quiz can have multiple user scores
    user_answers = db.relationship("UserAnswers", backref="quiz")  # ✅ Link answers to the quiz

class QuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id"), nullable=False)
    attempt_time = db.Column(db.DateTime, default=datetime.utcnow)  # Stores attempt timestamp
    total_questions = db.Column(db.Integer, nullable=False)  # Total questions in the quiz
    correct_answers = db.Column(db.Integer, nullable=False, default=0)  # Correctly answered questions
    score = db.Column(db.Integer, nullable=False, default=0)  # User's total score
    percentage_score = db.Column(db.Float, nullable=False, default=0.0)  # Percentage score
    user = db.relationship("User", backref="quiz_attempts")  # Each user can attempt multiple quizzes
    quiz = db.relationship("Quiz", backref="quiz_attempts")  # Each quiz can have multiple attempts

    def calculate_percentage(self):
        """Calculate the percentage score."""
        if self.total_questions > 0:
            self.percentage_score = (self.correct_answers / self.total_questions) * 100
        else:
            self.percentage_score = 0.0

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id"), nullable=False)
    question_statement = db.Column(db.String(1000), nullable=False)
    option1 = db.Column(db.String(255), nullable=False)
    option2 = db.Column(db.String(255), nullable=False)
    option3 = db.Column(db.String(255), nullable=False)
    option4 = db.Column(db.String(255), nullable=False)
    correct_option_1 = db.Column(db.Integer, nullable=False)  # 1, 2, 3, or 4
    correct_option_2 = db.Column(db.Integer, nullable=True)  # 1,2,3,4
    user_answers = db.relationship("UserAnswers", backref="question")  # ✅ Link answers to the question

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    time_stamp_of_attempt = db.Column(db.String(), nullable=False)
    total_scored = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)  # Track total questions attempted
    percentage_score = db.Column(db.Float, nullable=False)  # Easy percentage calculation

class UserAnswers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    selected_answer = db.Column(db.String(50))  # Stores "Option X" or "Not Answered"

class BonusQuiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=True)
    date_of_quiz = db.Column(db.String(), nullable=False)
    time_duration = db.Column(db.Integer, nullable=False)  # Time limit in minutes
    reward_points = db.Column(db.Integer, default=0)  # Extra points for winning
    status = db.Column(db.String(), default="active")  # active/completed
    questions = db.relationship("BonusQuestion", backref="bonus_quiz")  # Link questions to bonus quiz
    scores = db.relationship("BonusScore", backref="bonus_quiz")  # Track user scores in bonus quizzes

class BonusQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bonus_quiz_id = db.Column(db.Integer, db.ForeignKey("bonus_quiz.id"), nullable=False)
    question_statement = db.Column(db.String(1000), nullable=False)
    option1 = db.Column(db.String(255), nullable=False)
    option2 = db.Column(db.String(255), nullable=False)
    option3 = db.Column(db.String(255), nullable=False)
    option4 = db.Column(db.String(255), nullable=False)
    correct_option = db.Column(db.Integer, nullable=False)  # 1, 2, 3, or 4

class BonusScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bonus_quiz_id = db.Column(db.Integer, db.ForeignKey("bonus_quiz.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    total_scored = db.Column(db.Integer, nullable=False)
    reward_earned = db.Column(db.Integer, default=0)  # Track extra reward points