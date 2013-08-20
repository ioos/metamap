from datetime import datetime

from flask import render_template, make_response, redirect, jsonify, flash, url_for, request
from ioos_metadata_mapper import app, login_manager
from ioos_metadata_mapper.models.user import User
from flask_login import login_required, login_user, logout_user, current_user
from flask.ext.wtf import Form
from wtforms import TextField, PasswordField

class LoginForm(Form):
    username = TextField(u'Name')
    password = PasswordField(u'Password')

@app.route('/', methods=['GET'])
@login_required
def index():
    return render_template('index.html')

@login_manager.user_loader
def load_user(userid):
    return User.get(userid)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.validate(form.username.data, form.password.data)
        if not user:
            flash("Failed")
            return redirect(url_for("login"))

        login_user(user)
        flash("Logged in successfully")
        return redirect(request.args.get("next") or url_for("index"))

    return render_template("login.html", form=form)

@app.route('/logout', methods=['GET'])
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route('/crossdomain.xml', methods=['GET'])
def crossdomain():
    domain = """
    <cross-domain-policy>
        <allow-access-from domain="*"/>
        <site-control permitted-cross-domain-policies="all"/>
        <allow-http-request-headers-from domain="*" headers="*"/>
    </cross-domain-policy>
    """
    response = make_response(domain)
    response.headers["Content-type"] = "text/xml"
    return response

