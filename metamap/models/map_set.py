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
        src_types = list((db.SourceType.find_one({'_id':src}) for src in self.source_types))
        return src_types

    def make_source_mapping(self, source_type_id):
        """
        Creates a source mapping to be used by wicken.
        """

        source_type = db.SourceType.find_one({'_id':source_type_id})

        map_file = {'__name__' : self.name,
                    '__source_mapping_type__' : source_type.name}

        mappings = db.Mapping.find({'map_set':self._id,
                                    'queries.source_type': source_type_id})

        for m in mappings:
            map_file[m.ioos_name] = {'query': [q['query'] for q in m.queries if q['source_type'] == source_type_id][0]}
            if m.description:
                map_file[m.ioos_name]['desc'] = m.description

        return map_file

