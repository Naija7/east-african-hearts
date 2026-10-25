from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
from functools import lru_cache
from utils import log_event, log_error, log_info

# Load environment variables
load_dotenv()

matching = Blueprint('matching', __name__)

from db import db

# Simple cache for discovery page
_cache = {'data': None, 'timestamp': None}

def insert_notification(user_id, actor_id, notification_type, related_id=""):
    try:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO notifications (user_id, actor_id, type, related_id, read_status, created_at)
            VALUES (%s, %s, %s, %s, 0, %s)
        """, (user_id, actor_id, notification_type, related_id, datetime.now()))
        db.commit()
        cursor.close()
    except Exception as e:
        log_error(f"Notification error for user {user_id}: {e}", exc_info=True, user_id=user_id)

def get_user_notifications(user_id, limit=10):
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT n.id, n.actor_id, n.type, u.full_name as actor_name, n.created_at, n.read_status
            FROM notifications n
            JOIN users u ON n.actor_id = u.id
            WHERE n.user_id = %s
            ORDER BY n.created_at DESC
            LIMIT %s
        """, (user_id, limit))
        notifications = cursor.fetchall()
        cursor.close()
        return notifications
    except Exception as e:
        log_error(f"Get notifications error for user {user_id}: {e}", exc_info=True, user_id=user_id)
        return []

