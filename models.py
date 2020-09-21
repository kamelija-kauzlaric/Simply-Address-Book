import os
from sqla_wrapper import SQLAlchemy

db = SQLAlchemy(os.getenv("DATABASE_URL", "sqlite:///localhost.sqlite"))

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contact_user_name = db.Column(db.String, unique=False)
    contact_first_name = db.Column(db.String, unique=False)
    contact_last_name = db.Column(db.String, unique=False)
    contact_email = db.Column(db.String, unique=True)
    contact_telephone = db.Column(db.String, unique=False)
    contact_address = db.Column(db.String, unique=False)
    contact_city = db.Column(db.String, unique=False)
    contact_zipcode = db.Column(db.String, unique=False)
    contact_country = db.Column(db.String, unique=False)