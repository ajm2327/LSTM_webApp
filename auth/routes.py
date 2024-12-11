from flask import Blueprint, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from oauthlib.oauth2 import WebApplicationClient
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from models.user import User
from database import db
import os
import json


auth = Blueprint('auth', __name__)
login_manager = LoginManager()
google_client_id = os.getenv('GOOGLE_CLIENT_ID')
google_client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
client = WebApplicationClient(google_client_id)



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

def get_google_provider_cfg():
    return requests.get(
        "https://accounts.google.com/.well-known/openid-configuration"
    ).json()

@auth.route("/register", methods=['POST'])
def register():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 400
    
    user = User(
        email = email,
        password_hash=generate_password_hash(password, method='scrypt')
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({
        "message": "User created successfully",
        "user":{
            "email": user.email,
            "id": str(user.user_id)
        }
    }), 201

@auth.route("/login", methods=['POST'])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid email or password"}), 401
    
    login_user(user)
    return jsonify({
        "message": "Logged in successfully",
        "user": {
            "email" : user.email,
            "id": str(user.user_id)
        }
    })

@auth.route("/google/auth-url", methods=['GET'])
def get_google_auth_url():
    """Return the google OAuth url instead of redirecting"""
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    request_url = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri = request.base_url.replace("/auth-url", "/callback"),
        scope = ["openid", "email", "profile"],
    )
    return jsonify({"auth_uri": request_url})

@auth.route("/google/login/callback")
def google_callback():
    code = request.args.get("code")
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response = request.url,
        redirect_url = request.base_url,
        code=code
    )

    token_response = requests.post(
        token_url, 
        headers = headers,
        data = body,
        auth=(google_client_id, google_client_secret),
    )

    client.parse_request_body_response(json.dumps(token_response.json()))

    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers = headers, data=body)

    if userinfo_response.json().get("email_verified"):
        email = userinfo_response.json()["email"]
        user = User.query.filter_by(email=email).first()

        if not user:
            user = User(email = email)
            db.session.add(user)
            db.session.commit()

        login_user(user)
        return jsonify({
            "message": "Logged in successfully via Google",
            "user": {
                "email": user.email,
                "id": str(user.user_id)
            }
        })
    return jsonify({"error": "User email not verified"}), 400



@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"})


@auth.route("/status")
@login_required
def auth_status():
    return jsonify({
        "authenticated": True,
        "user": {
            "email": current_user.email,
            "id": str(current_user.user_id)
        }
    })
