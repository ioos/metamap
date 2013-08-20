from datetime import datetime
from ioos_metadata_mapper import db
from flask.ext.mongokit import Document

@db.register
class Mapping(Document):
    __collection__ = 'mappings'
    use_dot_notation = True
    use_schemaless = True

    structure = {
        'ioos_name' : unicode, # ioos concept name
        'queries'   : [{'source_type' :unicode,          # [ { "swe_xml" => xpath }, { "iso19110" => xpath } ... ]
                        'query'       :unicode}],
        'created'   : datetime,
        'updated'   : datetime,
    }

    default_values = {
        'created': datetime.utcnow
    }


