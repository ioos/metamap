from datetime import datetime
from metamap import db
from flask.ext.mongokit import Document
from bson import ObjectId

@db.register
class MapSet(Document):
    __collection__ = 'map_sets'
    use_dot_notation = True
    use_schemaless = True

    structure = {
        'name'    : unicode,
        'owner'   : ObjectId,
        'authors' : [ObjectId],
        'parent'  : ObjectId,   # ref to a "parent" MapSet if applicable
        'created' : datetime,
        'updated' : datetime,
    }

    default_values = {
        'created': datetime.utcnow
    }

