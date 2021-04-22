import telebot
import sqlite3 as sq
from newsapi import NewsApiClient
import requests
from config import ap_key, tg_key
bot = telebot.TeleBot(tg_key, parse_mode=None)
api = NewsApiClient(api_key=ap_key)

try:
	conn = sq.connect('db_bot.db')
	cursor = conn.cursor()

	cursor.execute("""CREATE TABLE IF NOT EXISTS "categories" (
	"id"	INTEGER NOT NULL,
	"category"	TEXT NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
	);""")
	conn.commit()

	info = cursor.execute("""SELECT category FROM categories""").fetchall()
	category_list=['business','entertainment',
	'general', 'health', 'science', 'sports', 'technology']
	category_in_base=[]
	for j in info:
		category_in_base.append(j[0])
	for i in category_list:
		if i not in category_in_base:
			cursor.execute('INSERT INTO categories (category) VALUES (?)', (i,))
			conn.commit()

	cursor.execute("""CREATE TABLE IF NOT EXISTS "keywords" (
	"id"	INTEGER NOT NULL,
	"word"	TEXT NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
	);""")
	conn.commit()

	cursor.execute(
		"""CREATE TABLE IF NOT EXISTS "users" (
	"id"	INTEGER NOT NULL,
	"id_tg"	INTEGER NOT NULL UNIQUE,
	PRIMARY KEY("id" AUTOINCREMENT)
	);""")
	conn.commit()

	cursor.execute("""CREATE TABLE IF NOT EXISTS "user_category" (
	"id_user"	INTEGER NOT NULL,
	"id_category"	INTEGER NOT NULL
	);""")
	conn.commit()

	cursor.execute('''CREATE TABLE IF NOT EXISTS "user_keywords" (
	"id_user"	INTEGER NOT NULL,
	"id_keyword"	INTEGER NOT NULL
	);''')
	conn.commit()
	print ('база благополучно открыта')

except sq.Error:
    print ('ошибка подключения к базе')
finally:
    conn.close()

@bot.message_handler(commands=['start', 'help'])
def handle_start_help(message):
	try:
		conn = sq.connect('db_bot.db')
		cursor = conn.cursor()
		x=int(message.from_user.id)
		info = cursor.execute("SELECT * FROM users WHERE id_tg=?", (x,)).fetchall()
		if len(info) == 0:
			cursor.execute("INSERT INTO users (id_tg) VALUES (?)", (x,))
			conn.commit()
			bot.send_message(message.from_user.id, f'Привет, {message.chat.username}')
	except sq.Error:
		bot.send_message(message.from_user.id,'Ошибка подключения к базе, не могу зарегистрировать')
	finally:
		conn.close()
		bot.send_message(message.from_user.id, 'Я могу предложить новости. Доступные команды:\n'
										   'просмотр категорий - /view_cat\n'
										   'добавить категорию - /add_cat название\n'
										   'удалить категорию - /delete_cat название\n'
										   'просмотр ключевых слов - /view_key\n'
										   'добавить ключевое слово - /add_key название\n'
										   'удалить ключевое слово - /delete_key название\n'
										   'просмотреть последние новости - /news')

@bot.message_handler(commands=['view_cat'])
def handle_view_category(message):
	try:
		conn = sq.connect('db_bot.db')
		cursor = conn.cursor()
		x=int(message.from_user.id)
		info = cursor.execute("""SELECT category
FROM categories
JOIN user_category ON categories.id=id_category
JOIN users ON users.id=id_user
WHERE users.id_tg=?""", (x,)).fetchall()
		if len(info) == 0:
			bot.send_message(message.from_user.id, 'Вы пока ни на какие категории не подписаны')
		else:
			answer=''
			for i in info:
				answer += i[0] + ', '
			bot.send_message(message.from_user.id, f'Вы подписаны на следующие категории: {answer[:-2]}')
	except sq.Error:
		bot.send_message(message.from_user.id,'Ошибка подключения к базе, не могу просмотреть подписки')
	finally:
		conn.close()

