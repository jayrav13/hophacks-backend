from flask import Flask, abort, request, jsonify, make_response, render_template
import requests
from sqlalchemy import Integer, ForeignKey, String, Column
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.associationproxy import association_proxy
from secret import db_host, db_username, db_password, db_database, google_secret_key
from model import Users, Requests, Claims, db
import hashlib

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

@app.route("/api/v0.1/docs", methods=['GET'])
def docs():
	return render_template("page.html")

@app.route("/api/v0.1/register", methods=['GET'])
def register():
        if not all (k in request.args for k in ("username","password","email","phone","zip_code", "name")):
                return make_response(jsonify({'error':'Invalid usage. Must include username, password, email, phone, zip_code and name.'}), 400)
        else:
                def validate(input):
                        return len(input) >= 8 and len(input) <= 16

                if validate(request.args['username']) and validate(request.args['password']):
                        user = Users.query.filter_by(username=request.args['username']).first()
                        if not user:
                                user = Users(request.args['username'], request.args['password'], request.args['email'], request.args['phone'], request.args['zip_code'], request.args['name'])
                                db.session.add(user)
                                db.session.commit()
                                return make_response(jsonify(
                                        {'success':{
                                                        'username':user.username,
                                                        'email':user.email,
                                                        'phone':user.phone,
                                                        'zip_code':user.zip_code,
                                                        'user_token':user.user_token,
                                                        'name':user.name
                                                }
                                        }), 200)
                        else:
                                return make_response(jsonify({'error':'Username already exists!'}), 400)
                else:
                        return make_response(jsonify({'error':'Username or Password not between 8 and 16 characters.'}), 400)

@app.route("/api/v0.1/login", methods=['GET'])
def login():
	if request.args['username'] and request.args['password']:
		user = Users.query.filter_by(username=request.args['username']).filter_by(password=hashlib.md5(request.args['password']).hexdigest()).first()
		if not user:
			return make_response(jsonify({'error':'User not found.'}), 400)
		else:
			return make_response(jsonify({'success':user.user_token}), 200)
	else:
		return make_response(jsonify({'error':'Must include username and password.'}), 400)

@app.route("/api/v0.1/requests/add", methods=['GET'])		
def add_request():
	if not request.args['user_token']:
		return make_response(jsonify({'error':'User token not found.'}), 400)
	else:
		user_token = request.args['user_token']
		user = Users.query.filter_by(user_token = user_token).first()
		if user:
			user_request = Requests(request.args['title'], request.args['type'], request.args['description'], request.args['paid'], request.args['estimated_time'], request.args['complete_by'])
			user.requests.append(user_request)
			db.session.commit()
			return make_response(jsonify({'success': 'Added request!'}), 200)
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
				'id':user.id,
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
			types = Requests.query.all()
			reply = []
			arr = {}
			for type in types:
				if type.users.zip_code == user.zip_code:
					if not type.type in reply:
						reply.append(type.type)
			
			for item in reply:
				arr[str(len(arr))] = str(item)

			return make_response(jsonify(arr), 200)
	
		else:
			return make_response(jsonify({'error':'Messed up token?'}), 400) 
	else:
		return make_response(jsonify({'error':'Requires authentication.'}), 400)

@app.route("/api/v0.1/requests/all")
def all_requests():
	if request.args['user_token']:
		user = Users.query.filter_by(user_token = request.args['user_token']).first()
		if user:
			all_requests = Requests.query.all()
			reply = {}
			for req in all_requests:
				if req.users.zip_code == user.zip_code or req.users.id == user.id:
					reply[str(len(reply))] = {
								'id':req.id,
								'user_id':req.user_id,
								'claim_id':req.claim_id,
								'title':req.title,
								'type':req.type,
								'description':req.description,
								'paid':req.paid,
								'estimated_time':req.estimated_time,
								'complete_by':req.complete_by					
							}
			
			return make_response(jsonify(reply), 200)
		else:
			return make_response(jsonify({'error':'User authentication failed.'}), 400)		

	else:
		return make_response(jsonify({'error':'Authentication needed.'}), 400)

@app.route("/api/v0.1/claims/add", methods=['GET'])
def add_claim():
	if request.args['user_token']:
		user = Users.query.filter_by(user_token = request.args['user_token']).first()
		if user:
			claim_request = Requests.query.filter_by(id=request.args['request_id']).first()
			if claim_request:
				claim = Claims(request.args['request_id'], user.id, request.args['notes'])
				claim_request.claims.append(claim)
				db.session.commit()
				return make_response(jsonify({'success':'Claim added!'}), 200)
			else:
				return make_response(jsonify({'error':'Request ID invalid.'}), 400)
		else:
			return make_response(jsonify({'error':'Authentication failed.'}), 400)
	else:
		return make_reponse(jsonify({'error':'Authentication needed.'}), 400)


@app.route("/api/v0.1/claims/confirm", methods=['GET'])
def confirm_claim():
	if request.args['user_token']:
		user = Users.query.filter_by(user_token=request.args['user_token']).first()
		if not user:
			return make_response(jsonify({'error':'Authentication failed'}), 400)
		else:
			req = Requests.query.filter_by(id=request.args['request_id']).first()
			claim = Claims.query.filter_by(id=request.args['claim_id']).first()
			req.claim_id = claim.id
			claim.complete_flag = 1
			db.session.commit()
			return make_response(jsonify({'success':'Claim complete.'}), 200)
	else:
		return make_response(jsonify({'error':'Authentication required.'}), 400)

@app.route("/api/v0.1/claims/get", methods=['GET'])
def get_claims():
	if request.args['user_token']:
		user = Users.query.filter_by(user_token=request.args['user_token']).first()
		if not user:
			return make_response(jsonify({'error':'Authentication failed.'}), 400)
		else:
			claims = Claims.query.filter_by(user_id=user.id).all()
			reply = []
			for claim in claims:
				arr = {
					'request_id':claim.request_id,
					'user_id':claim.user_id,
					'notes':claim.notes,
					'complete_flag':claim.complete_flag,
					'request':
						{
							'user_id':claim.requests.user_id,
							'claim_id':claim.requests.claim_id,
							'title':claim.requests.title,
							'type':claim.requests.type,
							'description':claim.requests.description,
							'paid':claim.requests.paid,
							'estimated_time':claim.requests.estimated_time,
							'complete_by':claim.requests.complete_by
						}	
				}
				reply.append(arr)
				
			return make_response(jsonify({'data':reply}), 200)
	
	else:
		return make_response(jsonify({'error':'Authentication required.'}), 400)


@app.route("/api/v0.1/requests/get", methods=['GET'])
def get_requests():
	if request.args['user_token']:
		user = Users.query.filter_by(user_token=request.args['user_token']).first()
		if not user:
			return make_response(jsonify({'error':'Authentication failed.'}), 400)
		else:
			reply = []
			for req in user.requests:
				arr = {
					'id':req.id,
					'user_id':req.user_id,
					'claim_id':req.claim_id,
					'title':req.title,
					'type':req.type,
					'description':req.description,
					'paid':req.paid,
					'estimated_time':req.estimated_time,
					'complete_by':req.complete_by
					}
				reply.append(arr)
				
			return make_response(jsonify({'data':reply}), 200)		
	
	else:
		return make_response(jsonify({'error':'Requires authentication'}), 400)

@app.route("/api/v0.1/test", methods=['GET'])
def testing():
	return make_response(jsonify({'success':'FINALLY.'}), 200)

if __name__ == "__main__":
	if not development:
		app.run(host='0.0.0.0')
	else:
		app.run(debug=True, host='45.33.69.6', port=5000)
