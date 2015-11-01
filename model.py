from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref
from secret import secret_key
import hashlib
import time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = secret_key 
db = SQLAlchemy(app)

class Users(db.Model):
	__tablename__ = 'users'

	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String)
	password = db.Column(db.String)
	email = db.Column(db.String)
	phone = db.Column(db.String)
	zip_code = db.Column(db.String)
	user_token = db.Column(db.String)
	name = db.Column(db.String)

	requests = relationship("Requests", backref="users", primaryjoin=("Users.id==Requests.user_id"))
	claims = relationship("Claims", backref="users", primaryjoin=("Users.id==Claims.user_id"))

	def __init__(self, username, password, email, phone, zip_code, name):
		self.username = username
		self.password = hashlib.md5(password).hexdigest()
		self.email = email
		self.phone = phone
		self.zip_code = zip_code 
		self.user_token = hashlib.md5(username + ":" + str(time.time())).hexdigest()
		self.name = name

class Requests(db.Model):
	__tablename__ = 'requests'

	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, ForeignKey('users.id'))
	claim_id = db.Column(db.Integer, ForeignKey('claims.id'))
	title = db.Column(db.String)
	type = db.Column(db.String)
	description = db.Column(db.String)
	paid = db.Column(db.String)
	estimated_time = db.Column(db.String)
	complete_by = db.Column(db.String)

	claims = relationship("Claims", backref="requests", primaryjoin=("Requests.id==Claims.request_id"))	

	def __init__(self, title, type, description, paid, estimated_time, complete_by):
		self.claim_id = None
		self.title = title
		self.type = type
		self.description = description
		self.paid = paid
		self.estimated_time = estimated_time
		self.complete_by = complete_by

class Claims(db.Model):
	__tablename__ = 'claims'
	
	id = db.Column(db.Integer, primary_key=True)
	request_id = db.Column(db.Integer, ForeignKey('requests.id'))
	user_id = db.Column(db.Integer, ForeignKey('users.id'))
	notes = db.Column(db.String)
	complete_flag = db.Column(db.Integer)	
	
	def __init__(self, request_id, user_id, notes):
		self.request_id = request_id
		self.user_id = user_id
		self.notes = notes
		self.complete_flag = 0

