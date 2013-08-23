from datetime import datetime

from flask import render_template, make_response, redirect, jsonify, flash, url_for, request
from metamap import app, db, login_manager
from metamap.models.user import User
from flask_login import login_required, login_user, logout_user, current_user
from flask.ext.wtf import Form
from wtforms import TextField, PasswordField
from itertools import chain
import sys
import json
from bson import ObjectId

class LoginForm(Form):
    username = TextField(u'Name')
    password = PasswordField(u'Password')

@app.route('/', methods=['GET'])
#@login_required
def index():
    # get all mappings
    mappings = list(db.Mapping.find().sort([('ioos_name',1)]))

    # set indicies to help the view out
    srcs = list(db.SourceType.find().sort([('name', 1)]))
    srcs_idx = [s._id for s in srcs]

    # transform lists in correct order for table view
    for m in mappings:
        ql = [''] * len(srcs)
        for q in m.queries:
            idx = srcs_idx.index(q['source_type'])
            ql[idx] = q['query']

        m.queries = ql

    return render_template('index.html', mappings=mappings, srcs=srcs)

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

@app.route('/mapping', methods=['POST'])
def update_mapping():
    mapping = json.loads(request.form['data'])

    if '_id' in mapping and mapping['_id']:
        db_mapping = db.Mapping.find_one({'_id':ObjectId(mapping['_id'])})
        assert db_mapping
    else:
        db_mapping = db.Mapping()

    db_mapping.ioos_name = mapping['ioos_name']
    db_mapping.queries = [{'source_type':ObjectId(x['source_type']),
                           'query': x['query']} for x in mapping['queries']]

    db_mapping.save()

    return str(db_mapping._id)

@app.route('/delete_mapping', methods=['POST'])
def delete_mapping():
    mapping = db.Mapping.find_one({'_id':ObjectId(request.form['id'])})
    mapping.delete()
    return ""