@bot.message_handler(commands=['add_cat'])
def handle_add_category(message):
	# bot.send_message(message.from_user.id, 'Хотите добавить новую категорию? Не вопрос')
	try:
		conn = sq.connect('db_bot.db')
		cursor = conn.cursor()
		x=int(message.from_user.id)
		info2 = cursor.execute("""SELECT category FROM categories""").fetchall()
		inf2 = []
		for i in info2:
			inf2.append(i[0])
		if len(message.text.split()) <=1:
			bot.send_message(message.from_user.id, f'''Беда! Вы не указали категорию. Введите команду в формате /add_cat название_категории.\n
			Доступные категории: {inf2}''')
		else:
			cat = message.text.lower().split()[1]
			#проверить на что подписан пользователь
			info1 = cursor.execute("""SELECT category
FROM categories
JOIN user_category ON categories.id=id_category
JOIN users ON users.id=id_user
WHERE users.id_tg=?""", (x,)).fetchall()
			inf1=[]
			for i in info1:
				inf1.append(i[0])
			print (inf1)


			if cat in inf1:
				# print ('и там, и там')
				bot.send_message(message.from_user.id, 'Вы уже подписаны на эту категорию')
			elif cat in inf2:
				# print('в категориях, но не в подписках')
				cursor.execute("""INSERT INTO user_category (id_user, id_category) VALUES 
				((SELECT id FROM users WHERE id_tg=?),
				(SELECT id FROM categories WHERE category=?))""", (x,cat))
				conn.commit()
				bot.send_message(message.from_user.id, f'Ура! Подписка на категорию {cat} добавлена')
			else:
				bot.send_message(message.from_user.id, f'На категорию {cat} подписаться нельзя')
	except sq.Error:
		bot.send_message(message.from_user.id,'Ошибка подключения к базе, не могу добавить категорию')
	finally:
		conn.close()

@bot.message_handler(commands=['delete_cat'])
def handle_delete_category(message):
	# bot.send_message(message.from_user.id, 'Зачем же удалять категорию?')
	try:
		conn = sq.connect('db_bot.db')
		cursor = conn.cursor()
		x=int(message.from_user.id)
		if len(message.text.split()) <=1:
			bot.send_message(message.from_user.id, 'Беда! Вы не указали категорию. Введите команду в формате /delete_cat название_категории')
		else:
			cat = message.text.lower().split()[1]
			# проверить на что подписан пользователь
			info1 = cursor.execute("""SELECT category
FROM categories
JOIN user_category ON categories.id=id_category
JOIN users ON users.id=id_user
WHERE users.id_tg=?""", (x,)).fetchall()
			inf1 = []
			for i in info1:
				inf1.append(str(i)[2:-3])
			if cat in inf1:
				cursor.execute("""DELETE FROM user_category 
WHERE id_user=(SELECT id FROM users WHERE id_tg=?) 
AND id_category=(SELECT id FROM categories WHERE category=?)""",(x,cat))
				conn.commit()
				bot.send_message(message.from_user.id, f'Вы больше не подписаны на категорию {cat}')
			else:
				bot.send_message(message.from_user.id, 'Вы не подписаны на эту категорию')
	except sq.Error:
		bot.send_message(message.from_user.id,'Ошибка подключения к базе, не могу удалить подписку на категорию')
	finally:
		conn.close()

@bot.message_handler(commands=['view_key'])
def handle_view_keywords(message):
	try:
		conn = sq.connect('db_bot.db')
		cursor = conn.cursor()
		x = int(message.from_user.id)
		info = cursor.execute("""SELECT word
FROM keywords
JOIN user_keywords ON keywords.id=id_keyword
JOIN users ON users.id=id_user
WHERE id_tg=?""", (x,)).fetchall()
		if len(info) == 0:
			bot.send_message(message.from_user.id, 'У вас пока нет ключевых слов')
		else:
			answer = ''
			for i in info:
				answer += str(i)[2:-3] + ', '
			bot.send_message(message.from_user.id, f'Вас интересуют следующие ключевые слова: {answer[:-2]}')
	except sq.Error:
		bot.send_message(message.from_user.id, 'Ошибка подключения к базе, не могу просмотреть ключевые слова')
	finally:
		conn.close()

@bot.message_handler(commands=['add_key'])
def handle_add_keyword(message):
	# bot.send_message(message.from_user.id, 'Добавляем новые ключевые слова')
	try:
		conn = sq.connect('db_bot.db')
		cursor = conn.cursor()
		x=int(message.from_user.id)
		if len(message.text.split()) <=1:
			bot.send_message(message.from_user.id, 'Беда! Вы не указали ключевое слово. Введите команду в формате /add_key ключевое_слово')
		else:
			key = message.text.lower().split()[1]
			#проверить на что подписан пользователь
			info1 = cursor.execute("""SELECT word
FROM keywords
JOIN user_keywords ON keywords.id=id_keyword
JOIN users ON users.id=id_user
WHERE id_tg=?""", (x,)).fetchall()
			inf1=[]
			for i in info1:
				inf1.append(str(i)[2:-3])
			# и проверить, какие слова уже в базе есть
			info2 = cursor.execute("""SELECT word
										FROM keywords""").fetchall()
			inf2=[]
			for i in info2:
				inf2.append(str(i)[2:-3])
			if key in inf1:
				bot.send_message(message.from_user.id, 'Вы уже подписаны на это ключевое слово')
			elif key in inf2:
				cursor.execute("""INSERT INTO user_keywords (id_user, id_keyword) VALUES
((SELECT id FROM users WHERE id_tg=?),
 (SELECT id FROM keywords WHERE word=?))""", (x,key))
				conn.commit()
				bot.send_message(message.from_user.id, f'Ура! Новое ключевое слово {key} добавлено')
			else:
				cursor.execute("""INSERT INTO keywords (word) VALUES (?)""", (key,))
				conn.commit()
				cursor.execute("""INSERT INTO user_keywords (id_user, id_keyword) VALUES
((SELECT id FROM users WHERE id_tg=?),
 (SELECT id FROM keywords WHERE word=?))""", (x, key))
				conn.commit()
				bot.send_message(message.from_user.id, f'Ура! Новое ключевое слово {key} добавлено')
	except sq.Error:
		bot.send_message(message.from_user.id,'Ошибка подключения к базе, не могу добавить ключевое слово')
	finally:
		conn.close()

