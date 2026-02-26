from flask import Blueprint, request, jsonify, current_app
from flask_mail import Message
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
import secrets
import logging
from ..extensions import db, bcrypt, mail
from ..models.user import User
from flask_jwt_extended import create_access_token
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
                "message": "Email already registered and verified."
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
            "message": "Verification email sent."
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
        response.set_cookie(
            "access_token",
            access_token,
            httponly=True,
            secure=False,  
            samesite="Lax"
        )
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


def generate_verification_token():
    return secrets.token_urlsafe(32)