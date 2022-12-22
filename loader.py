from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage2

from secret import TOKEN

bot = Bot(token=TOKEN)

storage = RedisStorage2('localhost', 6379, db=5, pool_size=10, prefix='fbfarmBot')
dp = Dispatcher(bot, storage=storage)

