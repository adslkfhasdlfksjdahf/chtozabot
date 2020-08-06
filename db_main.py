from peewee import *
from datetime import datetime
from playhouse.signals import Model, pre_save, pre_init
from pathlib import Path

from config import database_name

db = SqliteDatabase(database_name, pragmas={'foreign_keys': 1, 'ignore_check_constraints': 0})
db.connect()


class BaseModel(Model):
    class Meta:
        database = db

class UserWallet(BaseModel):
    tg_id = IntegerField()
    balance = FloatField(default=0)
    wallet_addr = TextField(default='')
    wallet_key = TextField(default='')
    

    class Meta:
        table_name = 'user_wallet'

class UserBallance(BaseModel):
    tg_id = IntegerField()
    balance = FloatField(default=0)

    class Meta:
        table_name = 'user_ballance'


class UserBet(BaseModel):
    tg_id = IntegerField()
    bet_summ = FloatField(default=0)
    second_time = BooleanField(default=False)
    bet_target= IntegerField(default=0)

    class Meta:
        table_name = 'user_bet'

def db_connect():
    db.connect(reuse_if_open=True)
    return

def db_disconnect():
    db.close()
    return

# первичная инициализация БД
def init_tables():
    #with db:
    #my_file = Path(database_name)
    #if (not my_file.is_file()):
    db.create_tables([UserWallet, UserBallance, UserBet])
    return

# проверить, существует ли юзер
def user_exists(tg_id, id_is_wallet = False):
    if(id_is_wallet == True):
        query = UserWallet.select().where(UserWallet.wallet_addr == tg_id)
    else:
        query = UserWallet.select().where(UserWallet.tg_id == int(tg_id))

    if query.exists():
        return True
    else:
        return False

# изменить юзера
def update_user(tg_id, upd_c):
    user = UserWallet.select().where(UserWallet.tg_id == tg_id).get()
    for key in upd_c:
        value = upd_c[key]
        setattr(user, key, value)
    user.save()

# создать юзера
def add_new_user(newuser):
    UserWallet.create(
        balance=newuser['balance'], 
        tg_id=newuser['tg_id'], 
        wallet_addr=str(newuser['wallet_addr']), 
        wallet_key=str(newuser['wallet_key'])
    )
    UserBallance.create(
        balance=newuser['balance'], 
        tg_id=newuser['tg_id']
    )    
    return True

# удалить юзера
def delete_user(tg_id):
    user = UserWallet.get(UserWallet.tg_id == tg_id)
    return user.delete_instance()

# вытащить всех юзеров
def get_users():
    users = []
    for user in UserWallet.select().where(1):
        users.append(user)
    return users

# вытащить юзера по телеграмИД
def get_user(tg_id, return_object = True):
    uw = UserWallet.select().where(UserWallet.tg_id == tg_id).get()
    if return_object:
        return uw
    else:
        return {'balance': uw.balance, 'tg_id': uw.tg_id, 'wallet_addr': uw.wallet_addr, 'wallet_key': uw.wallet_key}

# получить колво юзеров
def get_users_count():
    gc=0
    for grp in UserWallet.select().where(1):
        gc+=1
    return gc

# новая ставка
def add_new_bet(newbet):
    UserBet.create(
        tg_id=newbet['tg_id'], 
        bet_summ=newbet['bet_summ'], 
        second_time=newbet['second_time'],
        bet_target=newbet['bet_target']
    )
    return True

# обнуляем ставки. параметр указывает какую половину часа обнулить
def clear_bets(second_time = False):
    bets = UserBet.select().where(UserBet.second_time == second_time)
    for bet in bets:
        bet.bet_summ=0
        bet.save()
    return

# удаляем ставки. параметр указывает какую половину часа удалить
def delete_bets(second_time = False):
    bets = UserBet.select().where(UserBet.second_time == second_time)
    for bet in bets:
        bet.delete_instance()
    return


# вытащить ставки
def get_bet(bet_target, second_time = False, bet_target_is_tg_id = False):
    if(bet_target_is_tg_id==True):
        uw = UserBet.select().where((UserBet.second_time == second_time) & (UserBet.tg_id == bet_target)).get()
    else:
        uw = UserBet.select().where((UserBet.second_time == second_time) & (UserBet.bet_target == bet_target))
    #if return_object:
    return uw
    #else:
    #    return {'bet_summ': uw.bet_sum, 'tg_id': uw.tg_id, 'second_time': uw.second_time, 'bet_target': uw.bet_target}

def update_bet(tg_id, upd_c):
    user_bet = UserBet.select().where(UserBet.tg_id == tg_id).get()
    for key in upd_c:
        value = upd_c[key]
        setattr(user_bet, key, value)
    user_bet.save()

# изменить баланс юзера
def update_user_ballance(tg_id, upd_c):
    user_ballance = UserBallance.select().where(UserBallance.tg_id == tg_id).get()
    for key in upd_c:
        value = upd_c[key]
        setattr(user_ballance, key, value)
    user_ballance.save()
    
# вытащить юзер валлет по телеграмИД
def get_user_ballance(tg_id, return_object = True):
    uw = UserBallance.select().where(UserBallance.tg_id == tg_id).get()
    if return_object:
        return uw
    else:
        return {'balance': uw.balance, 'tg_id': uw.tg_id}
    