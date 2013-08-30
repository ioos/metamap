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
        'name'         : unicode,
        'owner'        : ObjectId,
        'authors'      : [ObjectId],
        'parent'       : ObjectId,   # ref to a "parent" MapSet if applicable
        'source_types' : [ObjectId], # list of source types to show on this MapSet
        'created'      : datetime,
        'updated'      : datetime,
    }

    default_values = {
        'created': datetime.utcnow
    }

    @property
    def mappings(self):
        mappings = list(db.Mapping.find({'map_set': self._id}).sort([('ioos_name',1)]))
        return mappings

    @property
    def src_types(self):
        """
        Not to be confused with actual db param source_types, this actually returns the database objects.
        """
        src_types = list((db.SourceType.find({'_id':src}) for src in self.source_types))
        return src_types

