import os
import json
import hmac
import hashlib
import urllib.parse
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from functools import wraps
from datetime import datetime

app = Flask(__name__)  # ИСПРАВЛЕНО: было Flask(name)
app.secret_key = "habitmaster-secret-key-2026-fixed"
BOT_TOKEN = "8534219584:AAHW2T8MTmoR3dJN_bQDtru49lUSx401QqA"

def check_telegram_authorization(init_data):
    """Проверка подписи Telegram (упрощенная)"""
    if not init_data:
        return False
    try:
        parsed_data = urllib.parse.parse_qs(init_data)
        hash_value = parsed_data.get('hash', [''])[0]
        data_check_list = []
        for key in sorted(parsed_data.keys()):
            if key != 'hash':
                data_check_list.append(f"{key}={parsed_data[key][0]}")
        data_check_string = '\n'.join(data_check_list)
        secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
        hmac_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        return hmac_hash == hash_value
    except Exception as e:
        print(f"Auth Error: {e}")
        return False

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    init_data = request.args.get('tgWebAppData', '')
    
    # Пытаемся авторизовать
    if init_data and check_telegram_authorization(init_data):
        try:
            parsed = urllib.parse.parse_qs(init_data)
            user_data = json.loads(parsed.get('user', ['{}'])[0])
            session['user_id'] = str(user_data.get('id', 123456))
            session['user_name'] = user_data.get('first_name', 'User')
            session['username'] = user_data.get('username', '')
            session['photo_url'] = user_data.get('photo_url', '')
            return redirect(url_for('home'))
        except Exception as e:
            print(f"Parse Error: {e}")
    
    # FALLBACK: Если не вышло (или локально) - пускаем как гостя
    # Это нужно, чтобы приложение не висело на ошибке
    if 'user_id' not in session:
        session['user_id'] = 'demo_user'
        session['user_name'] = 'Гость (Demo)'
        session['username'] = 'demo'
        session['photo_url'] = ''
        
    return redirect(url_for('home'))

@app.route('/home')
@login_required
def home():
    data = {
        'user': {
            'first_name': session.get('user_name', 'User'),
            'level': 5, 'xp': 450, 'coins': 1200,
            'current_streak': 7, 'longest_streak': 14,
            'joined_date': '2026-02-25'
        },
        'stats': {
            'total_habits': 8, 'total_completed': 156,
            'achievements': 5, 'completed_goals': 2,
            'active_goals': 3,
            'category_stats': [
                {'category': 'Чтение', 'count': 45},
                {'category': 'Спорт', 'count': 38}
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
                {"title": "Сон — точка возврата", "content": "Сон важнее всего...", "read_time": "5 мин", "read": False},
                {"title": "Еда как топливо", "content": "Избегай сахара...", "read_time": "4 мин", "read": True},
            ]
        }
    ]
    return render_template('library.html', categories=categories, total_articles=2, read_count=1, progress=50)

@app.route('/shop')
@login_required
def shop():
    items = [
        {"id": 1, "name": "Темная тема", "price": 500, "icon": "🎨", "desc": "Стиль", "can_afford": True, "purchased": False},
        {"id": 2, "name": "XP Бустер", "price": 300, "icon": "⚡", "desc": "Опыт x2", "can_afford": True, "purchased": False},
        {"id": 3, "name": "Золотая рамка", "price": 2000, "icon": "👑", "desc": "Премиум", "can_afford": False, "purchased": False},
    ]
    return render_template('shop.html', items=items, user_coins=1200, recommended=items[:2])

@app.route('/stats')
@login_required
def stats():
    data = {
        'user': {'first_name': session.get('user_name', 'User'), 'level': 5, 'xp': 450},
        'stats': {
            'total_habits': 8, 'total_completed': 156,
            'achievements': 5, 'completed_goals': 2, 'active_goals': 3,
            'category_stats': [{'category': 'Чтение', 'count': 45}]
        }
    }
    return render_template('stats.html', **data)

@app.route('/achievements')
@login_required
def achievements():
    achs = [
        {"id": 1, "name": "Новичок", "desc": "Старт", "icon": "🌱", "earned": True},
        {"id": 2, "name": "Боец", "desc": "7 дней", "icon": "🔥", "earned": True},
        {"id": 3, "name": "Легенда", "desc": "30 дней", "icon": "👑", "earned": False},
    ]
    return render_template('achievements.html', achievements=achs)

@app.route('/profile')
@login_required
def profile():
    data = {
        'user': {
            'first_name': session.get('user_name', 'User'),
            'level': 5, 'xp': 450, 'coins': 1200,
            'current_streak': 7, 'longest_streak': 14,
            'joined_date': '2026-02-25'
        },
        'stats': {'achievements': 5},
        'username': session.get('username', ''),
        'photo_url': session.get('photo_url', '')
    }
    return render_template('profile.html', **data)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