@matching.route("/discovery")
def discovery():
    if 'user_id' not in session:
        flash("Please login to browse profiles", "error")
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    language = session.get('language', 'en')

    # Check cache (30 second TTL). The cache holds ALL users; the viewer is
    # filtered out per request so one user's id never shapes everyone's list.
    if _cache['data'] and _cache['timestamp'] and datetime.now() - _cache['timestamp'] < timedelta(seconds=30):
        profiles = _cache['data']
    else:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.id, u.full_name as name, u.age, u.gender, p.bio, p.interests, p.location, p.profile_picture
            FROM users u
            LEFT JOIN profiles p ON u.id = p.user_id
            ORDER BY u.created_at DESC
            LIMIT 200
        """)
        profiles = cursor.fetchall()
        cursor.close()

        # Cache the results
        _cache['data'] = profiles
        _cache['timestamp'] = datetime.now()

    profiles = [p for p in profiles if p['id'] != user_id][:50]

    # Get user's likes
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT liked_id FROM likes WHERE liker_id = %s", (user_id,))
    liked_users = [row['liked_id'] for row in cursor.fetchall()]
    cursor.close()

    return render_template("discovery.html",
                         profiles=profiles,
                         liked_users=liked_users,
                         age_min=None,
                         age_max=None,
                         location=None,
                         interests=None,
                         lang=language)

@matching.route("/search")
def search():
    if 'user_id' not in session:
        flash("Please login to browse profiles", "error")
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    language = session.get('language', 'en')

    age_min = request.args.get('age_min', type=int)
    age_max = request.args.get('age_max', type=int)
    location = request.args.get('location', type=str)
    interests = request.args.get('interests', type=str)
    page = request.args.get('page', 1, type=int)

    per_page = 50
    offset = (page - 1) * per_page

    cursor = db.cursor(dictionary=True)

    query = """
        SELECT u.id, u.full_name as name, u.age, u.gender, p.bio, p.interests, p.location, p.profile_picture
        FROM users u
        LEFT JOIN profiles p ON u.id = p.user_id
        WHERE u.id != %s
    """
    params = [user_id]

    if age_min is not None:
        query += " AND u.age >= %s"
        params.append(age_min)

    if age_max is not None:
        query += " AND u.age <= %s"
        params.append(age_max)

    if location:
        query += " AND p.location LIKE %s"
        params.append(f"%{location}%")

    if interests:
        query += " AND p.interests LIKE %s"
        params.append(f"%{interests}%")

    query += " ORDER BY u.created_at DESC"

    count_query = query.replace("SELECT u.id, u.full_name as name, u.age, u.gender, p.bio, p.interests, p.location", "SELECT COUNT(*) as total")

    cursor.execute(count_query, params)
    total = cursor.fetchone()['total']

    query += f" LIMIT {per_page} OFFSET {offset}"
    cursor.execute(query, params)
    profiles = cursor.fetchall()

    cursor.execute("SELECT liked_id FROM likes WHERE liker_id = %s", (user_id,))
    liked_users = [row['liked_id'] for row in cursor.fetchall()]

    cursor.close()

    total_pages = (total + per_page - 1) // per_page

    pagination = {
        'page': page,
        'total_pages': total_pages,
        'total': total,
        'has_prev': page > 1,
        'prev_num': page - 1,
        'has_next': page < total_pages,
        'next_num': page + 1
    }

    return render_template("discovery.html",
                         profiles=profiles,
                         liked_users=liked_users,
                         pagination=pagination,
                         age_min=age_min,
                         age_max=age_max,
                         location=location,
                         interests=interests,
                         lang=language)

@matching.route("/like/<int:liked_user_id>", methods=["POST"])
def like_profile(liked_user_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    cursor = db.cursor()

    try:
        # Check if already liked
        cursor.execute("SELECT * FROM likes WHERE liker_id = %s AND liked_id = %s",
                      (user_id, liked_user_id))
        if not cursor.fetchone():
            # Add like
            cursor.execute("INSERT INTO likes (liker_id, liked_id, created_at) VALUES (%s, %s, %s)",
                          (user_id, liked_user_id, datetime.now()))
            db.commit()

            # Log event
            log_event(user_id, 'USER_LIKE', f"Liked user {liked_user_id}")

            # Send notification
            insert_notification(liked_user_id, user_id, 'like', str(liked_user_id))

            # Check if it's a mutual like (match)
            cursor.execute("SELECT * FROM likes WHERE liker_id = %s AND liked_id = %s",
                          (liked_user_id, user_id))
            if cursor.fetchone():
                # Create match
                cursor.execute("SELECT * FROM matches WHERE (user1_id = %s AND user2_id = %s) OR (user1_id = %s AND user2_id = %s)",
                              (user_id, liked_user_id, liked_user_id, user_id))
                if not cursor.fetchone():
                    cursor.execute("INSERT INTO matches (user1_id, user2_id, status, created_at) VALUES (%s, %s, %s, %s)",
                                  (user_id, liked_user_id, 'Matched', datetime.now()))
                    db.commit()

                    # Log match event
                    log_event(user_id, 'USER_MATCH', f"Matched with user {liked_user_id}")

                    # Send match notifications
                    insert_notification(liked_user_id, user_id, 'match', str(liked_user_id))

                    flash("It's a match! 💕", "success")

        cursor.close()
    except Exception as e:
        log_error(f"Like Error for user {user_id}: {e}", exc_info=True, user_id=user_id)
        flash("Error liking profile", "error")

    return redirect(url_for('matching.discovery'))

@matching.route("/unlike/<int:liked_user_id>", methods=["POST"])
def unlike_profile(liked_user_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    cursor = db.cursor()

    try:
        cursor.execute("DELETE FROM likes WHERE liker_id = %s AND liked_id = %s",
                      (user_id, liked_user_id))
        db.commit()

        # Remove match if exists
        cursor.execute("DELETE FROM matches WHERE (user1_id = %s AND user2_id = %s) OR (user1_id = %s AND user2_id = %s)",
                      (user_id, liked_user_id, liked_user_id, user_id))
        db.commit()

        flash("Profile unliked", "success")
        cursor.close()
    except Exception as e:
        log_error(f"Unlike Error for user {user_id}: {e}", exc_info=True, user_id=user_id)
        flash("Error unliking profile", "error")

    return redirect(url_for('matching.discovery'))

@matching.route("/matches")
def matches():
    if 'user_id' not in session:
        flash("Please login to view matches", "error")
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    language = session.get('language', 'en')

    cursor = db.cursor(dictionary=True)

    # Get all matches
    cursor.execute("""
        SELECT u.id, u.full_name as name, u.age, u.gender, p.bio, p.location, p.profile_picture
        FROM matches m
        JOIN users u ON (
            (m.user1_id = %s AND u.id = m.user2_id) OR
            (m.user2_id = %s AND u.id = m.user1_id)
        )
        LEFT JOIN profiles p ON u.id = p.user_id
        WHERE m.status = 'Matched'
        ORDER BY m.created_at DESC
    """, (user_id, user_id))

    matches_list = cursor.fetchall()
    cursor.close()

    return render_template("matches.html",
                         matches=matches_list,
                         lang=language)

@matching.route("/messages/<int:match_user_id>")
def messages(match_user_id):
    if 'user_id' not in session:
        flash("Please login to view messages", "error")
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    language = session.get('language', 'en')

    cursor = db.cursor(dictionary=True)

    # Verify they are matched
    cursor.execute("""
        SELECT id FROM matches
        WHERE ((user1_id = %s AND user2_id = %s) OR (user1_id = %s AND user2_id = %s))
        AND status = 'Matched'
    """, (user_id, match_user_id, match_user_id, user_id))

    match = cursor.fetchone()
    if not match:
        flash("You can only message your matches", "error")
        cursor.close()
        return redirect(url_for('matching.matches'))

    match_id = match['id']

    # Get match user info
    cursor.execute("""
        SELECT u.id, u.full_name as name, u.age, p.location, p.profile_picture
        FROM users u
        LEFT JOIN profiles p ON u.id = p.user_id
        WHERE u.id = %s
    """, (match_user_id,))
    match_user = cursor.fetchone()

    # Get messages
    cursor.execute("""
        SELECT * FROM messages
        WHERE match_id = %s
        ORDER BY sent_at ASC
    """, (match_id,))

    conversation = cursor.fetchall()
    cursor.close()

    return render_template("messages.html",
                         match_user=match_user,
                         match_id=match_id,
                         conversation=conversation,
                         lang=language)

@matching.route("/send-message/<int:receiver_id>", methods=["POST"])
def send_message(receiver_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    message_text = request.form.get("message", "").strip()

    if not message_text:
        flash("Message cannot be empty", "error")
        return redirect(url_for('matching.messages', match_user_id=receiver_id))

    cursor = db.cursor()

    try:
        # Get the match_id
        cursor.execute("""
            SELECT id FROM matches
            WHERE ((user1_id = %s AND user2_id = %s) OR (user1_id = %s AND user2_id = %s))
            AND status = 'Matched'
        """, (user_id, receiver_id, receiver_id, user_id))

        match = cursor.fetchone()
        if not match:
            flash("Match not found", "error")
            cursor.close()
            return redirect(url_for('matching.matches'))

        match_id = match[0]

        cursor.execute("""
            INSERT INTO messages (match_id, sender_id, message_text, sent_at)
            VALUES (%s, %s, %s, %s)
        """, (match_id, user_id, message_text, datetime.now()))
        db.commit()

        # Log message event
        log_event(user_id, 'USER_MESSAGE', f"Sent message to user {receiver_id}")

        # Send notification
        insert_notification(receiver_id, user_id, 'message', str(match_id))

        flash("Message sent!", "success")
        cursor.close()
    except Exception as e:
        log_error(f"Message Error for user {user_id}: {e}", exc_info=True, user_id=user_id)
        flash("Error sending message", "error")

    return redirect(url_for('matching.messages', match_user_id=receiver_id))

@matching.route("/notifications")
def notifications():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    notifs = get_user_notifications(user_id)

    return render_template("notifications.html",
                         notifications=notifs,
                         unread_count=sum(1 for n in notifs if not n['read_status']),
                         lang=session.get('language', 'en'))

@matching.route("/notifications/mark-read/<int:notif_id>", methods=["POST"])
def mark_notification_read(notif_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    try:
        cursor = db.cursor()
        cursor.execute("UPDATE notifications SET read_status = 1 WHERE id = %s", (notif_id,))
        db.commit()
        cursor.close()
    except Exception as e:
        log_error(f"Mark read error for notification {notif_id}: {e}", exc_info=True, user_id=user_id)

    return redirect(request.referrer or url_for('matching.notifications'))

@matching.route("/api/notifications/unread-count")
def unread_notifications_count():
    if 'user_id' not in session:
        return jsonify({'count': 0})

    user_id = session['user_id']
    try:
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM notifications WHERE user_id = %s AND read_status = 0", (user_id,))
        result = cursor.fetchone()
        cursor.close()
        return jsonify({'count': result[0] if result else 0})
    except Exception as e:
        log_error(f"Count error for user {user_id}: {e}", exc_info=True, user_id=user_id)
        return jsonify({'count': 0})
