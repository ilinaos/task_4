from flask import Flask, request, jsonify
import sqlite3 as sq
from newsapi import NewsApiClient
import requests
from config import ap_key

api = NewsApiClient(api_key=ap_key)
app = Flask(__name__)
category_list = ['business', 'entertainment', 'general', 'health', 'science', 'sports', 'technology']

@app.route('/', methods=['GET','POST'])
def start_page():
    if request.method=='POST':
        return {'ok':True}
    if request.method == 'GET':
        return {'ok': True}

@app.route('/users', methods=['GET', 'POST'])
def users():
    if request.method == 'POST':
        chat_id = int(request.json['id'])
        try:
            connect = sq.connect('db_bot.db')
            cursor = connect.cursor()
            info = cursor.execute("SELECT * FROM users WHERE id_tg=?", (chat_id,)).fetchall()
            print (info)
            if len(info) == 0:
                cursor.execute("INSERT INTO users (id_tg) VALUES (?)", (chat_id,))
                connect.commit()
                print ('пользователь зарегистрирован')
        except sq.Error:
            print('ошибка подключения к базе при регистрации')
        finally:
            connect.close()
            return {'ok': True}

    if request.method == 'GET':
        return {'ok': True}

@app.route('/subscriptions/categories', methods=['GET', 'POST'])
def categories():
    if request.method == 'POST':
        chat_id = int(request.json['id'])
        command=str(request.json['command'])
        try:
            connect = sq.connect('db_bot.db')
            cursor = connect.cursor()
            answer = ''
            #выяснить, на какие категории подписан пользователь
            info = cursor.execute("""SELECT category
                            FROM categories
                            JOIN user_category ON categories.id=id_category
                            JOIN users ON users.id=id_user
                            WHERE users.id_tg=?""", (chat_id,)).fetchall()
            subscription = []
            for i in info:
                subscription.append(i[0])
            if command=='view':
                if len(subscription) == 0:
                    answer='вы пока ни на какие категории не подписаны, '
                else:
                    for i in subscription:
                        answer += i + ', '
            elif command=='add':
                cat=str(request.json['category'])
                if cat in subscription:
                    answer='Вы уже подписаны на эту категорию  '
                elif cat in category_list:
                    cursor.execute("""INSERT INTO user_category (id_user, id_category) VALUES
                    				((SELECT id FROM users WHERE id_tg=?),
                    				(SELECT id FROM categories WHERE category=?))""", (chat_id, cat))
                    connect.commit()
                    answer=f'Ура! Подписка на категорию {cat} добавлена  '
                else:
                    answer=f'На категорию {cat} подписаться нельзя  '
            else:
                cat = str(request.json['category'])
                if cat in subscription:
                    cursor.execute("""DELETE FROM user_category
                    WHERE id_user=(SELECT id FROM users WHERE id_tg=?)
                    AND id_category=(SELECT id FROM categories WHERE category=?)""", (chat_id, cat))
                    connect.commit()
                    answer=f'Вы больше не подписаны на категорию {cat}  '
                else:
                    answer=f'Подписку на категорию {cat} удалить нельзя  '
            return {'answer':answer}
        except sq.Error:
            print('ошибка подключения к базе при работе с категориями')
        finally:
            connect.close()
    if request.method == 'GET':
        return {'ok': True}

@app.route('/subscriptions/keywords', methods=['GET', 'POST'])
def keywords():
    if request.method == 'POST':
        chat_id = int(request.json['id'])
        command=str(request.json['command'])
        try:
            connect = sq.connect('db_bot.db')
            cursor = connect.cursor()
            answer = ''
        #выяснить, на какие ключевые слова подписан пользователь
            info = cursor.execute("""SELECT word
            FROM keywords
            JOIN user_keywords ON keywords.id=id_keyword
            JOIN users ON users.id=id_user
            WHERE id_tg=?""", (chat_id,)).fetchall()
            subscription=[]
            for i in info:
                subscription.append(i[0])
        #посмотреть, что нужно сделать с ключевыми словами
            if command=='view':
                if len(subscription)==0:
                    answer='у вас пока нет ключевых слов  '
                else:
                    for i in subscription:
                        answer += i + ', '
            elif command=='add':
                key = str(request.json['key'])
                # выяснить, какие ключевые слова есть в базе
                info2 = cursor.execute("""SELECT word FROM keywords""").fetchall()
                content = []
                for i in info2:
                    content.append(i[0])
                if key in subscription:
                    answer=f'Вы уже подписаны на ключевое слово {key}  '
                elif key in content:
                    cursor.execute("""INSERT INTO user_keywords (id_user, id_keyword) VALUES
                    ((SELECT id FROM users WHERE id_tg=?),
                     (SELECT id FROM keywords WHERE word=?))""", (chat_id, key))
                    connect.commit()
                    answer=f'Подписка на ключевое слово {key} добавлена  '
                else:
                    cursor.execute("""INSERT INTO keywords (word) VALUES (?)""", (key,))
                    connect.commit()
                    cursor.execute("""INSERT INTO user_keywords (id_user, id_keyword) VALUES
                                        ((SELECT id FROM users WHERE id_tg=?),
                                         (SELECT id FROM keywords WHERE word=?))""", (chat_id, key))
                    connect.commit()
                    answer = f'Подписка на ключевое слово {key} добавлена  '
            else:
                key = str(request.json['key'])
                if key in subscription:
                    cursor.execute("""DELETE FROM user_keywords
                    WHERE id_keyword=(SELECT id FROM keywords WHERE word=?)
                    AND id_user=(SELECT id FROM users WHERE id_tg=?)""", (key, chat_id))
                    connect.commit()
                    answer=f'Вы больше не подписаны на ключевое слово {key}  '
                else:
                    answer = f'У вас нет подписки на ключевое слово {key}  '
            return {'answer':answer}
        except sq.Error:
            print('ошибка подключения к базе при работе с ключевыми словами')
        finally:
            connect.close()
    if request.method == 'GET':
        return {'ok': True}

