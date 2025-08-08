import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram import F

import os

TOKEN = os.getenv('8337898993:AAGlATM17_cUZxY_vLxYMJE2dO2pFdx_ngg')
bot = Bot(token=TOKEN)
dp = Dispatcher()

waiting = []
pairs = {}
active_timers = {}

CHAT_DURATION = 300  # 5 минут в секундах


async def end_chat(user1, user2):
    pairs.pop(user1, None)
    pairs.pop(user2, None)
    active_timers.pop(user1, None)
    active_timers.pop(user2, None)
    try:
        await bot.send_message(user1, "⏰ Время чата закончилось. Для нового собеседника напиши /start")
    except:
        pass
    try:
        await bot.send_message(user2, "⏰ Время чата закончилось. Для нового собеседника напиши /start")
    except:
        pass
    if user1 not in waiting:
        waiting.append(user1)
    if user2 not in waiting:
        waiting.append(user2)
    await try_match()


async def start_timer(user1, user2):
    await asyncio.sleep(CHAT_DURATION)
    if pairs.get(user1) == user2 and pairs.get(user2) == user1:
        await end_chat(user1, user2)


async def try_match():
    while len(waiting) >= 2:
        user1 = waiting.pop(0)
        user2 = waiting.pop(0)
        pairs[user1] = user2
        pairs[user2] = user1

        await bot.send_message(user1, "🤫 Партнёр найден! Чат анонимный. Пиши сюда. У вас есть 5 минут.")
        await bot.send_message(user2, "🤫 Партнёр найден! Чат анонимный. Пиши сюда. У вас есть 5 минут.")

        task = asyncio.create_task(start_timer(user1, user2))
        active_timers[user1] = task
        active_timers[user2] = task


@dp.message(Command("start"))
async def start_handler(message: Message):
    user_id = message.from_user.id
    if user_id in pairs:
        await message.answer("Ты уже в чате. Пиши собеседнику или останови чат командой /stop")
        return
    if user_id in waiting:
        await message.answer("Ты уже в очереди, жди собеседника.")
        return

    waiting.append(user_id)
    await message.answer("Ты в очереди, жди собеседника.")
    await try_match()


@dp.message(Command("stop"))
async def stop_handler(message: Message):
    user_id = message.from_user.id
    if user_id in pairs:
        partner_id = pairs.pop(user_id)
        pairs.pop(partner_id, None)

        task = active_timers.pop(user_id, None)
        if task:
            task.cancel()
        active_timers.pop(partner_id, None)

        await bot.send_message(user_id, "Чат завершён. Чтобы начать новый — /start")
        await bot.send_message(partner_id, "Чат завершён собеседником. Чтобы начать новый — /start")

        if partner_id not in waiting:
            waiting.append(partner_id)
            await try_match()
    else:
        if user_id in waiting:
            waiting.remove(user_id)
            await message.answer("Ты вышел из очереди.")
        else:
            await message.answer("Ты не в чате и не в очереди.")


@dp.message(F.text)
async def relay_message(message: Message):
    user_id = message.from_user.id
    if user_id in pairs:
        partner_id = pairs[user_id]
        text = message.text
        if not text:
            return
        try:
            await bot.send_message(partner_id, f"👤 Собеседник: {text}")
        except:
            await end_chat(user_id, partner_id)
    else:
        await message.answer("Ты не в чате. Начни новый /start")


async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    print("Бот запущен. Нажми Ctrl+C для остановки.")
    import asyncio
    asyncio.run(main())
