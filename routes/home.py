from flask import Blueprint, render_template, session, request, redirect, url_for
from translations import TRANSLATIONS, get_text

home = Blueprint('home', __name__)

@home.route("/")
def index():
    language = session.get('language', 'en')
    translations = TRANSLATIONS.get(language, TRANSLATIONS['en'])
    return render_template("home.html", lang=language, t=translations, get_text=get_text)

@home.route("/home")
def home_page():
    language = session.get('language', 'en')
    translations = TRANSLATIONS.get(language, TRANSLATIONS['en'])
    return render_template("home.html", lang=language, t=translations, get_text=get_text)

@home.route("/about")
def about():
    language = session.get('language', 'en')
    translations = TRANSLATIONS.get(language, TRANSLATIONS['en'])
    return render_template("about.html", lang=language, t=translations, get_text=get_text)

@home.route("/set-language/<language>")
def set_language(language):
    if language in TRANSLATIONS:
        session['language'] = language
    return redirect(request.referrer or url_for('home.index'))
