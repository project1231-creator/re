import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = "habitmaster-secret-key-2026-no-auth"

# Декоратор для защиты страниц (просто проверяет, есть ли юзер в сессии)
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    # --- АВТОМАТИЧЕСКИЙ ВХОД БЕЗ ПРОВЕРКИ ---
    # Мы просто создаем тестового пользователя при каждом заходе на главную
    session['user_id'] = '123456789'
    session['user_name'] = 'Феликс (Demo)'
    session['username'] = 'felix_dev'
    session['photo_url'] = '' # Можно вставить ссылку на картинку если хочешь
    
    print(">>> USER LOGGED IN AUTOMATICALLY (NO AUTH CHECK)")
    return redirect(url_for('home'))

@app.route('/home')
@login_required
def home():
    # Данные для главной
    data = {
        'user': {
            'first_name': session['user_name'],
            'level': 5,
            'xp': 450,
            'coins': 1200,
            'current_streak': 7,
            'longest_streak': 14,
            'joined_date': '2026-02-25',
        },
        'stats': {
            'total_habits': 8,
            'total_completed': 156,
            'active_goals': 3,
            'completed_goals': 2,
            'achievements': 5,
            'category_stats': [
                {'category': 'Чтение', 'count': 45},
                {'category': 'Спорт', 'count': 38},
                {'category': 'Вода', 'count': 42},
            ]
        }
    }
    return render_template('home.html', **data)

@app.route('/library')
@login_required
def library():
    categories = [
        {
            "name": "Фундамент", "icon": "🏗️",
            "articles": [
                { "title": "Сон — точка возврата", "content": "Сон важнее всего...", "read_time": "5 мин", "read": False, "favorite": False},
                { "title": "Еда как топливо", "content": "Избегай сахарных качелей...", "read_time": "4 мин", "read": True, "favorite": False},
            ]
        },
        {
            "name": "Привычки", "icon": "🔄",
            "articles": [
                { "title": "Петля привычки", "content": "Триггер -> Действие -> Награда", "read_time": "6 мин", "read": False, "favorite": False},
            ]
        }
    ]
    return render_template('library.html', categories=categories, total_articles=3, read_count=1, progress=33)

@app.route('/shop')
@login_required
def shop():
    items = [
        { "id": 1, "name": "Темная тема", "price": 500, "icon": "🎨", "desc": "Эксклюзивная тема", "can_afford": True, "purchased": False},
        { "id": 2, "name": "XP Бустер", "price": 300, "icon": "⚡", "desc": "x2 опыта на час", "can_afford": True, "purchased": False},
        { "id": 3, "name": "Золотая рамка", "price": 2000, "icon": "👑", "desc": "Для профиля", "can_afford": False, "purchased": False},
    ]
    return render_template('shop.html', items=items, user_coins=1200, recommended=items[:2])

@app.route('/stats')
@login_required
def stats():
    data = {
        'user': {'first_name': session['user_name'], 'level': 5, 'xp': 450},
        'stats': {
            'total_habits': 8,
            'total_completed': 156,
            'active_goals': 3,
            'completed_goals': 2,
            'achievements': 5,
            'category_stats': [
                {'category': 'Чтение', 'count': 45},
                {'category': 'Спорт', 'count': 38},
            ]
        }
    }
    return render_template('stats.html', **data)

@app.route('/achievements')
@login_required
def achievements():
    achs = [
        { "id": 1, "name": "Новичок", "desc": "Первая привычка", "icon": "🌱", "earned": True},
        { "id": 2, "name": "Стабильный", "desc": "7 дней подряд", "icon": "🔥", "earned": True},
        { "id": 3, "name": "Марафонец", "desc": "30 дней", "icon": "🏃", "earned": False},
        { "id": 4, "name": "Богач", "desc": "1000 монет", "icon": "💰", "earned": True},
    ]
    return render_template('achievements.html', achievements=achs)

@app.route('/profile')
@login_required
def profile():
    data = {
        'user': {
            'first_name': session['user_name'],
            'level': 5,
            'xp': 450,
            'coins': 1200,
            'current_streak': 7,
            'longest_streak': 14,
            'joined_date': '2026-02-25',
        },
        'stats': {'achievements': 5},
        'username': session['username'],
        'photo_url': session['photo_url']
    }
    return render_template('profile.html', **data)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
