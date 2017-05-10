import jinja_filters
import pycountry
import pytz
from flask import Flask, g, session, url_for, redirect
from flask_debugtoolbar import DebugToolbarExtension
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from geoip import geolite2
from lxml.html.clean import Cleaner
from server import run_server

# Create and initialize app
app = Flask(__name__)
app.jinja_env.filters['pretty_date'] = jinja_filters.pretty_date
app.jinja_env.filters['supress_none'] = jinja_filters.supress_none
app.jinja_env.auto_reload = True
app.debug = True
app.config.from_object(__name__)
mail = Mail(app)
html_cleaner = Cleaner(page_structure=True, links=False)

# Load default config and override config from an environment variable
app.config.update(dict(
	SQLALCHEMY_DATABASE_URI='postgresql://devmsx-centercom:zazuKQ9c@192.168.1.104/devmsx-centercom',
	SQLALCHEMY_ECHO=True,
	MAIL_SERVER='192.168.1.200',
	DEFAULT_MAIL_SENDER='javi.lavandeira@msx-center.com',
	SECRET_KEY='e620f0121309a360fc596c481efd895da1c19b1e9358e87a',
	SERVER_NAME='dev.msx-center.com',
	DEBUG_TB_INTERCEPT_REDIRECTS=False,
	MAX_CONTENT_LENGTH=32*1024*1024
))
app.config.from_envvar('MSXCENTER_SETTINGS', silent=True)

db = SQLAlchemy(app)
toolbar = DebugToolbarExtension(app)

# Create ordered lists of countries and timezones
country_list = sorted(pycountry.countries, key = lambda c: c.name)
timezone_list = sorted(pytz.common_timezones)

#######################
## APPLICATION SETUP ##
#######################
    
# Create test user
@app.before_first_request
def create_database_tables():
	db.create_all()

from models import *
from routes import *
from routes.account import *
from routes.lounges import *
from routes.member import *
from routes.news import *
from routes.articles import *
from routes.admin import *
from routes.votes import *

#################################
## NON-SERVICEABLE PARTS BELOW ##
#################################

if __name__ == '__main__':
	run_server(app)

