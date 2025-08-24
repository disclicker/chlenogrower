import telebot
import sqlite3
import random
import time
from datetime import datetime, timedelta, timezone
from telebot import types
bot = telebot.TeleBot('8148784990:AAGmEo1JlkOk_LzwP8kWSehb4036UDHcPQQ')
moscow = timezone(timedelta(hours=3), "Moscow")
random.seed(int(time.time()*1000))
superbet = 0

@bot.message_handler(commands=['start'])
def start(message):
    conn = sqlite3.connect('data.sql')
    cur = conn.cursor()
    cur.close()
    conn.close()
    conn = sqlite3.connect('data.sql')
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS users (id int primary key, name varchar(50), length int, last_grown varchar(50), loses int, wins int, losestreak int, winstreak int, cur_losestreak int, cur_winstreak int, record_length int, top_position int)')
    conn.commit()
    cur.close()
    conn.close()
    if not if_exists(message.from_user.id):
        bot.send_message(message.chat.id, f'{message.from_user.first_name}, игра началась')
        register_user(message.from_user.id, message.from_user.first_name)
    

@bot.message_handler(commands=['number_of_users'])
def number_of_users(message):
    conn = sqlite3.connect('data.sql')
    cur = conn.cursor()
    cur.execute('SELECT * FROM users')
    answer = cur.fetchall()
    bot.send_message(message.chat.id, f'текущее количество пользователей: {len(answer)}')
    cur.close()
    conn.close()


@bot.message_handler(commands=['pvp'])
def start_fight(message):
    global superbet
    st = message.text.strip()
    if not if_exists(message.from_user.id):
        register_user(message.from_user.id, message.from_user.first_name)
    
    if len(st) == 4:
        bot.send_message(message.chat.id, "После /pvp напиши длину ставки")
    else:
        bet = st[4:].strip()
        if bet.isdigit() or bet == 'all':
            if bet == 'all':
                fin = get_length(message.from_user.id)
            else:
                fin = int(bet)
            if fin == 0:
                bot.reply_to(message, "Ваша ставка 0 см, такую не принимаем чтобы не засирать чат")
                return
            ln = get_length(message.from_user.id)
            superbet = fin
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton('Атаковать!', callback_data=message.from_user.id))
            if ln == fin:
                bot.reply_to(message, f'{message.from_user.first_name} пошел ва-банк со ставкой {fin} см!!!', reply_markup=markup)
            elif ln < fin:
                bot.reply_to(message, f'{message.from_user.first_name}, писюн коротковат :3')
            else:
                bot.reply_to(message, f'{message.from_user.first_name} бросил вызов чату со ставкой {fin} см', reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "После /pvp напиши длину ставки целым положительным числом или  /pvp all если хочешь поставить всю письку")
        

@bot.callback_query_handler(func=lambda callback: True)
def fight(callback):
    if not if_exists(callback.from_user.id):
        register_user(callback.from_user.id, callback.from_user.first_name)
    
    pupa = int(callback.data)
    lupa = int(callback.from_user.id)

    if pupa == lupa:
        return
    bet = superbet
    lenlup = get_length(lupa)
    lenpup = get_length(pupa)
    if lenpup < bet:
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text=f'{get_name(pupa)}, че-то ты разбежался своей третей ногой')
        return
    if lenlup < bet:
        bot.send_message(callback.message.chat.id, f'{callback.from_user.first_name}, не твой уровень дорогой')
        return
    win = get_winner(pupa, lupa)
    if win == pupa:
        winner = pupa
        loser = lupa
    else:
        winner = lupa
        loser = pupa
    add_cur_winstreak(winner)
    add_cur_losestreak(loser)
    add_wins(winner)
    add_loses(loser)
    set_length(winner, get_length(winner) + bet)
    set_length(loser, get_length(loser) - bet)
    update_record_length(winner)
    bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text=f'Победил {get_name(winner)}! Его текущая длина {get_length(winner)} см. Бедолага {get_name(loser)} проиграл и вынужден ходить со стручком длиной {get_length(loser)} см...\n Текущий винстрик победителя: {get_cur_winstreak(winner)}, лузстрик проигравшего: {get_cur_losestreak(loser)}')
    update_top_positions()                                      


