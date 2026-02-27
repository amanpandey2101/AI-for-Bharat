from flask import Blueprint, request, jsonify, current_app, redirect
import requests
from flask_mail import Message
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
import secrets
import logging
from ..extensions import db, bcrypt, mail
from ..models.user import User
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, set_access_cookies
from flask import make_response
from ..validators.auth_validators import RegisterSchema, LoginSchema
from ..utils.validators import validate_request
logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
@validate_request(RegisterSchema)
def register():
    try:
        data = request.validated_data

        existing_user = User.query.filter_by(email=data["email"]).first()

        if existing_user and existing_user.is_verified:
            return jsonify({
                "success": False,
                "message": "Email already registered."
            }), 400

        if existing_user and not existing_user.is_verified:
            db.session.delete(existing_user)
            db.session.commit()

        hashed_password = bcrypt.generate_password_hash(
            data["password"]
        ).decode("utf-8")

        token = generate_verification_token()

        new_user = User(
            email=data["email"],
            name=data["name"],
            password_hash=hashed_password,
            provider="email",
            verification_token=token,
            verification_token_expires=datetime.utcnow() + timedelta(hours=24),
            is_verified=False
        )

        db.session.add(new_user)
        db.session.commit()

        verification_link = f"http://localhost:5000/auth/verify-email?token={token}"

        msg = Message(
            subject="Verify your Memora.dev account",
            sender=current_app.config["MAIL_USERNAME"],
            recipients=[new_user.email]
        )

        msg.body = f"Click the link to verify your account:\n{verification_link}"
        mail.send(msg)

        return jsonify({
            "success": True,
            "message": "Verification email sent. Please verify your account to login"
        }), 200

    except SQLAlchemyError:
        db.session.rollback()
        logger.error("Database error during registration", exc_info=True)

        return jsonify({
            "success": False,
            "message": "Database error occurred."
        }), 500

    except Exception:
        db.session.rollback()
        logger.error("Database error during registration", exc_info=True)

        return jsonify({
            "success": False,
            "message": "Something went wrong."
        }), 500



@auth_bp.route("/login", methods=["POST"])
@validate_request(LoginSchema)
def login():
    try:
        data = request.validated_data

        user = User.query.filter_by(email=data["email"]).first()

        if not user:
            return jsonify({
                "success": False,
                "message": "Invalid email or password."
            }), 401

        if user.provider != "email":
            return jsonify({
                "success": False,
                "message": "Please login using GitHub."
            }), 400

        if user.is_deleted:
            return jsonify({
                "success": False,
                "message": "Account has been deleted."
            }), 403

        if user.is_inactive:
            return jsonify({
                "success": False,
                "message": "Account is inactive."
            }), 403

        if not user.is_verified:
            return jsonify({
                "success": False,
                "message": "Please verify your email before logging in."
            }), 403

        if not bcrypt.check_password_hash(user.password_hash, data["password"]):
            return jsonify({
                "success": False,
                "message": "Invalid email or password."
            }), 401

        access_token = create_access_token(identity=user.id)

        response = make_response(jsonify({
            "success": True,
            "message": "Login successful."
        }))
        set_access_cookies(response, access_token)

        return response

    except SQLAlchemyError:
        db.session.rollback()
        logger.error("Database error during login", exc_info=True)
        return jsonify({
            "success": False,
            "message": "Database error occurred."
        }), 500

    except Exception:
        logger.error("Unexpected error during login", exc_info=True)
        return jsonify({
            "success": False,
            "message": "Something went wrong."
        }), 500



@auth_bp.route("/verify-email", methods=["GET"])
def verify_email():
    try:
        token = request.args.get("token")

        if not token:
            return jsonify({
                "success": False,
                "message": "Verification token is required."
            }), 400

        user = User.query.filter_by(verification_token=token).first()

        if not user:
            return jsonify({
                "success": False,
                "message": "Invalid or expired verification token."
            }), 400

        if user.is_verified:
            return jsonify({
                "success": False,
                "message": "Email already verified."
            }), 400

        if user.verification_token_expires < datetime.utcnow():
            return jsonify({
                "success": False,
                "message": "Verification token has expired."
            }), 400

        user.is_verified = True
        user.verification_token = None
        user.verification_token_expires = None

        db.session.commit()

        return "Email verified successfully. You can now log in.", 200


    except SQLAlchemyError:
        db.session.rollback()
        logger.error("Database error during email verification", exc_info=True)
        return "Database error occurred.", 500

    except Exception:
        db.session.rollback()
        logger.error("Unexpected error during email verification", exc_info=True)
        return "Something went wrong.", 500


@auth_bp.route("/github", methods=["GET"])
def github_login():
    github_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={current_app.config['GITHUB_CLIENT_ID']}"
        f"&scope=user:email"
    )
    return redirect(github_url)



@auth_bp.route("/github/callback", methods=["GET"])
def github_callback():
    try:
        code = request.args.get("code")

        if not code:
            return "Authorization code not provided.", 400

        # Exchange code for access token
        token_response = requests.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": current_app.config["GITHUB_CLIENT_ID"],
                "client_secret": current_app.config["GITHUB_CLIENT_SECRET"],
                "code": code,
            },
        )

        token_json = token_response.json()
        access_token = token_json.get("access_token")

        if not access_token:
            return "Failed to obtain access token.", 400

        # Fetch GitHub user
        user_response = requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        github_user = user_response.json()

        github_id = str(github_user["id"])
        email = github_user.get("email")
        name = github_user.get("name") or github_user.get("login")
        avatar_url = github_user.get("avatar_url")

        # Some GitHub accounts don't return email in /user
        if not email:
            emails_response = requests.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            emails = emails_response.json()
            primary_email = next((e["email"] for e in emails if e["primary"]), None)
            email = primary_email

        if not email:
            return "Email not available from GitHub.", 400

        # Check if user exists
        user = User.query.filter_by(email=email).first()

        if user:
            # Link GitHub if not linked
            if not user.github_id:
                user.github_id = github_id
                user.avatar_url = avatar_url
                user.provider = "github"
                user.is_verified = True
                db.session.commit()
        else:
            # Create new user
            user = User(
                email=email,
                name=name,
                github_id=github_id,
                provider="github",
                avatar_url=avatar_url,
                is_verified=True,
            )
            db.session.add(user)
            db.session.commit()

        # Create JWT
        jwt_token = create_access_token(identity=user.id)

        # Set cookie
        response = redirect("http://localhost:3000/dashboard")
        set_access_cookies(response, jwt_token)

        return response

    except Exception as e:
        db.session.rollback()
        return f"GitHub login failed: {str(e)}", 500

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "avatar_url": user.avatar_url,
    }

def generate_verification_token():
    return secrets.token_urlsafe(32)