# - *- coding: utf- 8 - *-
import telebot
#multiprocess:
import multiprocessing
import os
#import threading
import time
import datetime
import sqlite3
import requests
# подключаем модуль работы с БД
from db_main import *
import requests
import json
from telebot import types
from config import token, database_name, SFHH, EFHH, SSHH, ESHH, FHCM, SHCM, MOB
from secrets import token_bytes
from coincurve import PublicKey
from sha3 import keccak_256

bot = telebot.TeleBot(token)
# первоначальная инициализация БД
init_tables()
global EthToken
EthToken = "7UQF8ZIRHENNVS6F3YKDRXPD1SF5AMHURD"
global pricestart
pricestart = 100
print(pricestart)
global betx
betx = 1.5
upordownitog = 0
global finishprice1
global finishprice2
finishprice1 = 0
finishprice2 = 0
global winwinbet1
global winwinbet2
winwinbet1 = 0
winwinbet2 = 0
global pricestart1
global pricestart2
pricestart1 = 0
pricestart2 = 0

#####################################
manager = multiprocessing.Manager()
# Define a list (queue) for tasks and computation results
tasks = manager.Queue()
results = manager.Queue()
pool = multiprocessing.Pool(processes=3)
processes = []

def is_first_half_hour():
    mint = datetime.now().minute
    if(mint>=SFHH and mint<=EFHH):
        return True
    elif(mint>=SSHH and mint<=ESHH):
        return False


def background():  # фоновый def для парсинга курса eth в usd
    global pricestart
    global pricestart1
    global pricestart2
    global finishprice1
    global finishprice2
    pid = 'PID:'+ str(os.getpid())+' :: '
    print(pid+'Starting background()')
    while True:
        nowglaw = datetime.now().minute
        if nowglaw == 0 or nowglaw == 30:
            r = requests.get(
                'https://www.coingecko.com/price_charts/279/usd/24_hours.json').json()
            pricestart = r['stats'][-1][1]  # цена eth в usd
            if nowglaw == 0:
                pricestart1 = pricestart
                finishprice2 = pricestart


            if nowglaw == 30:
                pricestart2 = pricestart
                finishprice1 = pricestart

        #print(pid+str(pricestart))
        #print(pid+str(pricestart1))
        #print(pid+str(pricestart2))
        #print(pid+str(finishprice1))
        #print(pid+str(finishprice2))

        time.sleep(2)


def dapezda():  # фоновый def для парсинга курса eth в usd
    global pricestart
    global finishprice1
    global finishprice2
    global winwinbet1
    global winwinbet2
    global pricestart1
    global pricestart2
    d = 0
    b = 0
    pid = 'PID:'+ str(os.getpid())+' :: '
    print(pid+'Starting dapezda()')
    while True:
        nowglaw = datetime.now().minute
        if nowglaw == 1:
            b = 0
            if d <= 0:
                if finishprice2 >= pricestart2:
                    winwinbet2 = 1

                elif finishprice2 <= pricestart2:
                    winwinbet2 = 0

        if nowglaw == 31:
            d = 0
            if b <= 0:
                if finishprice1 >= pricestart1:
                    winwinbet1 = 1

                elif finishprice1 <= pricestart1:
                    winwinbet1 = 0



        time.sleep(2)


def background_process_bets():
    global winwinbet1
    global winwinbet2
    global betx
    
    mint = datetime.now().minute
    pid = 'PID:'+ str(os.getpid())+' :: '
    print(pid+'Starting background_process_bets()')
    
    if(mint==FHCM or mint==SHCM):
        print(pid+'Starting process bets....')    
        if is_first_half_hour():
            #первая половина часа обрабатывается тут:
            winbets = get_bet(winwinbet1)
        else:
            #вторая половина часа обрабатывается тут:
            winbets = get_bet(winwinbet2, True)


        print(pid+' Found bets:')
        print(winbets)
        
        for bet in winbets:
            win = get_user_ballance(bet.tg_id) + bet.bet_summ * betx
            print(pid+' User '+str(bet.tg_id)+' has winned '+str(win))
            update_user(bet.tg_id, {'balance': win})
            delete_bets(is_first_half_hour())
    time.sleep(60)