@bot.message_handler(commands=['top'])
def show_top(message):
    conn = sqlite3.connect('data.sql')
    cur = conn.cursor()
    cur.execute('SELECT name, length, record_length FROM users ORDER BY length DESC')
    res = cur.fetchall()
    info = 'Топ всех удавов:\n\n'
    place = 1
    for name, length, record_length in res:
        info += f'{place}) {name} — <b>{length}</b>,  <i>рекорд: {record_length}</i>\n'
        place += 1
    cur.close()
    conn.close()
    bot.send_message(message.chat.id, info, parse_mode='HTML')

@bot.message_handler(commands=['show_id'])
def show_all_ids(message):
    conn = sqlite3.connect('data.sql')
    cur = conn.cursor()
    cur.execute('SELECT name, id FROM users ORDER BY length DESC')
    res = cur.fetchall()
    info = 'ID участников:\n\n'
    place = 1
    for name, id in res:
        info += f'{place}) {name} — {id}\n'
        place += 1
    cur.close()
    conn.close()
    bot.send_message(message.chat.id, info)

@bot.message_handler(commands=['set_secretly_very'])
def add_length_chosen(message):
    tx = message.text.strip()
    user_id = int(tx[18:].strip())
    bot.register_next_step_handler(message, getcm, user_id)
    update_top_positions()
    update_record_length(message.from_user.id)

def getcm(message, user_id):
    lng = int(message.text.strip())
    set_length(user_id, lng)

@bot.message_handler(commands=['grow'])
def grow_meat(message):
    if not if_exists(message.from_user.id):
        register_user(message.from_user.id, message.from_user.first_name)
    tm = datetime.now(moscow)
    day = str(tm.date().year)+'.'+str(tm.date().month)+'.'+str(tm.date().day)
    if day == get_last_grown(message.from_user.id):
        bot.reply_to(message, f"Ты уже растил пиписю сегодня, следующая попытка через {23 - tm.hour} ч. {59 - tm.minute} мин")
        return
    pls = (random.randint(0, 10000000000) % 20) - 5
    if get_length(message.from_user.id) + pls <= 0:
        pls = 1
    set_length(message.from_user.id, get_length(message.from_user.id) + pls)
    set_last_grown(message.from_user.id, day)
    if pls >= 0:
        bot.send_message(message.chat.id, f"Пипирик {message.from_user.first_name} увеличился на {pls} см, теперь его длина составляет {get_length(message.from_user.id)} см")
    else:
        bot.send_message(message.chat.id, f"Пипирик {message.from_user.first_name} скукожился на {-pls} см, теперь его длина составляет {get_length(message.from_user.id)} см")
    update_top_positions()
    update_record_length(message.from_user.id)
        

@bot.message_handler(commands=['stats'])
def show_statistics(message):
    if not if_exists(message.from_user.id):
        register_user(message.from_user.id, message.from_user.first_name)
    id = message.from_user.id
    winperc = 0
    ws = get_wins(id)
    ls = get_loses(id)
    if ws + ls != 0:
        winperc = round((ws / (ws + ls) * 100), 2)
    bot.reply_to(message, f'Длина: {get_length(id)}\nРекордная длина: {get_record_length(id)}\nПозиция в топе: {get_top_position(id)}\n\nКолличество побед: {ws}\nКолличество поражений: {ls}\nПроцент побед: {winperc}%\nМаксимальный винстрик: {get_winstreak(id)}\nМаксимальный лузстрик {get_losestreak(id)}')

@bot.message_handler(commands=['help'])
def help_user(message):
    bot.reply_to(message, "Иди нахуй")


def if_exists(user_id):
    conn = sqlite3.connect('data.sql')
    cur = conn.cursor()
    cur.execute(f'SELECT length FROM users WHERE id = {user_id}')
    if cur.fetchall():
        return True
    return False