@app.route('/news', methods=['GET', 'POST'])
def news():
    text='wow!'
    if request.method == 'POST':
        chat_id = int(request.json['id'])
        try:
            connect = sq.connect('db_bot.db')
            cursor = connect.cursor()
            # получить список категорий
            info = cursor.execute("""SELECT category
            		FROM categories
            		JOIN user_category ON categories.id=id_category
            		JOIN users ON users.id=id_user
            		WHERE users.id_tg=?""", (chat_id,)).fetchall()

            news = []

            # список новостей по категориям
            for k in info:
                a = requests.get(f'https://newsapi.org/v2/top-headlines?apiKey={ap_key}&category={k[0]}&pageSize=10')
                for i in a.json()['articles']:
                    news.append([k[0], i['title'], i['publishedAt'], i['url']])

            # получить список ключевых слов
            info = cursor.execute("""SELECT word
            			FROM keywords
            			JOIN user_keywords ON keywords.id=id_keyword
            			JOIN users ON users.id=id_user
            			WHERE id_tg=?""", (chat_id,)).fetchall()

            # получить список новостей по ключевым словам
            for k in info:
                a = requests.get(f'https://newsapi.org/v2/top-headlines?apiKey={ap_key}&pageSize=10&q={k[0]}')
                for i in a.json()['articles']:
                    news.append([k[0], i['title'], i['publishedAt'], i['url']])

            # отсортировать весь список по дате
            news.sort(key=lambda x: x[2], reverse=True)

            # вывести 10 первых новостей
            text = dict()
            for i in range(10):
                text[f'{news[i][1]}']=news[i][3]
            return text
        except sq.Error:
            print('ошибка подключения к базе при работе с новостями')
        finally:
            connect.close()
            return text
    if request.method=='GET':
        return {'ok': True}


if __name__ == '__main__':
    try:
        connect = sq.connect('db_bot.db')
        cursor = connect.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS "categories" (
    	"id"	INTEGER NOT NULL,
    	"category"	TEXT NOT NULL,
    	PRIMARY KEY("id" AUTOINCREMENT)
    	);""")
        connect.commit()

        info = cursor.execute("""SELECT category FROM categories""").fetchall()
        category_in_base = []
        for j in info:
            category_in_base.append(j[0])
        for i in category_list:
            if i not in category_in_base:
                cursor.execute('INSERT INTO categories (category) VALUES (?)', (i,))
                connect.commit()

        cursor.execute("""CREATE TABLE IF NOT EXISTS "keywords" (
    	"id"	INTEGER NOT NULL,
    	"word"	TEXT NOT NULL,
    	PRIMARY KEY("id" AUTOINCREMENT)
    	);""")
        connect.commit()

        cursor.execute(
            """CREATE TABLE IF NOT EXISTS "users" (
        "id"	INTEGER NOT NULL,
        "id_tg"	INTEGER NOT NULL UNIQUE,
        PRIMARY KEY("id" AUTOINCREMENT)
        );""")
        connect.commit()

        cursor.execute("""CREATE TABLE IF NOT EXISTS "user_category" (
    	"id_user"	INTEGER NOT NULL,
    	"id_category"	INTEGER NOT NULL
    	);""")
        connect.commit()

        cursor.execute('''CREATE TABLE IF NOT EXISTS "user_keywords" (
    	"id_user"	INTEGER NOT NULL,
    	"id_keyword"	INTEGER NOT NULL
    	);''')
        connect.commit()
        print('база благополучно открыта')

    except sq.Error:
        print('ошибка подключения к базе на старте')
    finally:
        connect.close()
        app.run()

