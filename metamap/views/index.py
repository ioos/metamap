from datetime import datetime

from flask import render_template, make_response, redirect, jsonify, flash, url_for, request
from metamap import app, db, login_manager
from metamap.models.user import User
from flask_login import login_required, login_user, logout_user, current_user
from flask.ext.wtf import Form
from wtforms import TextField, PasswordField, SelectField, FileField
from itertools import chain
import sys
import json
from bson import ObjectId
from StringIO import StringIO
from lxml import etree
from wicken.xml_dogma import XmlDogma

class LoginForm(Form):
    username = TextField(u'Name')
    password = PasswordField(u'Password')

class AddEvalSourceForm(Form):
    name        = TextField(u'Name')
    source_type = SelectField(u'Source Type')
    url         = TextField(u'URL')
    upload      = FileField(u'File')

namespaces = {
    "gmx":"http://www.isotc211.org/2005/gmx",
    "gsr":"http://www.isotc211.org/2005/gsr",
    "gss":"http://www.isotc211.org/2005/gss",
    "gts":"http://www.isotc211.org/2005/gts",
    "xs":"http://www.w3.org/2001/XMLSchema",
    "gml":"http://www.opengis.net/gml/3.2",
    "xlink":"http://www.w3.org/1999/xlink",
    "xsi":"http://www.w3.org/2001/XMLSchema-instance",
    "gco":"http://www.isotc211.org/2005/gco",
    "gmd":"http://www.isotc211.org/2005/gmd",
    "gmi":"http://www.isotc211.org/2005/gmi",
    "srv":"http://www.isotc211.org/2005/srv",
}

@app.route('/', methods=['GET'])
#@login_required
def index():
    # get all mappings
    mappings = list(db.Mapping.find().sort([('ioos_name',1)]))

    # set indicies to help the view out
    srcs = list(db.SourceType.find().sort([('name', 1)]))
    srcs_idx = [s._id for s in srcs]
    src_map = {s._id:s for s in srcs}

    # transform lists in correct order for table view
    for m in mappings:
        ql = [''] * len(srcs)
        for q in m.queries:
            idx = srcs_idx.index(q['source_type'])
            ql[idx] = q['query']

        m.queries = ql

    f = AddEvalSourceForm()
    f.source_type.choices = [(s._id, s.name) for s in srcs]

    # get eval sources
    def fix_source_type(eval_source):
        eval_source.source_type = src_map[eval_source.source_type].name
        return eval_source

    eval_sources = map(fix_source_type, db.EvalSource.find())

    return render_template('index.html',
                           mappings=mappings,
                           srcs=srcs,
                           form=f,
                           eval_sources=eval_sources)

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

@app.route('/eval_source', methods=['POST'])
def add_eval_source():
    print >>sys.stderr, request.form
    print >>sys.stderr, request.files

    eval_source = db.EvalSource()
    eval_source.name = request.form['name']
    eval_source.source_type = ObjectId(request.form['source_type'])
    eval_source.save()

    # switch on presence of file
    if 'upload' in request.files:
        file_obj = request.files['upload']
        eval_source.endpoint = file_obj.filename

        s = StringIO()
        for x in file_obj.read():
            s.write(x)

        #print >>sys.stderr, str(s.getvalue())
        eval_source.fs.src_file = str(s.getvalue())
        s.close()

    else:
        # @TODO: request.get the url, store it the same way
        eval_source.endpoint = request.form['url']
        pass

    eval_source.save()

    response = make_response(json.dumps({'name':eval_source.name,
                                          'source_type':db.SourceType.find_one({'_id':eval_source.source_type}).name,
                                          '_id': str(eval_source._id)}))

    response.headers['Content-type'] = 'application/json'
    return response

@app.route("/eval/<ObjectId:mapping_id>", methods=['GET'])
def eval_mapping(mapping_id):
    mapping = db.Mapping.find_one({'_id':mapping_id})

    # @TODO go into schema
    type_translate = {'ISO 19115'      : 'Iso19115',
                      'SWE XML'        : None,
                      'NetCDF CF NCML' : 'NetcdfCF'}

    type_map = {x._id:type_translate[x.name] for x in db.SourceType.find()}

    evals = []
    for query in mapping.queries:

        source_type_id = query['source_type']
        eval_sources = db.EvalSource.find({'source_type':source_type_id})

        cur_mappings = {'curval': query['query']}

        # load attachment from gridfs
        for eval_source in eval_sources:
            root = etree.fromstring(eval_source.fs.src_file)

            data_object = XmlDogma(type_map[source_type_id],
                                   cur_mappings,
                                   root,
                                   namespaces=namespaces)

            evals.append((str(eval_source._id), data_object.curval))

    return json.dumps(dict(evals))

