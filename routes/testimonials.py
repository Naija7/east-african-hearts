from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
from dotenv import load_dotenv
import os
from utils import log_event, log_error

load_dotenv()

testimonials = Blueprint('testimonials', __name__)

from db import db

@testimonials.route("/testimonials", methods=["GET", "POST"])
def add_testimonial():
    if request.method == "POST":
        male_name = request.form.get("male_name", "").strip()
        female_name = request.form.get("female_name", "").strip()
        country = request.form.get("country", "").strip()
        story = request.form.get("story", "").strip()

        if not all([male_name, female_name, country, story]):
            flash("All fields are required", "error")
            return redirect(url_for('testimonials.add_testimonial'))

        cursor = db.cursor()
        try:
            cursor.execute("""
                INSERT INTO testimonials (male_name, female_name, country, story, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (male_name, female_name, country, story, 'pending', datetime.now()))
            db.commit()
            flash("Thank you! Your story will be reviewed by our team soon.", "success")
            return redirect(url_for('home.index'))
        except Exception as e:
            log_error(f"Testimonial submission error: {e}", exc_info=True)
            flash("Error submitting testimonial. Please try again.", "error")
        finally:
            cursor.close()

    return render_template("testimonials.html")

@testimonials.route("/success-stories")
def view_testimonials():
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, male_name, female_name, country, story, created_at
        FROM testimonials
        WHERE status = 'approved'
        ORDER BY created_at DESC
    """)
    testimonials_list = cursor.fetchall()
    cursor.close()

    return render_template("success_stories.html",
                         testimonials=testimonials_list,
                         lang='en')

@testimonials.route("/api/testimonials")
def get_testimonials():
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, male_name, female_name, country, story, created_at
        FROM testimonials
        WHERE status = 'approved'
        ORDER BY created_at DESC
    """)
    testimonials_list = cursor.fetchall()
    cursor.close()

    for t in testimonials_list:
        if isinstance(t.get('created_at'), datetime):
            t['created_at'] = t['created_at'].isoformat()

    return jsonify(testimonials_list)
