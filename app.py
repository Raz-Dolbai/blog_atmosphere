import os
from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email
from flask_migrate import Migrate
import email_validator
from flask_login import LoginManager, UserMixin, current_user, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
UPLOAD_FOLDER = 'static/img'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'you-will-never-guess'
migrate = Migrate(app, db)
login_manager = LoginManager(app)


class LoginForm(FlaskForm):
    """Authorization admin form"""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class Add_admin(FlaskForm):
    """Form for sending data about the adminn"""
    email = StringField('Username', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')


class Leave_comment(FlaskForm):
    """Form for submitting comment data"""
    name = StringField('Имя', validators=[DataRequired()])
    text = StringField('Комментарий', validators=[DataRequired()])
    submit = SubmitField('Отправить')


class Article(db.Model):
    """Post data storage table"""
    id = db.Column(db.Integer, primary_key=True)
    post_category = db.Column(db.String(30), nullable=False)
    name_img = db.Column(db.String(70), nullable=False)
    post_title = db.Column(db.String(100), nullable=False)
    card_text = db.Column(db.Text(), nullable=False)
    post_text = db.Column(db.Text(), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Article %r>' % self.post_title


class Comment(db.Model):
    """Сomment storage table"""
    id = db.Column(db.Integer, primary_key=True)
    name_user = db.Column(db.String(70), nullable=False)
    text = db.Column(db.Text(), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    post_title = db.Column(db.String(150))

    def __repr__(self):
        return '<Comment %r>' % self.id


class User(UserMixin, db.Model):
    """Amin data storage table"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<Email %r>' % self.email


class Email_page(db.Model):
    """Subscriber data storage table"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Email %r>' % self.id


@app.route('/email')
@login_required
def email():
    email_name = Email_page.query.all()
    return render_template('email.html', email=email_name)


@app.route('/', methods=['POST', 'GET'])
def index():
    articles_in_db = Article.query.all()
    articles = []
    len_articles = len(articles_in_db)
    if len_articles % 2 == 1:
        m = len_articles - 1
        while len(articles) != m:
            x = random.choice(articles_in_db)
            if x not in articles:
                articles.append(x)
    else:
        articles = articles_in_db
    if request.method == 'POST':
        email_name = request.form['email']
        post = Email_page(email=email_name)

        try:
            db.session.add(post)
            db.session.commit()
            return redirect('/')
        except:
            return 'При добавлении вашего Email произошла ошибка'
    else:
        return render_template('index_test.html', articles=articles)


@app.route('/post/<int:id>/comment', methods=['POST', 'GET'])
def comment(id):
    post = Article.query.get_or_404(id)
    title = 'comment'
    form = Leave_comment()
    if form.validate_on_submit():  # and request.method == 'POST':
        name = form.name.data
        text = form.text.data
        comment = Comment(name_user=name, text=text, post_title=post.post_title)
        try:
            db.session.add(comment)
            db.session.commit()
            flash('Ваш комментарий добавлен, благодарю')
        except:
            flash('При отправке Вашего отзывы произошла ошибка')
    return render_template('comment.html', title=title, form=form)


@app.route('/posts')
@login_required
def posts():
    articles = Article.query.order_by(Article.date.desc()).all()
    return render_template('posts.html', articles=articles)


@app.route('/posts/<int:id>')
def post_detail(id):
    article = Article.query.get(id)
    return render_template('post_detail.html', article=article)


@app.route('/all_comments')
def all_comments():
    comment = Comment.query.all()
    return render_template('all_comments.html', comments=comment)


@app.route('/posts/<int:id>/delete')
@login_required
def post_delete(id):
    article = Article.query.get_or_404(id)
    try:
        db.session.delete(article)
        db.session.commit()
        return redirect('/posts')

    except:
        return 'При удалении статьи произошла ошибка'


@app.route('/add_admin/<int:id>/delete')
@login_required
def admin_delete(id):
    admin = User.query.get_or_404(id)
    try:
        db.session.delete(admin)
        db.session.commit()
        return redirect('/add_admin')

    except:
        return 'При удалении пользователя произошла ошибка'


@app.route('/posts/<int:id>/update', methods=['POST', 'GET'])
def post_update(id):
    article = Article.query.get(id)
    if request.method == 'POST':
        file = request.files['name_img']
        filename = secure_filename(file.filename)
        article.name_img = file.filename
        article.post_title = request.form['post_title']
        article.card_text = request.form['card_text']
        article.post_text = request.form['post_text']
        article.post_category = request.form['post_category']
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))  # save image in static directory

        try:
            db.session.commit()
            return redirect('/posts')
        except:
            return 'При редактировании статьи произошла ошибка'
    else:

        return render_template('post_update.html', article=article)


@app.route('/create-article', methods=['POST', 'GET'])
@login_required
def create_article():
    if request.method == 'POST':
        file = request.files['name_img']  # get the image from form on site
        post_title = request.form['post_title']
        card_text = request.form['card_text']
        post_text = request.form['post_text']
        post_category = request.form['post_category']
        if file.filename == '':
            flash('Вы не выбрали ни одной картинки')
            return redirect(request.url)
        if file and post_title and post_text and card_text and post_category:
            filename = secure_filename(file.filename)  # never trust user input
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))  # save image in static directory
        else:
            flash('Заполните все поля')
        article = Article(post_title=post_title, post_category=post_category,
                          card_text=card_text, post_text=post_text, name_img=filename)

        try:
            db.session.add(article)
            db.session.commit()
            return redirect('/posts')
        except:
            return 'При добавлении статьи произошла ошибка'
    else:
        return render_template('create_article.html')


@app.route('/lifestyle')
def ls():
    articles = Article.query.filter(Article.post_category == 'Lifestyle').all()
    return render_template('lifestyle.html', articles=articles)


@app.route('/people')
def people():
    articles = Article.query.filter(Article.post_category == 'People').all()
    return render_template('people.html', articles=articles)


@app.route('/music')
def mus():
    articles = Article.query.filter(Article.post_category == 'Music').all()
    return render_template('music.html', articles=articles)


@app.route('/travel')
def tr():
    articles = Article.query.filter(Article.post_category == 'Travel').all()
    return render_template('travel.html', articles=articles)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('admin'))
    return render_template('login.html', title='Sign Up', form=form)


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/admin', methods=['POST', 'GET'])
@login_required
def admin():
    return render_template('admin.html', title='Admin Panel')


@app.route('/add_admin', methods=['POST', 'GET'])
@login_required
def add_admin():
    form = Add_admin()
    admin_in_db = User.query.all()
    user = User.query.filter_by(email=form.email.data).first()
    if user is not None:
        flash('Вы пытаетесь добавить пользователя, который уже есть в базе')
    elif form.validate_on_submit():  # and request.method == 'POST':
        password = generate_password_hash(form.password.data)
        email_post = form.email.data
        admin_add = User(email=email_post, password_hash=password)
        try:
            db.session.add(admin_add)
            db.session.commit()
            flash('Админ добавлен, милорд')
        except:
            flash('При добавлении статьи произошла ошибка')
    return render_template('add_admin.html', title='Add admin', form=form, email=admin_in_db)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Article': Article, 'Comment': Comment}


if __name__ == '__main__':
    app.run(debug=True)