def get_top_position(user_id):
    conn = sqlite3.connect('data.sql')
    cur = conn.cursor()
    cur.execute(f'SELECT top_position FROM users WHERE id = {user_id}')
    top_position = int(cur.fetchone()[0])
    cur.close()
    conn.close()
    return top_position

def get_length(user_id):
    conn = sqlite3.connect('data.sql')
    cur = conn.cursor()
    cur.execute(f'SELECT length FROM users WHERE id = {user_id}')
    length = int(cur.fetchone()[0])
    cur.close()
    conn.close()
    return length

def get_name(user_id):
    conn = sqlite3.connect('data.sql')
    cur = conn.cursor()
    cur.execute(f'SELECT name FROM users WHERE id = {user_id}')
    name = str(cur.fetchone()[0])
    cur.close()
    conn.close()
    return name

def get_last_grown(user_id):
    conn = sqlite3.connect('data.sql')
    cur = conn.cursor()
    cur.execute(f'SELECT last_grown FROM users WHERE id = {user_id}')
    last_grown = str(cur.fetchone()[0])
    cur.close()
    conn.close()
    return last_grown

def get_winstreak(user_id):
    conn = sqlite3.connect('data.sql')
    cur = conn.cursor()
    cur.execute(f'SELECT winstreak FROM users WHERE id = {user_id}')
    winstreak = int(cur.fetchone()[0])
    cur.close()
    conn.close()
    return winstreak

def get_cur_winstreak(user_id):
    conn = sqlite3.connect('data.sql')
    cur = conn.cursor()
    cur.execute(f'SELECT cur_winstreak FROM users WHERE id = {user_id}')
    cur_winstreak = int(cur.fetchone()[0])
    cur.close()
    conn.close()
    return cur_winstreak

def get_winstreak(user_id):
    conn = sqlite3.connect('data.sql')
    cur = conn.cursor()
    cur.execute(f'SELECT winstreak FROM users WHERE id = {user_id}')
    winstreak = int(cur.fetchone()[0])
    cur.close()
    conn.close()
    return winstreak

def get_cur_losestreak(user_id):
    conn = sqlite3.connect('data.sql')
    cur = conn.cursor()
    cur.execute(f'SELECT cur_losestreak FROM users WHERE id = {user_id}')
    cur_losestreak = int(cur.fetchone()[0])
    cur.close()
    conn.close()
    return cur_losestreak

def get_losestreak(user_id):
    conn = sqlite3.connect('data.sql')
    cur = conn.cursor()
    cur.execute(f'SELECT losestreak FROM users WHERE id = {user_id}')
    losestreak = int(cur.fetchone()[0])
    cur.close()
    conn.close()
    return losestreak

def get_record_length(user_id):
    conn = sqlite3.connect('data.sql')
    cur = conn.cursor()
    cur.execute(f'SELECT record_length FROM users WHERE id = {user_id}')
    record_length = int(cur.fetchone()[0])
    cur.close()
    conn.close()
    return record_length

def get_wins(user_id):
    conn = sqlite3.connect('data.sql')
    cur = conn.cursor()
    cur.execute(f'SELECT wins FROM users WHERE id = {user_id}')
    wins = int(cur.fetchone()[0])
    cur.close()
    conn.close()
    return wins

def get_loses(user_id):
    conn = sqlite3.connect('data.sql')
    cur = conn.cursor()
    cur.execute(f'SELECT loses FROM users WHERE id = {user_id}')
    loses = int(cur.fetchone()[0])
    cur.close()
    conn.close()
    return loses

def add_wins(user_id):
    conn = sqlite3.connect('data.sql')
    cur = conn.cursor()
    cur.execute(f'UPDATE users SET wins = wins + 1 WHERE id = {user_id}')
    conn.commit()
    cur.close()
    conn.close()

def add_loses(user_id):
    conn = sqlite3.connect('data.sql')
    cur = conn.cursor()
    cur.execute(f'UPDATE users SET loses = loses + 1 WHERE id = {user_id}')
    conn.commit()
    cur.close()
    conn.close()

