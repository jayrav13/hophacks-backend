from flask import Flask, abort, request, jsonify, make_response
import requests
from sqlalchemy import Integer, ForeignKey, String, Column
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.associationproxy import association_proxy
from secret import db_host, db_username, db_password, db_database, google_secret_key
from model import Users, Requests, Claims, db

app = Flask(__name__)

google_key = google_secret_key

development = True

# database setup
my_host = db_host
my_username = db_username
my_password = db_password
my_database = db_database

@app.route("/")
def hello():
	return "Hello, I love HopHacks!"

@app.route("/api/v0.1/register", methods=['POST'])
def register():
	if not all (k in request.form for k in ("username","password","email","phone","address")):
		return make_response(jsonify({'error':'Invalid usage. Must include username, password, email, phone and address.'}), 400)
	else:
		def validate(input):
			return len(input) >= 8 and len(input) <= 16
	
		if validate(request.form['username']) and validate(request.form['password']):
			user = Users.query.filter_by(username=request.form['username']).first()
			if not user:
				user = Users(request.form['username'], request.form['password'], request.form['email'], request.form['phone'], request.form['address'])
				db.session.add(user)
				db.session.commit()
				return make_response(jsonify(
					{'success':{
							'username':user.username,
							'email':user.email,
							'phone':user.phone,
							'address':user.address,
							'user_token':user.user_token	
						}
					}), 200)	
			else:
				return make_response(jsonify({'error':'Username already exists!'}), 400)
		else:	
			return make_response(jsonify({'error':'Username or Password not between 8 and 16 characters.'}), 400)


@app.route("/api/v0.1/requests/add", methods=['POST'])		
def add_request():
	if not request.form['user_token']:
		return make_response(jsonify({'error':'User token not found.'}), 400)
	else:
		user_token = request.form['user_token']
		user = Users.query.filter_by(user_token = user_token).first()
		if user:
			user_request = Requests(request.form['title'], request.form['type'], request.form['description'], request.form['paid'], request.form['estimated_time'], request.form['complete_by'])
			user.requests.append(user_request)
			db.session.commit()
			return make_response(jsonify({'success', 'Added request!'}), 200)
		else:
			return make_response(jsonify({'error':'Messed up token?'}), 400)


@app.route("/api/v0.1/users/get", methods=['GET'])
def get_user():
	if request.args['user_id'] and request.args['user_token']:
		search_user = Users.query.filter_by(id=request.args['user_id']).first()
		user = Users.query.filter_by(user_token=request.args['user_token']).first()
		if not user or not search_user:
			return make_response(jsonify({'error', 'User not found or authentication not provided.'}), 404)
		else:
			return make_response(jsonify({
				'username':user.username,
				'email':user.email,
				'phone':user.phone,
				'address':user.address
			}), 200)
	else:
		return make_response(jsonify({'error', 'Invalid usage - please include a User ID and User Token.'}), 400)

@app.route("/api/v0.1/types", methods=['GET'])
def types():
	if request.args['user_token']:
		user = Users.query.filter_by(user_token=request.args['user_token']).first()
		if user:
			types = Requests.query(Requests.type).distinct()
			for type in types:
				print type
		else:
			return make_response(jsonify({'error':'Messed up token?'}), 400) 
	else:
		return make_response(jsonify({'error':'Requires authentication.'}), 400)


if __name__ == "__main__":
	if not development:
		app.run(host='0.0.0.0')
	else:
		app.run(debug=True, host='45.33.69.6', port=5000)