@bot.message_handler(commands=['delete_key'])
def handle_delete_keyword(message):
	# bot.send_message(message.from_user.id, 'Ну давайте удалим ключевые слов')
	try:
		conn = sq.connect('db_bot.db')
		cursor = conn.cursor()
		x=int(message.from_user.id)
		if len(message.text.split()) <=1:
			bot.send_message(message.from_user.id, 'Беда! Вы не указали ключевое слово. Введите команду в формате /delete_key ключевое_слово')
		else:
			key = message.text.lower().split()[1]
			# проверить на что подписан пользователь
			info1 = cursor.execute("""SELECT word
FROM keywords
JOIN user_keywords ON keywords.id=id_keyword
JOIN users ON users.id=id_user
WHERE id_tg=?""", (x,)).fetchall()
			inf1 = []
			for i in info1:
				inf1.append(str(i)[2:-3])
			if key in inf1:
				cursor.execute("""DELETE FROM user_keywords 
WHERE id_keyword=(SELECT id FROM keywords WHERE word=?)
AND id_user=(SELECT id FROM users WHERE id_tg=?)""",(key,x))
				conn.commit()
				bot.send_message(message.from_user.id, 'Вы больше не подписаны на это ключевое слово')
			else:
				bot.send_message(message.from_user.id, 'Вы не подписаны на это ключевое слово')
	except sq.Error:
		bot.send_message(message.from_user.id,'Ошибка подключения к базе, не могу удалить подписку на ключевое слово')
	finally:
		conn.close()

@bot.message_handler(commands=['news'])
def handle_view_news(message):
	try:
		conn = sq.connect('db_bot.db')
		cursor = conn.cursor()
		#получить список категорий
		info = cursor.execute("""SELECT category
		FROM categories
		JOIN user_category ON categories.id=id_category
		JOIN users ON users.id=id_user
		WHERE users.id_tg=?""", (message.from_user.id,)).fetchall()

		news=[]

		#список новостей по категориям
		for k in info:
			a = requests.get(f'https://newsapi.org/v2/top-headlines?apiKey={ap_key}&category={k[0]}&pageSize=10')
			for i in a.json()['articles']:
				news.append([k[0], i['title'], i['publishedAt'], i['url']])

		#получить список ключевых слов
		info = cursor.execute("""SELECT word
			FROM keywords
			JOIN user_keywords ON keywords.id=id_keyword
			JOIN users ON users.id=id_user
			WHERE id_tg=?""", (message.from_user.id,)).fetchall()

		#получить список новостей по ключевым словам
		for k in info:
			a = requests.get(f'https://newsapi.org/v2/top-headlines?apiKey={ap_key}&pageSize=10&q={k[0]}')
			for i in a.json()['articles']:
				news.append([k[0], i['title'], i['publishedAt'], i['url']])

		#отсортировать весь список по дате
		news.sort(key=lambda x:x[2], reverse=True)

		#вывести 10 первых новостей
		text=''
		for i in range(10):
			text+=str(news[i][0])+'\n'+str(news[i][1])+'\n'+str(news[i][2])+'\n'+str(news[i][3])+'\n\n'
		bot.send_message(message.from_user.id, text)

	except sq.Error:
		bot.send_message(message.from_user.id,'Ошибка подключения к базе, не могу просмотреть подписки')
	finally:
		conn.close()

@bot.message_handler(func=lambda message: True)
def handle_another(message):
	bot.send_message(message.from_user.id, 'Хотелось бы поболтать, но я не умею =( Воспользуйтесь командой /help, чтобы узнать, что я могу')

bot.polling()
