import os
import json
import hmac
import hashlib
import urllib.parse
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from functools import wraps
from datetime import datetime

app = Flask(__name__)
# Секретный ключ для сессий (можно любой набор символов)
app.secret_key = "habitmaster-super-secret-key-change-in-prod"

# Токен твоего бота
BOT_TOKEN = "8534219584:AAHW2T8MTmoR3dJN_bQDtru49lUSx401QqA"

def check_telegram_authorization(init_data: str) -> dict:
    """Проверяет подпись данных от Telegram и возвращает данные пользователя"""
    if not init_data:
        return None
    
    try:
        parsed_data = urllib.parse.parse_qs(init_data)
        hash_value = parsed_data.get('hash', [''])[0]
        
        # Формируем строку данных для проверки (ключ=значение, отсортированные)
        data_check_list = []
        for key in sorted(parsed_data.keys()):
            if key != 'hash':
                data_check_list.append(f"{key}={parsed_data[key][0]}")
        data_check_string = '\n'.join(data_check_list)
        
        # Создаем секретный ключ из токена бота (HMAC-SHA256)
        secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
        
        # Вычисляем хеш
        hmac_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Сравниваем хеши
        if hmac_hash == hash_value:
            user_data_str = parsed_data.get('user', ['{}'])[0]
            return json.loads(user_data_str)
            
        return None
    except Exception as e:
        print(f"Auth error details: {e}")
        return None

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
    
    # 1. Пытаемся авторизовать через Telegram
    tg_user = check_telegram_authorization(init_data)
    
    if tg_user:
        # Успех! Сохраняем данные в сессию
        session['user_id'] = str(tg_user['id'])
        session['user_name'] = tg_user.get('first_name', 'User')
        session['username'] = tg_user.get('username', '')
        session['photo_url'] = tg_user.get('photo_url', '')
        return redirect(url_for('home'))
    
    # 2. РЕЖИМ РАЗРАБОТЧИКА (LOCALHOST)
    # Если ты запускаешь локально (без HTTPS), Telegram не передаст данные корректно.
    # Этот блок позволяет тебе зайти как "Тестовый пользователь" просто открыв сайт в браузере.
    host = request.host.split(':')[0]
    if host in ['127.0.0.1', 'localhost']:
        print("⚠️ LOCALHOST MODE: Авторизация пропущена для тестов.")
        session['user_id'] = '999999' 
        session['user_name'] = 'Феликс (Тест)'
        session['username'] = 'felix_dev'
        session['photo_url'] = ''
        return redirect(url_for('home'))

    # 3. Если это не localhost и проверка не прошла — показываем ошибку
    return render_template('index.html', error="Authorization failed. Открой приложение через бота в Telegram (нужен HTTPS).")

@app.context_processor
def utility_processor():
    def format_date(date_str):
        if not date_str: return ''
        try:
            # Попытка парсинга разных форматов
            if 'T' in date_str:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
            return dt.strftime('%d.%m.%Y')
        except:
            return date_str
            
    def format_number(num):
        if num is None: return "0"
        if num >= 1000000: return f"{num/1000000:.1f}M"
        elif num >= 1000: return f"{num/1000:.1f}K"
        return str(num)

    return dict(format_date=format_date, format_number=format_number)

# --- МОКОВЫЕ ДАННЫЕ (Временные, пока нет БД) ---
def get_user_stats(user_id):
    return {
        'user': {
            'first_name': session.get('user_name', 'User'),
            'level': 5,
            'xp': 450,
            'coins': 1200,
            'current_streak': 7,
            'longest_streak': 14,
            'joined_date': '2024-01-01',
        },
        'stats': {
            'total_habits': 8,
            'total_completed': 156,
            'active_goals': 3,
            'completed_goals': 2,
            'achievements': 5,
        }
    }

def get_achievements(user_id):
    return [
        { "id": 1, "name": "Новичок", "desc": "Создай первую привычку", "icon": "🌱", "earned": True},
        { "id": 2, "name": "Стабильный", "desc": "7 дней подряд", "icon": "🔥", "earned": True},
        { "id": 3, "name": "Марафонец", "desc": "30 дней подряд", "icon": "🏃", "earned": False},
        { "id": 4, "name": "Богач", "desc": "Накопи 1000 монет", "icon": "💰", "earned": True},
    ]

def get_library_articles(user_id):
    return {
        'categories': [
            {
                "name": "Фундамент", "icon": "🏗️",
                "articles": [
                    { "title": "Сон — точка возврата", "content": "Сон важнее всего...", "read_time": "5 мин", "read": False, "favorite": False},
                    { "title": "Еда как топливо", "content": "Избегай сахарных качелей...", "read_time": "4 мин", "read": True, "favorite": False},
                ]
            }
        ],
        'total_articles': 2,
        'read_count': 1,
        'progress': 50
    }

def get_shop_items(user_id):
    items = [
        { "id": 1, "name": "Темная тема", "price": 500, "icon": "🎨", "desc": "Эксклюзивная тема", "can_afford": True, "purchased": False},
        { "id": 2, "name": "XP Бустер", "price": 300, "icon": "⚡", "desc": "x2 опыта на час", "can_afford": True, "purchased": False},
        { "id": 3, "name": "Золотая рамка", "price": 2000, "icon": "👑", "desc": "Для профиля", "can_afford": False, "purchased": False},
    ]
    return {
        'items': items,
        'user_coins': 1200,
        'recommended': [i for i in items if i['can_afford'] and not i['purchased']]
    }

# --- МАРШРУТЫ ---

@app.route('/home')
@login_required
def home():
    data = get_user_stats(session['user_id'])
    return render_template('home.html', **data)

@app.route('/library')
@login_required
def library():
    data = get_library_articles(session['user_id'])
    return render_template('library.html', **data)

@app.route('/shop')
@login_required
def shop():
    data = get_shop_items(session['user_id'])
    return render_template('shop.html', **data)

@app.route('/stats')
@login_required
def stats():
    data = get_user_stats(session['user_id'])
    return render_template('stats.html', **data)

@app.route('/achievements')
@login_required
def achievements():
    achs = get_achievements(session['user_id'])
    return render_template('achievements.html', achievements=achs)

@app.route('/profile')
@login_required
def profile():
    data = get_user_stats(session['user_id'])
    data['username'] = session.get('username', '')
    data['photo_url'] = session.get('photo_url', '')
    return render_template('profile.html', **data)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Запуск на всех интерфейсах, порт 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
