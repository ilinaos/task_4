import telebot
import sqlite3 as sq
import newsapi
bot = telebot.TeleBot("1796482318:AAGijFv_OgK7xLPGGJnkQGJygsM-IYMnQZg", parse_mode=None)

try:
	conn = sq.connect('db_bot.db')
	cursor = conn.cursor()

	cursor.execute("""CREATE TABLE IF NOT EXISTS "categories" (
	"category"	TEXT NOT NULL UNIQUE,
	PRIMARY KEY("category")
);""")
	conn.commit()

	cursor.execute("""CREATE TABLE IF NOT EXISTS "keywords" (
	"word"	TEXT NOT NULL UNIQUE,
	PRIMARY KEY("word")
	);""")
	conn.commit()

	cursor.execute(
		"""CREATE TABLE IF NOT EXISTS "users" (
	"id"	INTEGER NOT NULL UNIQUE,
	"name"	TEXT,
	PRIMARY KEY("id")
);""")
	conn.commit()

	cursor.execute("""CREATE TABLE IF NOT EXISTS "user_category" (
	"id_user"	INTEGER NOT NULL,
	"id_category"	TEXT NOT NULL
	);""")
	conn.commit()

	cursor.execute('''CREATE TABLE IF NOT EXISTS "user_keywords" (
	"id_user"	INTEGER NOT NULL,
	"id_word"	TEXT NOT NULL
	);''')
	conn.commit()
	print ('база благополучно открыта')

except sq.Error:
    print ('ошибка подключения к базе')
finally:
    conn.close()

@bot.message_handler(commands=['start', 'help'])
def handle_start_help(message):
	bot.send_message(message.from_user.id, 'Привет! Я могу предложить новости. Доступные команды:\n'
										   'регистрация - /register\n'
										   'просмотр категорий - /view_cat\n'
										   'добавить категорию - /add_cat название\n'
										   'удалить категорию - /delete_cat название\n'
										   'просмотр ключевых слов - /view_key\n'
										   'добавить ключевое слово - /add_key название\n'
										   'удалить ключевое слово - /delete_key название\n'
										   'просмотреть последние новости - /news')

@bot.message_handler(commands=['register'])
def handle_register(message):
	try:
		conn = sq.connect('db_bot.db')
		cursor = conn.cursor()
		x=message.from_user.id
		name=message.chat.username
		# print (f'{message.from_user.id} - {message.chat.username}')
		info = cursor.execute("SELECT * FROM users WHERE id=?", (int(x),)).fetchall()
		# print(info)
		if len(info)==0:
			bot.send_message(message.from_user.id, 'Вас в таблице нет')
			cursor.execute("INSERT INTO users (id, name) VALUES (?, ?)", (x,name))
			conn.commit()
			bot.send_message(message.from_user.id, f'wow, новый пользователь #{name}')
		else:
			bot.send_message(message.from_user.id, 'Вы уже зарегистрированы!')
	except sq.Error:
		bot.send_message(message.from_user.id,'Ошибка подключения к базе, не могу зарегистрировать')
	finally:
		conn.close()

