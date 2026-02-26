from flask import Blueprint, request, jsonify, current_app
from flask_mail import Message
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
import secrets
import logging
from ..extensions import db, bcrypt, mail
from ..models.user import User
from ..validators.auth_validators import RegisterSchema
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


def generate_verification_token():
    return secrets.token_urlsafe(32)