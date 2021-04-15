import telebot
import sqlite3 as sq
import newsapi
bot = telebot.TeleBot("1796482318:AAGijFv_OgK7xLPGGJnkQGJygsM-IYMnQZg", parse_mode=None)

try:
	conn = sq.connect('db_bot.db')
	cursor = conn.cursor()

	cursor.execute("""CREATE TABLE IF NOT EXISTS "categories" (
	"id"	INTEGER NOT NULL UNIQUE,
	"category"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
);""")
	conn.commit()

	cursor.execute("""CREATE TABLE IF NOT EXISTS "keywords" (
	"id"	INTEGER NOT NULL UNIQUE,
	"word"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
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
	"id_category"	INTEGER NOT NULL,
	FOREIGN KEY("id_category") REFERENCES "categories"("id"),
	FOREIGN KEY("id_user") REFERENCES "users"("id")
	);""")
	conn.commit()

	cursor.execute('''CREATE TABLE IF NOT EXISTS "user_keywords" (
	"id_user"	INTEGER NOT NULL,
	"id_word"	INTEGER NOT NULL,
	FOREIGN KEY("id_user") REFERENCES "users"("id"),
	FOREIGN KEY("id_word") REFERENCES "keywords"("id")
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
										   'добавить категорию - /add_cat\n'
										   'удалить категорию - /delete_cat\n'
										   'просмотр ключевых слов - /view_key\n'
										   'добавить ключевое слово - /add_key\n'
										   'удалить ключевое слово - /delete_key\n'
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
								JOIN user_category ON categories.id=user_category.id_category
								JOIN users ON users.id=user_category.id_user
								WHERE users.id=?""", (x,)).fetchall()
		if len(info) == 0:
			bot.send_message(message.from_user.id, 'Вы пока ни на какие категории не подписаны')
		else:
			answer=''
			for i in range(len(info)):
				answer += f'{i}'
				if i!=len(info):
					answer+=', '
			bot.send_message(message.from_user.id, f'Вы подписаны на следующие категории: {answer}')
	except sq.Error:
		bot.send_message(message.from_user.id,'Ошибка подключения к базе, не могу просмотреть подписки')
	finally:
		conn.close()

@bot.message_handler(commands=['add_cat'])
def handle_add_category(message):
	bot.send_message(message.from_user.id, 'Хотите добавить новую категорию? Не вопрос')
	try:
		conn = sq.connect('db_bot.db')
		cursor = conn.cursor()
		x=int(message.from_user.id)
		if len(message.text.split()) <=1:
			bot.send_message(message.from_user.id, 'Беда! Вы не указали категорию. Введите команду в формате /add_cat название_категории')
		else:
			cat = message.text.lower().split()[1]
			#проверить на что подписан пользователь
			info1 = cursor.execute("""SELECT categories.category
										FROM categories
										JOIN user_category ON categories.id=user_category.id_category
										JOIN users ON users.id=user_category.id_user
										WHERE users.id=?""", (x,)).fetchall()
			print (info1)
			# и проверить, какие категории уже в базе есть
			info2=cursor.execute("""SELECT categories.category
										FROM categories
										WHERE categories.category=?""", (cat,)).fetchall()
			print (info2)
			if cat in info1 and cat in info2:
				bot.send_message(message.from_user.id, 'Вы уже подписаны на эту категорию')
			elif cat in info2:
				cursor.execute("""INSERT INTO user_category (id_user, id_category) VALUES (?, ?)""", (x,cat))
				conn.commit()
				bot.send_message(message.from_user.id, f'Ура! Подписка на категорию {cat} добавлена')
			else:
				cursor.execute("""INSERT INTO categories (category) VALUES (?)""", (cat,))
				conn.commit()
				cursor.execute("""INSERT INTO user_category (id_user, id_category) VALUES (?, ?)""", (x, cat))
				conn.commit()
				bot.send_message(message.from_user.id, f'Ура! Подписка на категорию {cat} добавлена')
	except sq.Error:
		bot.send_message(message.from_user.id,'Ошибка подключения к базе, не могу просмотреть добавить категорию')
	finally:
		conn.close()

@bot.message_handler(commands=['delete_cat'])
def handle_delete_category(message):
	bot.send_message(message.from_user.id, 'Зачем же удалять категорию?')

@bot.message_handler(commands=['view_key'])
def handle_view_keywords(message):
	try:
		conn = sq.connect('db_bot.db')
		cursor = conn.cursor()
		x = int(message.from_user.id)
		info = cursor.execute("""SELECT keywords.word
								FROM keywords
								JOIN user_keywords ON keywords.id=user_keywords.id_word
								JOIN users ON users.id=user_keywords.id_user
								WHERE users.id=?""", (x,)).fetchall()
		if len(info) == 0:
			bot.send_message(message.from_user.id, 'Для вас не указаны ключевые слова')
		else:
			answer = ''
			for i in range(len(info)):
				answer += f'{i}'
				if i != len(info):
					answer += ', '
			bot.send_message(message.from_user.id, f'Вас интересуют следующие ключевые слова: {answer}')
	except sq.Error:
		bot.send_message(message.from_user.id, 'Ошибка подключения к базе, не могу просмотреть ключевые слова')
	finally:
		conn.close()

@bot.message_handler(commands=['add_key'])
def handle_add_keyword(message):
	bot.send_message(message.from_user.id, 'Добавляем новые ключевые слова')

@bot.message_handler(commands=['delete_key'])
def handle_delete_keyword(message):
	bot.send_message(message.from_user.id, 'Ну давайте удалим ключевые слов')

@bot.message_handler(commands=['news'])
def handle_view_news(message):
	bot.send_message(message.from_user.id, 'Получите свои новости!')




bot.polling()