#pezdaaa = threading.Thread(name='dapezda', target=dapezda())
#pezdaaa.start()
#1
new_process = multiprocessing.Process(
    target=background
)
processes.append(new_process)
new_process.start()
#2
new_process = multiprocessing.Process(
    target=dapezda
)
#3 Clear Bets:
new_process = multiprocessing.Process(
    target=background_process_bets
)
processes.append(new_process)
new_process.start()

map(lambda new_process: new_process.join(), processes)


def check_stavka():

    mint = datetime.now().minute
    if(mint>=SFHH and mint<=EFHH):
        return 1
    elif(mint>=SSHH and mint<=ESHH):
        return 2
    else:
        return 0

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    print(user_id)
    if (not user_exists(user_id)):
        private_key = keccak_256(token_bytes(32)).digest()
        public_key = PublicKey.from_valid_secret(private_key).format(compressed=False)[1:]
        addr = keccak_256(public_key).digest()[-20:]
        addr = addr.hex()
        print('private_key:', private_key.hex())
        print('eth addr:', '0x' + addr)

        # create new user with wallet
        newuserdata = {'balance': 0, 'tg_id': user_id, 'wallet_addr': '0x' + str(addr),
                       'wallet_key': '' + str(private_key.hex())}
        add_new_user(newuserdata)
    
    bot.send_message(message.chat.id, "Это тотализатор BetEther для p2p ставок на курс Ethereum \n\nℹ️ Подробнее о том, как играть: \nhttps://graph.org/Instrukciya-kak-stavit-08-02", reply_markup=menu_keyboard, disable_web_page_preview=True)
    bot.register_next_step_handler(message, menu)


@bot.message_handler(content_types=['text'])
def menu(message):
    if message.text == "💰 Кошелёк ETH":
        bal_ = 0
        if(user_exists(message.from_user.id)):
            bal_ = get_user(message.from_user.id).balance
        bot.send_message(message.from_user.id, f"ETH кошелек тут должен выводиться баланс, который равен {bal_}", reply_markup=balance, disable_web_page_preview=True)
        bot.register_next_step_handler(message, menu)

    if message.text == "🎲 Betting":
        bot.send_message(message.from_user.id,
                         "Тут вы можете осуществлять ставки на курс ETH\n\nПодробнее: https://graph.org/Instrukciya-kak-stavit-08-02",
                         reply_markup=betiti, disable_web_page_preview=True)
        bot.register_next_step_handler(message, menu)

    if message.text == "🚀 О сервисе":
        bot.send_message(message.from_user.id, "Это тотализатор Bitoto для p2p ставок на курс Bitcoin\n\nℹ️ Подробнее о том, как играть в тотализатор: bitoto.io/instruction\n\nСайт проекта: bitoto.io", reply_markup=servese, disable_web_page_preview=True)
        bot.register_next_step_handler(message, menu)
    if message.text == "🤝 Партнёрам":
        bot.send_message(message.from_user.id, "💵 Партнерская программа 🤝\n\nПриглашай новых пользователей в двухуровневую реферальную программу и получай пассивный доход от комиссий тотализатора! 💵\n\n🔥 Зарабатывай до 7% от суммы выигрыша твоих рефералов!!!\n\n1 уровень: 5%\n2 уровень: 2%\n\n📌 Пример: Ты пригласил партнера, который выиграл 1 ETH, ты получишь выплату в  0.05 ETH Если твой партнер пригласит еще партнеров, то с каждого из них - ты будешь получать еще 2%\n\nВыходит, что если твой партнер и его партнер выиграют каждый по 1 ETH, то ты получишь - 0.07 ETH на свой баланс.", disable_web_page_preview=True)
        bot.register_next_step_handler(message, menu)


