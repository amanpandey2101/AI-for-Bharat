from marshmallow import Schema, fields, validate, ValidationError

class RegisterSchema(Schema):
    email = fields.Email(required=True)
    name = fields.String(
        required=True,
        validate=validate.Length(min=2, max=120)
    )
    password = fields.String(
        required=True,
        validate=validate.Length(min=6)
    )