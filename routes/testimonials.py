from flask import Blueprint, render_template, request, redirect, url_for
import mysql.connector
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

testimonials = Blueprint('testimonials', __name__)

# Database connection
from db import db

@testimonials.route("/testimonials", methods=["GET", "POST"])
def add_testimonial():
    if request.method == "POST":
        male_name = request.form.get("male_name")
        female_name = request.form.get("female_name")
        country = request.form.get("country")
        story = request.form.get("story")

        cursor = db.cursor()
        sql = "INSERT INTO testimonials (male_name, female_name, country, story, status) VALUES (%s, %s, %s, %s, 'approved')"
        values = (male_name, female_name, country, story)

        try:
            cursor.execute(sql, values)
            db.commit()
            return redirect(url_for('home.index'))
        except Exception as e:
            print(f"Error: {e}")
        finally:
            cursor.close()

    return render_template("testimonials.html")

@testimonials.route("/api/testimonials")
def get_testimonials():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM testimonials WHERE status = 'approved' ORDER BY created_at DESC")
    testimonials_list = cursor.fetchall()
    cursor.close()

    # Return as JSON
    import json
    from datetime import datetime

    for t in testimonials_list:
        t['created_at'] = t['created_at'].isoformat() if isinstance(t['created_at'], datetime) else str(t['created_at'])

    return json.dumps(testimonials_list)