@bot.message_handler(content_types=['text'])
def upstavkaa(message):
    cs = check_stavka()
    if message.text == "🔙 Назад":
        bot.send_message(message.from_user.id, "Отмена", reply_markup=menu_keyboard)
        bot.register_next_step_handler(message, menu)
    elif cs == 0:
        bot.send_message(message.from_user.id, "Игра закрыта", reply_markup=menu_keyboard)
        bot.register_next_step_handler(message, menu)    
    else:
        user_id = message.from_user.id
        print(user_id)
        txtvopr = float(message.text)
        print(txtvopr)
        print('upstavkaa CS:', cs)
        
        if txtvopr>get_user_ballance(user_id).balance:
            bot.send_message(message.from_user.id, "У вас недостаточно денег на балансе", reply_markup=menu_keyboard)
            bot.register_next_step_handler(message, menu)
        
        else:
            # сохраняем ставку
            if cs == 1:
                second_time = False
            elif cs == 2:
                second_time = True
                
            betdata = {'tg_id': user_id, 'bet_summ': (txtvopr), 'second_time': second_time, 'bet_target': 1}
            print(betdata)
            add_new_bet(betdata)
            update_user_ballance(user_id, {'balance': get_user_ballance(user_id).balance - txtvopr})
            
            bot.send_message(message.from_user.id, f"Вы сделали ставку Выше на сумму {txtvopr} ETH", reply_markup=menu_keyboard)
            bot.register_next_step_handler(message, menu)


@bot.message_handler(content_types=['text'])
def outstavkaa(message):
    cs = check_stavka()
    if message.text == "🔙 Назад":
        bot.send_message(message.from_user.id, "Отмена", reply_markup=menu_keyboard)
        bot.register_next_step_handler(message, menu)
    elif cs == 0:
        bot.send_message(message.from_user.id, "Игра закрыта", reply_markup=menu_keyboard)
        bot.register_next_step_handler(message, menu)    
    else:
        user_id = message.from_user.id
        print(user_id)
        txtvopr = float(message.text)
        print(txtvopr)
        print('outstavka CS:', cs)
        
        if txtvopr>get_user_ballance(user_id).balance:
            bot.send_message(message.from_user.id, "У вас недостаточно денег на балансе", reply_markup=menu_keyboard)
            bot.register_next_step_handler(message, menu)
        
        else:
            # сохраняем ставку
            if cs == 1:
                second_time = False
            elif cs == 2:
                second_time = True
                
            betdata = {'tg_id': user_id, 'bet_summ': (txtvopr), 'second_time': second_time, 'bet_target': 0}
            print(betdata)
            add_new_bet(betdata)
            update_user_ballance(user_id, {'balance': get_user_ballance(user_id).balance - txtvopr})
            
            bot.send_message(message.from_user.id, f"Вы сделали ставку Выше на сумму {txtvopr} ETH", reply_markup=menu_keyboard)
            bot.register_next_step_handler(message, menu)

@bot.message_handler(content_types=['text'])
def inputoutsumm():
    if message.text == "🔙 Назад":
        bot.send_message(message.from_user.id, "Отмена", reply_markup=menu_keyboard)
        bot.register_next_step_handler(message, menu)
    else:
        user_id = message.from_user.id
        print(user_id)
        txtvopr = float(message.text)
        print(txtvopr)
        
        update_out(user_id, {'out_summ': txtvopr})
        bot.send_message(message.from_user.id, f"Вы хотите вывести {txtvopr} ETH\nВведите адрес кошелька для вывода", reply_markup=menu_keyboard)
        bot.register_next_step_handler(message, inputoutaddr)

@bot.message_handler(content_types=['text'])
def inputoutaddr():
    if message.text == "🔙 Назад":
        bot.send_message(message.from_user.id, "Отмена", reply_markup=menu_keyboard)
        bot.register_next_step_handler(message, menu)
    else:
        user_id = message.from_user.id
        print(user_id)
        txtvopr = message.text
        print(txtvopr)
        
        update_out(user_id, {'wallet_addr': txtvopr})
        bot.send_message(message.from_user.id, f"Адрес для вывода: {txtvopr} ETH\nОжидайте вывода!", reply_markup=menu_keyboard)
        bot.register_next_step_handler(message, menu)
        