def set_length(user_id, val):
    conn = sqlite3.connect('data.sql')
    cur = conn.cursor()
    cur.execute(f'UPDATE users SET length = {val} WHERE id = {user_id}')
    conn.commit()
    cur.close()
    conn.close()

def set_last_grown(user_id, val):
    conn = sqlite3.connect('data.sql')
    cur = conn.cursor()
    cur.execute(f'UPDATE users SET last_grown = "{val}" WHERE id = {user_id}')
    conn.commit()
    cur.close()
    conn.close()

def set_top_position(user_id, val):
    conn = sqlite3.connect('data.sql')
    cur = conn.cursor()
    cur.execute(f'UPDATE users SET top_position = {val} WHERE id = {user_id}')
    conn.commit()
    cur.close()
    conn.close()

def set_winstreak(user_id, val):
    conn = sqlite3.connect('data.sql')
    cur = conn.cursor()
    cur.execute(f'UPDATE users SET winstreak = {val} WHERE id = {user_id}')
    conn.commit()
    cur.close()
    conn.close()

def set_losestreak(user_id, val):
    conn = sqlite3.connect('data.sql')
    cur = conn.cursor()
    cur.execute(f'UPDATE users SET losestreak = {val} WHERE id = {user_id}')
    conn.commit()
    cur.close()
    conn.close()

def register_user(user_id, user_name):
    conn = sqlite3.connect('data.sql')
    cur = conn.cursor()
    cur.execute(f'INSERT INTO users (id, name, length, last_grown, loses, wins, losestreak, winstreak, cur_losestreak, cur_winstreak, record_length, top_position) VALUES ("{user_id}", "{user_name}", 0, -1, 0, 0, 0, 0, 0, 0, 0, -1) ON CONFLICT (id) DO NOTHING;')
    conn.commit()
    cur.close()
    conn.close()

def update_top_positions():
    conn = sqlite3.connect('data.sql')
    cur = conn.cursor()
    cur.execute('SELECT id FROM users ORDER BY length DESC')
    res = cur.fetchall()
    cur.close()
    conn.close()
    place = 1
    for i in res:
        set_top_position(int(i[0]), place)
        place += 1

def add_cur_winstreak(user_id):
    conn = sqlite3.connect('data.sql')
    cur = conn.cursor()
    cur.execute(f'UPDATE users SET cur_winstreak = cur_winstreak + 1 WHERE id = {user_id}')
    conn.commit()
    cur.execute(f'UPDATE users SET cur_losestreak = 0 WHERE id = {user_id}')
    conn.commit()
    cur.close()
    conn.close()
    set_winstreak(user_id, max(get_winstreak(user_id), get_cur_winstreak(user_id)))

def add_cur_losestreak(user_id):
    conn = sqlite3.connect('data.sql')
    cur = conn.cursor()
    cur.execute(f'UPDATE users SET cur_losestreak = cur_losestreak + 1 WHERE id = {user_id}')
    conn.commit()
    cur.execute(f'UPDATE users SET cur_winstreak = 0 WHERE id = {user_id}')
    conn.commit()
    cur.close()
    conn.close()
    set_losestreak(user_id, max(get_losestreak(user_id), get_cur_losestreak(user_id)))

def update_record_length(user_id):
    conn = sqlite3.connect('data.sql')
    cur = conn.cursor()
    cur.execute(f'UPDATE users SET record_length = {max(get_length(user_id), get_record_length(user_id))} WHERE id = {user_id}')
    conn.commit()
    cur.close()
    conn.close()

def get_winner(user_id1, user_id2):
    place1 = get_top_position(user_id1)
    place2 = get_top_position(user_id2)
    mn1 = place1 * 0.035 + 1.245
    mn2 = place2 * 0.035 + 1.245
    num1 = (random.randint(0, 10000000000) % 10000) * mn1
    num2 = (random.randint(0, 10000000000) % 10000) * mn2
    if num1 > num2:
        return user_id1
    return user_id2

bot.polling(none_stop=True)
