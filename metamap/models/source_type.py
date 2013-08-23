from datetime import datetime
from metamap import db
from flask.ext.mongokit import Document

@db.register
class SourceType(Document):
    __collection__ = 'source_types'
    use_dot_notation = True
    use_schemaless = True

    structure = {
        'name'      : unicode,
        'created'   : datetime,
        'updated'   : datetime,
    }

    default_values = {
        'created': datetime.utcnow
    }