@bot.message_handler(commands=['view_cat'])
def handle_view_category(message):
	try:
		conn = sq.connect('db_bot.db')
		cursor = conn.cursor()
		x=int(message.from_user.id)
		info = cursor.execute("""SELECT categories.category
								FROM categories
								JOIN user_category ON categories.category=user_category.id_category
								JOIN users ON users.id=user_category.id_user
								WHERE users.id=?""", (x,)).fetchall()
		if len(info) == 0:
			bot.send_message(message.from_user.id, 'Вы пока ни на какие категории не подписаны')
		else:
			answer=''
			for i in info:
				answer+=str(i)[2:-3]+', '
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
		if len(message.text.split()) <=1:
			bot.send_message(message.from_user.id, 'Беда! Вы не указали категорию. Введите команду в формате /add_cat название_категории')
		else:
			cat = message.text.lower().split()[1]
			# print(cat, len(cat))
			#проверить на что подписан пользователь
			info1 = cursor.execute("""SELECT categories.category
										FROM categories
										JOIN user_category ON categories.category=user_category.id_category
										JOIN users ON users.id=user_category.id_user
										WHERE users.id=?""", (x,)).fetchall()
			inf1=[]
			for i in info1:
				inf1.append(str(i)[2:-3])
			# и проверить, какие категории уже в базе есть
			info2 = cursor.execute("""SELECT category
										FROM categories""").fetchall()
			inf2=[]
			for i in info2:
				inf2.append(str(i)[2:-3])
			if cat in inf1 and cat in inf2:
				# print ('и там, и там')
				bot.send_message(message.from_user.id, 'Вы уже подписаны на эту категорию')
			elif cat in inf2:
				# print('в категориях, но не в подписках')
				cursor.execute("""INSERT INTO user_category (id_user, id_category) VALUES (?, ?)""", (x,cat))
				conn.commit()
				bot.send_message(message.from_user.id, f'Ура! Подписка на категорию {cat} добавлена')
			else:
				# print('нигде нет')
				cursor.execute("""INSERT INTO categories (category) VALUES (?)""", (cat,))
				conn.commit()
				cursor.execute("""INSERT INTO user_category (id_user, id_category) VALUES (?, ?)""", (x, cat))
				conn.commit()
				bot.send_message(message.from_user.id, f'Ура! Подписка на категорию {cat} добавлена')
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
			info1 = cursor.execute("""SELECT categories.category
											FROM categories
											JOIN user_category ON categories.category=user_category.id_category
											JOIN users ON users.id=user_category.id_user
											WHERE users.id=?""", (x,)).fetchall()
			inf1 = []
			for i in info1:
				inf1.append(str(i)[2:-3])
			if cat in inf1:
				cursor.execute("""DELETE FROM user_category WHERE id_category=? AND id_user=?""",(cat,x))
				conn.commit()
				bot.send_message(message.from_user.id, 'Вы больше не подписаны на эту категорию')
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
		info = cursor.execute("""SELECT keywords.word
								FROM keywords
								JOIN user_keywords ON keywords.word=user_keywords.id_word
								JOIN users ON users.id=user_keywords.id_user
								WHERE users.id=?""", (x,)).fetchall()
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
										JOIN user_keywords ON word=id_word
										JOIN users ON id=id_user
										WHERE users.id=?""", (x,)).fetchall()
			inf1=[]
			for i in info1:
				inf1.append(str(i)[2:-3])
			# и проверить, какие слова уже в базе есть
			info2 = cursor.execute("""SELECT word
										FROM keywords""").fetchall()
			inf2=[]
			for i in info2:
				inf2.append(str(i)[2:-3])
			if key in inf1 and key in inf2:
				bot.send_message(message.from_user.id, 'Вы уже подписаны на это ключевое слово')
			elif key in inf2:
				cursor.execute("""INSERT INTO user_keywords (id_user, id_word) VALUES (?, ?)""", (x,key))
				conn.commit()
				bot.send_message(message.from_user.id, f'Ура! Новое ключевое слово {key} добавлено')
			else:
				cursor.execute("""INSERT INTO keywords (word) VALUES (?)""", (key,))
				conn.commit()
				cursor.execute("""INSERT INTO user_keywords (id_user, id_word) VALUES (?, ?)""", (x, key))
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
			info1 = cursor.execute("""SELECT keywords.word
										FROM keywords
										JOIN user_keywords ON keywords.word=user_keywords.id_word
										JOIN users ON users.id=user_keywords.id_user
										WHERE users.id=?""", (x,)).fetchall()
			inf1 = []
			for i in info1:
				inf1.append(str(i)[2:-3])
			if key in inf1:
				cursor.execute("""DELETE FROM user_keywords WHERE id_word=? AND id_user=?""",(key,x))
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
	bot.send_message(message.from_user.id, 'Получите свои новости!')




bot.polling()
