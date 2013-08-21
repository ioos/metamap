import os
import urlparse

DEBUG = False
TESTING = False
LOG_FILE = True

WEB_PASSWORD = os.environ.get("WEB_PASSWORD")
SECRET_KEY = os.environ.get("SECRET_KEY")
SERVER_NAME = os.environ.get("SERVER_NAME", None)

# Database
MONGO_URI = os.environ.get('MONGO_URI')
url = urlparse.urlparse(MONGO_URI)
MONGODB_HOST = url.hostname
MONGODB_PORT = url.port
MONGODB_USERNAME = url.username
MONGODB_PASSWORD = url.password
MONGODB_DATABASE = url.path[1:]


