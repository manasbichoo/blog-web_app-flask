import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from flaskblog import app, db, bcrypt
from flaskblog.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, ProjectForm
from flaskblog.models import User, Post, Project
from flask_login import login_user, current_user, logout_user, login_required
import pandas as pd
import urllib.request
import sqlite3
from bs4 import BeautifulSoup as bs
# NLP Packages
from textblob import TextBlob,Word 
import random 
import time
#PLOTS
import matplotlib.pyplot as plt
from wordcloud import WordCloud






#########HOME-Blogs Display################
@app.route("/")
@app.route("/home")
def home():
    posts = Post.query.all()
    projects = Project.query.all()
    return render_template('home.html', posts=posts, projects=projects)

#############ABOUT- ADD Project Description###########
@app.route("/about") 
def about():
    return render_template('about.html', title='About')

################Registration ######################
@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

##############LOGIN###########################################
@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

##############LOGOUT############################
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

######################PICTURE-Account##############
def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

##################UPDATE ACCOUNT########################
@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)

#################ADD POST################################
@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post',
                           form=form, legend='New Post')


###########################POST DESCRIPTION###############################
@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)

#########################UPDATE POST###################################
@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post',
                           form=form, legend='Update Post')

#########################DELETE POST#######################################

@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))



##########################ADD PROJECT - GITHUB SCRAPPER#############################
@app.route("/project", methods=['GET', 'POST'])
@login_required
def project():
    conn = sqlite3.connect(r"E:\COLLEGE PROJECTS\collegeproject\example.db")
    if request.method == 'POST': 
        result = request.form["URL"]
        inputurl=result
        url=inputurl+'?tab=repositories'
        df = {'Projects':[],'Link':[],'Language':[],'Name':[]}
        
        content = urllib.request.urlopen(url).read()
        soup = bs(content,'html.parser')

        for tag in soup.find_all('a',attrs={'itemprop':'name codeRepository'}):
            df['Projects'].append(str(tag.text))
                
        for link in soup.find_all('a',attrs={'itemprop':'name codeRepository'}):
            df['Link'].append('https://github.com'+str(link.get('href')))
        
        nm=soup.find('span', attrs={'class':'p-name vcard-fullname d-block overflow-hidden'})
        name=nm.text

        for div in soup.find_all('div', attrs={'class':'col-10 col-lg-9 d-inline-block'}):
            x=div.find('span',attrs={'itemprop':'programmingLanguage'})
            if x is None:
                df['Language'].append('None')
                df['Name'].append(name)
            else:
                df['Language'].append(x.text)
                df['Name'].append(name)
       
        df1=pd.DataFrame(df)
        
        #Database
        cur = conn.cursor()
        df1.to_sql('Projects', conn,if_exists='append', index=False)
        df2=pd.read_sql('select * from Projects', conn) 
        #pd.read_sql('select * from Projects', conn)
        conn.commit()
        conn.close()

        return render_template('index.html',result=url, table = df2.to_html()) # renders template: index.html with argument result = polarity value calculated
    else:
        conn = sqlite3.connect(r"E:\COLLEGE PROJECTS\collegeproject\example.db")
        cur = conn.cursor()
        df3=pd.read_sql('select * from Projects', conn) 
        conn.commit()
        conn.close()
        return render_template('index.html', table = df3.to_html())    


#################PROJECT TEST FORM################################
@app.route("/testproject", methods=['GET', 'POST'])
@login_required
def projecttest():
    form = ProjectForm()
    if form.validate_on_submit():
        project = Project(title=form.title.data, url=form.url.data, language=form.language.data, author=form.author.data)
        db.session.add(project)
        db.session.commit()
        flash('Your project has been added!', 'success')
        return redirect(url_for('home'))
    return render_template('projecttest.html', title='New Project',
                           form=form, legend='New Project')

###############################################################
@app.route('/analyse',methods=['POST','GET'])
@login_required
def analyse():
    start = time.time()
    if request.method == 'POST':
        result1 = float(request.form["ac"])
        result2 = float(request.form["ac2"])
        result3 = float(request.form["ac3"])
        result4 = float(request.form["ac4"])
        finalresult=result1+result2+result3+result4
        ########PLOT#################
        data = pd.array(['Computer Lab','Library','Faculty','Cleanliness'])
        names =pd.array([result1,result2,result3,result4])
        
        plt.bar(data, names,color='black')
        '''fig, axs = plt.subplots(1, 3, figsize=(10,10), sharey=True)
        axs[0].bar(names, values)
        axs[1].scatter(names, values)
        axs[2].plot(names, values)
        fig.suptitle('Categorical Plotting')'''
        name=str(current_user.id)
        path=r"E:/COLLEGE PROJECTS/blog/flask/flaskblog/static/images/"
        finalpath=path+name+'.png'
        plt.savefig(finalpath)
        urllll='/static/images/'+name+'.png'
        ####################NLP#################
        rawtext = request.form['rawtext']
        ########plot wordmap################
        name1=name+'word'
        finalpath1=path+name1+'.png'
        text=(str(rawtext))
        wordcloud = WordCloud(width=480, height=480, margin=0).generate(text)
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")
        plt.margins(x=0, y=0)
        plt.savefig(finalpath1)
        urlll='/static/images/'+name1+'.png'

        #NLP Stuff
        blob = TextBlob(rawtext)
        received_text2 = blob
        blob_sentiment,blob_subjectivity = blob.sentiment.polarity+finalresult,blob.sentiment.subjectivity
        if blob_sentiment > 0:
            return render_template('positive.html',user=current_user.username,blob_sentiment=blob_sentiment,blob_subjectivity=blob_subjectivity,url =urllll,url1=urlll)
        else:
            return render_template('negative.html',user=current_user.username,blob_sentiment=blob_sentiment,blob_subjectivity=blob_subjectivity,url =urllll,url1=urlll)
        
    else:
        return render_template('feedback.html')


