import sqlite3
from datetime import datetime
from functools import wraps

DATABASE_NAME = 'habitmaster.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Пользователи
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT,
            photo_url TEXT,
            balance INTEGER DEFAULT 0,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            streak INTEGER DEFAULT 0,
            habits_count INTEGER DEFAULT 0,
            completed_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Товары (заполним дефолтными при старте если пусто)
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price INTEGER,
            icon TEXT,
            description TEXT,
            type TEXT
        )
    ''')
    
    # Покупки
    c.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            user_id INTEGER,
            product_id INTEGER,
            bought_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, product_id)
        )
    ''')

    # Статьи библиотеки
    c.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            category TEXT,
            content TEXT,
            read_time TEXT
        )
    ''')

    # Прогресс чтения
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_reads (
            user_id INTEGER,
            article_id INTEGER,
            is_read BOOLEAN DEFAULT 0,
            PRIMARY KEY (user_id, article_id)
        )
    ''')

    # Достижения
    c.execute('''
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            desc TEXT,
            icon TEXT,
            condition_val INTEGER
        )
    ''')
    
    # Пользовательские достижения
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_achievements (
            user_id INTEGER,
            achievement_id INTEGER,
            earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, achievement_id)
        )
    ''')

    conn.commit()
    
    # Заполняем тестовыми данными, если таблицы пустые
    c.execute("SELECT count(*) FROM products")
    if c.fetchone()[0] == 0:
        products = [
            ('Премиум аватар', 500, '', 'Золотая рамка для профиля', 'cosmetic'),
            ('Ускоритель XP x2', 300, '', 'Двойной опыт на 24 часа', 'booster'),
            ('Защита серии', 200, '', 'Сохранит серию при пропуске', 'utility'),
            ('Набор мотивации', 100, '', '+50 монет бонусом', 'lootbox')
        ]
        c.executemany("INSERT INTO products (name, price, icon, description, type) VALUES (?, ?, ?, ?, ?)", products)
        
    c.execute("SELECT count(*) FROM articles")
    if c.fetchone()[0] == 0:
        articles = [
            ('Сон как фундамент', 'Здоровье', 'Недосып убивает продуктивность. Спи 8 часов.', '5 мин'),
            ('Петля привычки', 'Психология', 'Триггер -> Действие -> Награда.', '4 мин'),
            ('Матрица Эйзенхауэра', 'Продуктивность', 'Важное vs Срочное.', '6 мин'),
            ('Дофаминовое голодание', 'Развитие', 'Как перезагрузить мозг.', '7 мин')
        ]
        c.executemany("INSERT INTO articles (title, category, content, read_time) VALUES (?, ?, ?, ?)", articles)

    c.execute("SELECT count(*) FROM achievements")
    if c.fetchone()[0] == 0:
        achs = [
            ('Новичок', 'Создай первую привычку', '', 1),
            ('Боец', 'Выполни 10 задач', '', 10),
            ('Магнат', 'Накопи 1000 монет', '', 1000),
            ('Легенда', 'Достигни 30 уровня', '', 30)
        ]
        c.executemany("INSERT INTO achievements (name, desc, icon, condition_val) VALUES (?, ?, ?, ?)", achs)

    conn.commit()
    conn.close()

def get_or_create_user(tg_id, username, first_name, photo_url):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE telegram_id = ?", (str(tg_id),))
    user = c.fetchone()
    
    if not user:
        c.execute('''
            INSERT INTO users (telegram_id, username, first_name, photo_url)
            VALUES (?, ?, ?, ?)
        ''', (str(tg_id), username, first_name, photo_url))
        conn.commit()
        c.execute("SELECT * FROM users WHERE telegram_id = ?", (str(tg_id),))
        user = c.fetchone()
    
    conn.close()
    return dict(user)

def get_user_full_data(tg_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE telegram_id = ?", (str(tg_id),))
    user = c.fetchone()
    if not user: return None
    
    # Получаем покупки
    c.execute("SELECT product_id FROM purchases WHERE user_id = ?", (user['id'],))
    purchased_ids = [row['product_id'] for row in c.fetchall()]
    
    # Получаем прочитанные статьи
    c.execute("SELECT article_id FROM user_reads WHERE user_id = ? AND is_read = 1", (user['id'],))
    read_ids = [row['article_id'] for row in c.fetchall()]

    # Получаем достижения
    c.execute("SELECT a.* FROM achievements a JOIN user_achievements ua ON a.id = ua.achievement_id WHERE ua.user_id = ?", (user['id'],))
    earned_achs = [dict(row) for row in c.fetchall()]
    
    # Все достижения для сравнения
    c.execute("SELECT * FROM achievements")
    all_achs = [dict(row) for row in c.fetchall()]
    for ach in all_achs:
        ach['earned'] = any(a['id'] == ach['id'] for a in earned_achs)

    conn.close()
    
    return {
        'user': dict(user),
        'purchased_ids': purchased_ids,
        'read_ids': read_ids,
        'achievements': all_achs
    }

def buy_item(tg_id, product_id):
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT * FROM users WHERE telegram_id = ?", (str(tg_id),))
    user = c.fetchone()
    
    c.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = c.fetchone()
    
    if not user or not product:
        conn.close()
        return False, "Ошибка данных"
    
    if user['balance'] < product['price']:
        conn.close()
        return False, "Недостаточно монет"
    
    # Проверка на повторную покупку (если товар одноразовый)
    c.execute("SELECT * FROM purchases WHERE user_id = ? AND product_id = ?", (user['id'], product_id))
    if c.fetchone():
        conn.close()
        return False, "Уже куплено"

    # Списываем деньги
    new_balance = user['balance'] - product['price']
    c.execute("UPDATE users SET balance = ? WHERE telegram_id = ?", (new_balance, str(tg_id)))
    
    # Записываем покупку
    c.execute("INSERT INTO purchases (user_id, product_id) VALUES (?, ?)", (user['id'], product_id))
    
    # Начисляем эффект (упрощенно: просто даем бонус или меняем тип)
    if product['type'] == 'lootbox':
        bonus = 50
        c.execute("UPDATE users SET balance = balance + ? WHERE telegram_id = ?", (bonus, str(tg_id)))
        conn.commit()
        conn.close()
        return True, f"Куплено! Бонус: +{bonus} монет."

    conn.commit()
    conn.close()
    return True, "Покупка успешна!"

def mark_article_read(tg_id, article_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE telegram_id = ?", (str(tg_id),))
    user = c.fetchone()
    if not user: 
        conn.close()
        return False
    
    c.execute("INSERT OR REPLACE INTO user_reads (user_id, article_id, is_read) VALUES (?, ?, 1)", (user['id'], article_id))
    # Даем немного XP за чтение
    c.execute("UPDATE users SET xp = xp + 10 WHERE telegram_id = ?", (str(tg_id),))
    conn.commit()
    conn.close()
    return True

def get_leaderboard(limit=10):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT username, first_name, photo_url, level, xp, balance FROM users ORDER BY xp DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def find_user_by_id(search_id):
    conn = get_db_connection()
    c = conn.cursor()
    # Ищем по telegram_id (частичное совпадение или точное)
    c.execute("SELECT * FROM users WHERE telegram_id LIKE ?", (f"%{search_id}%",))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None