@bot.callback_query_handler(func=lambda call: True)
def callback_processing(call):
    global walletn
    global wallet
    global EthToken

    if call.data == "refreshbal":
        telegram_user_id = call.from_user.id
        bal_ = 1
        bot.answer_callback_query(call.id)
        usr = get_user(call.from_user.id, False)
        addr = usr['wallet_addr']
        response = requests.get(f"https://api.etherscan.io/api?module=account&action=balance&address={addr}&tag=latest&apikey={EthToken}")
        balnowwal = int(response.json()["result"]) / 1000000000000000000
        #берет нынешний баланс адреса эфириум

        usr = get_user(call.from_user.id, False)
        baloldwal = usr['balance']
        #берет старый баланс адреса из бд user_wallet

        razbal = balnowwal - baloldwal
        #находит разницу балансов(новго от старого)

        wallet = get_user_ballance(call.from_user.id, False)
        oldbalhum = wallet['balance']
        #берет старый баланс человека из бд user_ballance
        
        newbalhum = oldbalhum + razbal
        #суммирует разницу балансов адресов и нынешний баланс и получает новый баланс

        update_user(call.from_user.id, {'balance': balnowwal})
        #записывает нынешний баланс адреса в бд user_wallet

        update_user_ballance(telegram_user_id, {'balance': newbalhum})
        #записывает новый баланс юзера в бд user_ballance

        wallet = get_user_ballance(call.from_user.id, False)
        bal_ = wallet['balance']


        message = bot.send_message(call.from_user.id, f"Ваш баланс: {bal_}")

    if call.data == "upst":
        bot.answer_callback_query(call.id)
        message = bot.send_message(call.from_user.id, f"Какую сумму ты хочешь поставить на повышение?",
                                   reply_markup=back_keyboard)
        bot.register_next_step_handler(message, upstavkaa)

    if call.data == "outst":
        bot.answer_callback_query(call.id)
        message = bot.send_message(call.from_user.id, f"Какую сумму ты хочешь поставить на понижение?",
                                   reply_markup=back_keyboard)
        bot.register_next_step_handler(message, outstavkaa)
    if call.data == "out-money":
        user = get_user(call.from_user.id)
        if(user.balance <= MOB):
            bot.send_message(call.from_user.id, f"Не достаточно денег на балансе. Минимальная сумма для вывода {MOB}", reply_markup=back_keyboard)
        else:
            message = bot.send_message(call.from_user.id, f"Какую сумму ты хочешь вывести?",
                                       reply_markup=back_keyboard)
            bot.register_next_step_handler(message, inputoutsumm)        
    if call.data == "in-money":
        # check if user exsist or not
        if(not user_exists(call.from_user.id)):
            private_key = keccak_256(token_bytes(32)).digest()
            public_key = PublicKey.from_valid_secret(private_key).format(compressed=False)[1:]
            addr = keccak_256(public_key).digest()[-20:]            
            addr = addr.hex()
            print('private_key:', private_key.hex())
            print('eth addr:', '0x'+addr )            
            
            #create new user with wallet
            newuserdata = {'balance':0, 'tg_id': call.from_user.id, 'wallet_addr': '0x'+ str(addr), 'wallet_key': ''+ str(private_key.hex())}
            add_new_user(newuserdata)
            
        else:
            usr = get_user(call.from_user.id, False)
            private_key = usr['wallet_key']
            addr = usr['wallet_addr']
            print('private_key:', private_key)
            print('eth addr:', addr)
            
        bot.answer_callback_query(call.id)
        bot.send_message(call.from_user.id, f"Вот твой ETH адрес для пополнения:")
        bot.send_message(call.from_user.id, f"{addr}",reply_markup=refreshbaba)

    if call.data == "igra":
        nowm = datetime.now().minute
        if 0 <= nowm <= 10 or 30 <= nowm <= 40:
            bot.answer_callback_query(call.id)
            bot.send_message(call.from_user.id, "Доступные интервалы на данный момент:", reply_markup=interv)
        else:
            bot.answer_callback_query(call.id)
            ost = 2
            if 40 <= nowm <= 60:
                ost = 60 - nowm - 1
            if 10 <= nowm <= 30:
                ost = 30 - nowm - 1
            bot.send_message(call.from_user.id,
                             f"😔 На данный момент нет доступных интервалов\n\nДо начала розыгрыша осталось {ost} минут")
    if call.data == "30min":
        r = requests.get(
                'https://www.coingecko.com/price_charts/279/usd/24_hours.json').json()
        priceprice = r['stats'][-1][1]  # цена eth в usd
        nowm = datetime.now().minute
        bot.answer_callback_query(call.id)
        if 30 <= nowm <= 59:
            ost2 = 60 - nowm
        if 0 <= nowm <= 29:
            ost2 = 30 - nowm
        textvopr = get_user(call.from_user.id)
        print(textvopr)
        bot.send_message(call.from_user.id,
                     f"💥🎰 30 минутный интервал\n\nУ тебя есть время чтобы сделать ставку что курс ETH будет выше или ниже чем {pricestart}$ через {ost2} минуты\n\nПоставили Выше: 0.0000 ETH\n\nПоставили Ниже: 0.0000 ETH\n\nETH будет выше или ниже чем {pricestart}$ через {ost2} минуты по паре Binance ETH/USDT ?\n\nАктуальный курс Binance: {priceprice}$",
                     reply_markup=stavka)

    elif call.data == "my-igra":
        bot.answer_callback_query(call.id)
        textvopr = get_user(call.from_user.id)
        print(textvopr)
        bot.send_message(call.from_user.id,
                         "🚀 Тут ты можешь посмотреть информацию о розыгрышах, в которых ты принимаешь участие прямо сейчас\n\nНа данный момент ты не принимаешь участие ни в одном розыгрыше")
    #elif call.data == "out-money":
    #    message = bot.send_message(call.from_user.id, "Напиши адрес внешнего ETH кошелька")
    #    bot.register_next_step_handler(message, outoutmoney)


