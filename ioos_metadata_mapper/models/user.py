import os
import os.path
import glob
import sys
from datetime import datetime
from ioos_metadata_mapper import app
from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id):
        self.id = id

    @classmethod
    def validate(cls, username, password):
        return None

    @classmethod
    def get(cls, id):
        return User(id)

