from datetime import datetime
from metamap import db
from flask.ext.mongokit import Document
from bson import ObjectId

@db.register
class EvalSource(Document):
    __collection__ = 'eval_sources'
    use_dot_notation = True
    use_schemaless = True

    structure = {
        'name' : unicode,
        'endpoint': unicode,    # url or filename
        'source_type': ObjectId,
        'created'   : datetime,
        'updated'   : datetime,
    }

    gridfs = {
        'files':['src_file'],
    }

    default_values = {
        'created': datetime.utcnow
    }


