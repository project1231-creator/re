import os
import json
import hmac
import hashlib
import urllib.parse
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from functools import wraps
from database import init_db, get_or_create_user, get_user_full_data, buy_item, mark_article_read, get_leaderboard, find_user_by_id

app = Flask(__name__)
app.secret_key = os.urandom(24)
BOT_TOKEN = "8534219584:AAHW2T8MTmoR3dJN_bQDtru49lUSx401QqA" # Твой токен

# Инициализация БД при старте
init_db()

def check_telegram_authorization(init_data: str) -> dict:
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
        
        if hmac_hash == hash_value:
            user_data = json.loads(parsed_data.get('user', ['{}'])[0])
            return user_data
        return None
    except Exception as e:
        print(f"Auth error: {e}")
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
    tg_user = check_telegram_authorization(init_data)
    
    if tg_user:
        session['user_id'] = str(tg_user['id'])
        session['username'] = tg_user.get('username', '')
        session['first_name'] = tg_user.get('first_name', 'User')
        session['photo_url'] = tg_user.get('photo_url', '')
        
        # Создаем или обновляем юзера в БД
        get_or_create_user(
            tg_user['id'], 
            session['username'], 
            session['first_name'], 
            session['photo_url']
        )
        return redirect(url_for('home'))
    
    # Для тестов в браузере (раскомментируй для локальной проверки без ТГ)
    # session['user_id'] = '12345'
    # session['first_name'] = 'TestUser'
    # return redirect(url_for('home'))
    
    return render_template('index.html', error="Authorization failed")

@app.context_processor
def utility_processor():
    def get_current_user():
        if 'user_id' not in session: return None
        data = get_user_full_data(session['user_id'])
        if data:
            return data['user']
        return None
    return dict(current_user=get_current_user())

@app.route('/home')
@login_required
def home():
    data = get_user_full_data(session['user_id'])
    return render_template('home.html', data=data)

@app.route('/library')
@login_required
def library():
    # В реальном проекте нужно выгружать статьи из БД в шаблон
    # Пока используем заглушку структуры, но с проверкой прочтения
    data = get_user_full_data(session['user_id'])
    # Хардкод статей для примера (лучше вынести в БД запрос)
    from database import get_db_connection
    conn = get_db_connection()
    articles = conn.execute("SELECT * FROM articles").fetchall()
    conn.close()
    
    categories = {}
    for art in articles:
        cat = art['category']
        if cat not in categories: categories[cat] = []
        art_dict = dict(art)
        art_dict['is_read'] = art['id'] in data['read_ids']
        categories[cat].append(art_dict)
        
    return render_template('library.html', categories=categories, read_count=len(data['read_ids']))

@app.route('/shop')
@login_required
def shop():
    data = get_user_full_data(session['user_id'])
    from database import get_db_connection
    conn = get_db_connection()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    
    items = []
    for p in products:
        pd = dict(p)
        pd['purchased'] = p['id'] in data['purchased_ids']
        pd['can_afford'] = data['user']['balance'] >= p['price']
        items.append(pd)
        
    return render_template('shop.html', items=items, user=data['user'])

@app.route('/stats')
@login_required
def stats():
    data = get_user_full_data(session['user_id'])
    leaderboard = get_leaderboard(10)
    return render_template('stats.html', data=data, leaderboard=leaderboard)

@app.route('/profile')
@login_required
def profile():
    data = get_user_full_data(session['user_id'])
    return render_template('profile.html', data=data)

@app.route('/search')
@login_required
def search():
    query = request.args.get('q', '')
    found_user = None
    if query:
        found_user = find_user_by_id(query)
        if found_user:
            # Получаем публичные данные найденного юзера
            from database import get_db_connection
            conn = get_db_connection()
            # Упрощенный профиль для чужого юзера
            pub_data = {
                'username': found_user['username'],
                'first_name': found_user['first_name'],
                'photo_url': found_user['photo_url'],
                'level': found_user['level'],
                'xp': found_user['xp'],
                'balance': found_user['balance'] # Можно скрыть баланс если нужно
            }
            found_user = pub_data
    return render_template('search.html', query=query, found_user=found_user)

@app.route('/api/buy/<int:product_id>', methods=['POST'])
@login_required
def api_buy(product_id):
    success, msg = buy_item(session['user_id'], product_id)
    return jsonify({'success': success, 'message': msg})

@app.route('/api/read/<int:article_id>', methods=['POST'])
@login_required
def api_read(article_id):
    success = mark_article_read(session['user_id'], article_id)
    return jsonify({'success': success})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
