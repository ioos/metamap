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
import requests
from netCDF4 import Dataset
from petulantbear.netcdf2ncml import dataset2ncml
import tempfile
from collections import defaultdict

class LoginForm(Form):
    username = TextField(u'Name')
    password = PasswordField(u'Password')

class AddEvalSourceForm(Form):
    name        = TextField(u'Name')
    source_type = SelectField(u'Source Type')
    url         = TextField(u'URL')
    upload      = FileField(u'File')

namespaces = {
    "gmx"      : "http://www.isotc211.org/2005/gmx",
    "gsr"      : "http://www.isotc211.org/2005/gsr",
    "gss"      : "http://www.isotc211.org/2005/gss",
    "gts"      : "http://www.isotc211.org/2005/gts",
    "xs"       : "http://www.w3.org/2001/XMLSchema",
    "gml"      : "http://www.opengis.net/gml",
    "xlink"    : "http://www.w3.org/1999/xlink",
    "xsi"      : "http://www.w3.org/2001/XMLSchema-instance",
    "gco"      : "http://www.isotc211.org/2005/gco",
    "gmd"      : "http://www.isotc211.org/2005/gmd",
    "gmi"      : "http://www.isotc211.org/2005/gmi",
    "srv"      : "http://www.isotc211.org/2005/srv",
    "ncml"     : "http://www.unidata.ucar.edu/namespaces/netcdf/ncml-2.2",
    "sos"      : "http://www.opengis.net/sos/1.0",
    "ows"      : "http://www.opengis.net/ows/1.1",
    "om"       : "http://www.opengis.net/om/1.0",
    "sml"      : "http://www.opengis.net/sensorML/1.0.1",
    "swe"      : "http://www.opengis.net/swe/1.0.1",
    "swe2"     : "http://www.opengis.net/swe/2.0",
}