@bot.message_handler(content_types=['text'])
def outoutmoney(message):
    message = bot.send_message(message.from_user.id, "Ожидайте перевода", reply_markup=menu_keyboard)
    bot.register_next_step_handler(message, menu)



refreshbaba = types.InlineKeyboardMarkup(row_width=1)

refreshbaba.add(types.InlineKeyboardButton('Обновить баланс', callback_data="refreshbal"))


balance = types.InlineKeyboardMarkup(row_width=2)

balance.add(types.InlineKeyboardButton('📥 Внести', callback_data="in-money"),
            types.InlineKeyboardButton('📤 Вывести', callback_data="out-money"),
            types.InlineKeyboardButton('Обновить баланс', callback_data="refreshbal"))

servese = types.InlineKeyboardMarkup(row_width=2)

servese.add(types.InlineKeyboardButton('☕ Чат', url='https://t.me/EthBet_chat'),
            types.InlineKeyboardButton('🛠 Поддержка', url='https://t.me/EthBet_Support'),
            types.InlineKeyboardButton('📮 Новости', url='https://t.me/News_EthBet'),
            types.InlineKeyboardButton('📋 FAQ', url='https://graph.org/Instrukciya-kak-stavit-08-02'))

betiti = types.InlineKeyboardMarkup(row_width=2)

betiti.add(types.InlineKeyboardButton('🎰 Розыгрыши', callback_data="igra"),
           types.InlineKeyboardButton('🎮 Мои ставки', callback_data="my-igra"),
           types.InlineKeyboardButton('🔕 Отключить рассылку', callback_data="off-talk"))

menu_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
menu_keyboard.add(types.KeyboardButton("💰 Кошелёк ETH"), types.KeyboardButton("🎲 Betting"),
                  types.KeyboardButton("🚀 О сервисе"), types.KeyboardButton("🤝 Партнёрам"))

yesno = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
yesno.add(types.KeyboardButton("Да"), types.KeyboardButton("Нет"))

interv = types.InlineKeyboardMarkup(row_width=2)

interv.add(types.InlineKeyboardButton('⌛ 30 минутный интервал', callback_data="30min"))

stavka = types.InlineKeyboardMarkup(row_width=2)

stavka.add(types.InlineKeyboardButton('📈 Выше', callback_data="upst"),
           types.InlineKeyboardButton('📉 Ниже', callback_data="outst"),
           types.InlineKeyboardButton('🔃 Обновить данные', callback_data="30min"))

back_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
back_keyboard.add(types.KeyboardButton("🔙 Назад"))

bot.infinity_polling(True)