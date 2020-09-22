import json
import os
import requests

from flask import Flask, render_template, request, redirect, url_for, make_response
from models import Contact, db
from requests_oauthlib import OAuth2Session

try:
    import secrets
except ImportError as e:
    pass


app = Flask(__name__)
db.create_all()


@app.route("/")
def index():
    return render_template("index.html")


# LOGIN
@app.route("/github/login")
def github_login():
    github = OAuth2Session(os.environ.get("GITHUB_CLIENT_ID"))
    authorization_url, state = github.authorization_url("https://github.com/login/oauth/authorize")

    response = make_response(redirect(authorization_url))
    response.set_cookie("oauth_state", state, httponly=True)

    return response


@app.route("/github/callback")
def github_callback():
    github = OAuth2Session(os.environ.get("GITHUB_CLIENT_ID"), state=request.cookies.get("oauth_state"))
    token = github.fetch_token("https://github.com/login/oauth/access_token",
                                client_secret=os.environ.get("GITHUB_CLIENT_SECRET"),
                                authorization_response=request.url)

    response = make_response(redirect(url_for("my_contacts")))
    response.set_cookie("oauth_token", json.dumps(token), httponly=True)

    return response


# LOGOUT
@app.route("/github/logout")
def logout():
    response = make_response(redirect(url_for("index")))
    response.set_cookie("oauth_token", expires=0)

    return response


# VIEW USER'S CONTACT LIST
@app.route("/my_contacts", methods=["GET"])
def my_contacts():
    github = OAuth2Session(os.environ.get("GITHUB_CLIENT_ID"), token=json.loads(request.cookies.get("oauth_token")))
    github_profile_data = github.get("https://api.github.com/user").json()

    user_name = github_profile_data.get("login")

    # show all contacts belonging to that user based on their username
    contacts = db.query(Contact).filter_by(contact_user_name=user_name).all()

    return render_template("my_contacts.html", github_profile_data=github_profile_data, user_name=user_name, contacts=contacts)


# INPUT NEW CONTACT DATA
@app.route("/add_contact", methods=["GET", "POST"])
def add_contact():
    github = OAuth2Session(os.environ.get("GITHUB_CLIENT_ID"), token=json.loads(request.cookies.get("oauth_token")))
    github_profile_data = github.get("https://api.github.com/user").json()

    return render_template("add_contact.html", github_profile_data=github_profile_data)


# SAVE NEW CONTACT INTO DATABASE
@app.route("/store_contact", methods=["GET", "POST"])
def store_contact():
    github = OAuth2Session(os.environ.get("GITHUB_CLIENT_ID"), token=json.loads(request.cookies.get("oauth_token")))
    github_profile_data = github.get("https://api.github.com/user").json()

    user_name = github_profile_data.get("login")

    # get user and new contact data
    contact_user_name = user_name
    contact_first_name = request.form.get("contact_first_name")
    contact_last_name = request.form.get("contact_last_name")
    contact_email = request.form.get("contact_email")
    contact_telephone = request.form.get("contact_telephone")
    contact_address = request.form.get("contact_address")
    contact_city = request.form.get("contact_city")
    contact_zipcode = request.form.get("contact_zipcode")
    contact_country = request.form.get("contact_country")

    # create a contact object
    contact = Contact(contact_user_name=contact_user_name,
                      contact_first_name=contact_first_name,
                      contact_last_name=contact_last_name,
                      contact_email=contact_email,
                      contact_telephone=contact_telephone,
                      contact_address=contact_address,
                      contact_city=contact_city,
                      contact_zipcode=contact_zipcode,
                      contact_country=contact_country)

    # save the contact object into a database
    db.add(contact)
    db.commit()

    return redirect(url_for("success"))


# VIEW DETAILS FOR INDIVIDUAL CONTACT & API SETUP
@app.route("/contact/<contact_id>", methods=["GET"])
def contact_details(contact_id):
    github = OAuth2Session(os.environ.get("GITHUB_CLIENT_ID"), token=json.loads(request.cookies.get("oauth_token")))
    github_profile_data = github.get("https://api.github.com/user").json()

    contact = db.query(Contact).get(int(contact_id)) # query by id

# OPENWEATHER.ORG API SETUP
    query = contact.contact_city
    unit = "metric"
    api_key = os.environ.get("API_KEY_OPENWEATHER")

    url = "https://api.openweathermap.org/data/2.5/weather?q={0}&units={1}&appid={2}".format(query, unit, api_key)

    data = requests.get(url=url)

    return render_template("contact_details.html", contact=contact, github_profile_data=github_profile_data, data=data.json())


# EDIT CONTACT DETAILS
@app.route("/contact/edit/<contact_id>", methods=["GET", "POST"])
def contact_edit(contact_id):
    github = OAuth2Session(os.environ.get("GITHUB_CLIENT_ID"), token=json.loads(request.cookies.get("oauth_token")))
    github_profile_data = github.get("https://api.github.com/user").json()

    contact = db.query(Contact).get(int(contact_id)) # query by id

    if request.method == "GET":
        if contact:
            return render_template("contact_edit.html", contact=contact, github_profile_data=github_profile_data)
        else:
            return redirect(url_for("my_contacts"))

    elif request.method == "POST":
        contact_first_name = request.form.get("contact_first_name")
        contact_last_name = request.form.get("contact_last_name")
        contact_email = request.form.get("contact_email")
        contact_telephone = request.form.get("contact_telephone")
        contact_address = request.form.get("contact_address")
        contact_city = request.form.get("contact_city")
        contact_zipcode = request.form.get("contact_zipcode")
        contact_country = request.form.get("contact_country")

        # update the contact object
        contact.contact_first_name = contact_first_name
        contact.contact_last_name = contact_last_name
        contact.contact_email = contact_email
        contact.contact_telephone = contact_telephone
        contact.contact_address = contact_address
        contact.contact_city = contact_city
        contact.contact_zipcode = contact_zipcode
        contact.contact_country = contact_country

        # store changes into the database
        db.add(contact)
        db.commit()

        return redirect(url_for("success"))


# DELETE ENTIRE CONTACT
@app.route("/contact/delete/<contact_id>", methods=["GET", "POST"])
def contact_delete(contact_id):
    github = OAuth2Session(os.environ.get("GITHUB_CLIENT_ID"), token=json.loads(request.cookies.get("oauth_token")))
    github_profile_data = github.get("https://api.github.com/user").json()

    contact = db.query(Contact).get(int(contact_id))  # query by id

    if request.method == "GET":
        if contact:  # if contact is found
            return render_template("contact_delete.html", contact=contact, github_profile_data=github_profile_data)
        else:
            return redirect(url_for("my_contacts"))

    elif request.method == "POST":
        # delete the contact in the database
        db.delete(contact)
        db.commit()

        return redirect(url_for("success"))


# SUCCESS MESSAGE FOR ADDING, EDITING AND DELETING CONTACTS
@app.route("/success")
def success():
    return render_template("success.html")


# SOCIAL DISTANCING CORNER (NASA API SETUP)
@app.route("/faraway")
def faraway():
    github = OAuth2Session(os.environ.get("GITHUB_CLIENT_ID"), token=json.loads(request.cookies.get("oauth_token")))
    github_profile_data = github.get("https://api.github.com/user").json()

    api_key = os.environ.get("API_KEY_NASA_APOD")

    url = "https://api.nasa.gov/planetary/apod?api_key={0}".format(api_key)

    data = requests.get(url=url)

    return render_template("faraway.html", github_profile_data=github_profile_data, data=data.json())


if __name__ == '__main__':
    app.run()