@app.route('/', methods=['GET'])
@app.route('/<ObjectId:map_set_id>', methods=['GET'])
#@login_required
def index(map_set_id=None):

    if map_set_id is None:
        ms = db.MapSet.find_one({'name':'Default'})
        # Create the default MapSet as "Default"
        if ms is None:
            ms = db.MapSet()
            ms.name = u"Default"
            ms.save()
        map_set = ms
    else:
        map_set = db.MapSet.find_one({'_id':map_set_id})


    # list of map sets
    map_sets = list(db.MapSet.find())

    # mappings counted by map sets
    agg = db[db.Mapping.__collection__].aggregate({'$group':{'_id':'$map_set',
                                                             'count': { '$sum': 1}}})

    # create default map_set_id -> 0 to catch empty mapsets
    map_set_lookup = {m._id:{'count':0, 'name':m.name} for m in map_sets}
    for a in agg['result']:
        map_set_lookup[a['_id']]['count'] = a['count']


    # get all mappings
    mappings = map_set.mappings

    # set indicies to help the view out
    srcs = map_set.src_types
    srcs_idx = [s._id for s in srcs]
    src_map = {s._id:s for s in srcs}

    # transform lists in correct order for table view
    for m in mappings:
        ql = [''] * len(srcs)
        for q in m.queries:
            if q['source_type'] in srcs_idx:
                idx = srcs_idx.index(q['source_type'])
                ql[idx] = q['query']

        m.queries = ql

    all_srcs = list(db.SourceType.find().sort([('name', 1)]))
    src_map = {s._id:s for s in all_srcs}

    # reduce all srcs to remove srcs, then put srcs on front. this is for ordering
    # in the source type modal
    all_srcs = srcs + [s for s in all_srcs if s not in srcs]

    f = AddEvalSourceForm()
    f.source_type.choices = [(s._id, s.name) for s in srcs]

    # get eval sources
    def fix_source_type(eval_source):
        eval_source.source_type = src_map[eval_source.source_type].name
        return eval_source

    # add a blank eval source at the front, used as a hidden HTML template
    eval_sources = map(fix_source_type, db.EvalSource.find())
    eval_sources.insert(0, db.EvalSource())

    return render_template('index.html',
                           map_set=map_set,
                           map_sets=map_sets,
                           map_set_lookup=map_set_lookup,
                           mappings=mappings,
                           srcs=srcs,
                           all_srcs=all_srcs,
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
    db_mapping.description = mapping['description']
    db_mapping.map_set = ObjectId(mapping['map_set'])
    db_mapping.queries = [{'source_type':ObjectId(x['source_type']),
                           'query': x['query']} for x in mapping['queries']]

    db_mapping.save()

    return str(db_mapping._id)

@app.route('/delete_mapping', methods=['POST'])
def delete_mapping():
    mapping = db.Mapping.find_one({'_id':ObjectId(request.form['id'])})
    mapping.delete()
    return ""

@app.route('/eval_source/<ObjectId:eval_source_id>', methods=['GET'])
def get_eval_source(eval_source_id):
    eval_source = db.EvalSource.find_one({'_id':eval_source_id})

    return json.dumps({'_id': str(eval_source._id),
                       'name': eval_source.name,
                       'source_type': str(eval_source.source_type),
                       'endpoint': eval_source.endpoint})

@app.route('/eval_source', methods=['POST'])
@app.route('/eval_source/<ObjectId:eval_source_id>', methods=['POST'])
def eval_source(eval_source_id=None):
    eval_source = None
    if eval_source_id:
        eval_source = db.EvalSource.find_one({'_id':eval_source_id})
    else:
        eval_source = db.EvalSource()

    eval_source.name = request.form['name']
    eval_source.source_type = ObjectId(request.form['source_type'])
    eval_source.save()

    # switch on presence of file
    if 'upload' in request.files and request.files['upload'].filename != '':
        file_obj = request.files['upload']
        eval_source.endpoint = file_obj.filename

        # unfortunately we can't seem to switch on mimetype as both ncml and nc files
        # come through as "application/octet-stream" so we'll just cheaply switch on file ending
        s = StringIO()

        if file_obj.filename.endswith(".nc"):
            with tempfile.NamedTemporaryFile() as f:
                file_obj.save(f)

                # use pb to rip an ncml file, save that
                d = Dataset(f.name)
                s.write(dataset2ncml(d))
                d.close()

            # endpoint name should end with .ncml now
            eval_source.endpoint += "ml"

            # ensure user picked source type correctly
            eval_source.source_type = db.SourceType.find_one({'name':'NetCDF CF NCML'})._id

        else:
            for x in file_obj.read():
                s.write(x)

        eval_source.fs.src_file = str(s.getvalue())
        s.close()

    elif 'url' in request.form and request.form['url'] != "":
        url = request.form['url']
        r = requests.head(url)
        content = None
        if 'content-description' in r.headers and r.headers['content-description'].startswith('dods-'):
            if url.endswith(".html"):
                url = url[0:-5]

            d = Dataset(url)
            content = dataset2ncml(d)
            d.close()

            # ensure user picked source type correctly
            eval_source.source_type = db.SourceType.find_one({'name':'NetCDF CF NCML'})._id
        else:
            r = requests.get(url)
            r.raise_for_status()
            content = str(r.content)

        eval_source.fs.src_file = content
        eval_source.endpoint = url

    eval_source.save()

    response = make_response(json.dumps({'name':eval_source.name,
                                          'source_type':db.SourceType.find_one({'_id':eval_source.source_type}).name,
                                          '_id': str(eval_source._id)}))

    response.headers['Content-type'] = 'application/json'
    return response

@app.route('/delete_source', methods=['POST'])
def delete_source():
    eval_source = db.EvalSource.find_one({'_id':ObjectId(request.form['id'])})
    eval_source.delete()
    return ""

@app.route("/eval/<ObjectId:mapping_id>", methods=['GET'])
def eval_mapping(mapping_id):
    mapping = db.Mapping.find_one({'_id':mapping_id})

    evals = []
    for query in mapping.queries:

        source_type_id = query['source_type']
        eval_sources = db.EvalSource.find({'source_type':source_type_id})

        cur_mappings = {'curval': query['query']}

        # load attachment from gridfs
        for eval_source in eval_sources:
            try:
                root = etree.fromstring(eval_source.fs.src_file)
            except:
                print >>sys.stderr, "Could not parse:", eval_source.fs.src_file

            data_object = XmlDogma(str(source_type_id),    # any identifier here
                                   cur_mappings,
                                   root,
                                   namespaces=namespaces)

            evals.append((str(eval_source._id), data_object.curval))

    return json.dumps(dict(evals))

@app.route("/download/<ObjectId:map_set_id>/<ObjectId:source_type_id>", methods=['GET'])
def download_map_set(map_set_id, source_type_id):

    map_set = db.MapSet.find_one({'_id':map_set_id})
    map_file = map_set.make_source_mapping(source_type_id)

    response = make_response(json.dumps(map_file, indent=2))
    response.headers["Content-type"] = "application/json"
    response.headers["Content-Disposition"] = "attachment;filename=%s_%s.json" % (map_set_id, source_type_id)
    return response

@app.route("/map_set", methods=['POST'])
def new_map_set():
    map_set = json.loads(request.form['data'])

    db_map_set = db.MapSet()

    db_map_set.name = map_set['name']
    db_map_set.save()

    if map_set['copySrc']:
        src_id = ObjectId(map_set['copySrc'])
        db_map_set.parent = src_id

        # copy all mappings
        # @TODO: the parent property should make this irrelevent
        mappings = db.Mapping.find({'map_set':src_id})
        for mapping in mappings:
            #mapping._id = None      # gen a new one
            new_mapping = db.Mapping()
            new_mapping.ioos_name = mapping.ioos_name
            new_mapping.queries = mapping.queries
            new_mapping.map_set = db_map_set._id

            new_mapping.save()

        db_map_set.save()

    retval = {'_id':str(db_map_set._id)}
    response = make_response(json.dumps(retval))
    response.headers['Content-type'] = 'application/json'

    return response

@app.route("/import", methods=['POST'])
def import_mapping():

    map_set = db.MapSet()
    map_set.name = request.form['name']
    map_set.save()

    file_obj = request.files['upload']
    mapfile = json.load(file_obj)

    map_set.import_mapping(mapfile)

    retval = {'_id':str(map_set._id)}
    response = make_response(json.dumps(retval))
    response.headers['Content-type'] = 'application/json'

    return response

@app.route('/mapping/<ObjectId:map_set_id>/<ObjectId:source_type_id>', methods=['GET'])
def get_mapping_data(map_set_id, source_type_id):
    """
    Returns JSON of current mappings for this MapSet and SourceType.

    { "mapping id" -> "query", ... }
    """
    map_set = db.MapSet.find_one({'_id': map_set_id})
    mappings = db.Mapping.find({'map_set': map_set_id,
                                'queries.source_type': source_type_id})

    retval = {str(m._id):[q['query'] for q in m.queries if q['source_type'] == source_type_id][0] for m in mappings}

    response = make_response(json.dumps(retval))
    response.headers['Content-type'] = 'application/json'

    return response

@app.route('/mapset_sources/<ObjectId:map_set_id>', methods=['POST'])
def update_mapset_sources(map_set_id):
    source_types = json.loads(request.form['data'])

    map_set = db.MapSet.find_one({'_id': map_set_id})
    map_set.source_types = [ObjectId(x) for x in source_types]
    map_set.save()

    return ""

@app.route('/source_type', methods=['POST'])
def add_source_type():
    name = request.form['name']

    source_type = db.SourceType()
    source_type.name = name
    source_type.save()

    retval = {'_id': str(source_type._id),
              'name': name}

    response = make_response(json.dumps(retval))
    response.headers['Content-type'] = 'application/json'

    return response

