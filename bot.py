# Example of sending and receiving an event after pressing the Callback button
# Documentation: https://vk.cc/aC9JG2

import logging
import os

from vkbottle import Callback, GroupEventType, GroupTypes, Keyboard, Text, KeyboardButtonColor, DocMessagesUploader, \
    PhotoMessageUploader, AudioUploader
from vkbottle.bot import Bot, Message
from vkbottle.modules import json
from vkbottle_types import BaseStateGroup

from config import TOKEN, url

from requests import get

bot = Bot(TOKEN)
logging.basicConfig(level=logging.INFO)

user_words = dict()


class UserState(BaseStateGroup):
    UNKNOWN = 1


MAIN_KEYBOARD = Keyboard(one_time=True, inline=False)
MAIN_KEYBOARD.add(Text("Начать тренировку"), color=KeyboardButtonColor.PRIMARY)
MAIN_KEYBOARD = MAIN_KEYBOARD.get_json()

NEXT_KEYBOARD = Keyboard(inline=False)
NEXT_KEYBOARD.add(Text("Следующее слово"), color=KeyboardButtonColor.PRIMARY)
NEXT_KEYBOARD = NEXT_KEYBOARD.get_json()


# @bot.on.private_message(text="/callback")
# async def send_callback_button(message: Message):
#    await message.answer("Лови!", keyboard=KEYBOARD)


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, dataclass=GroupTypes.MessageEvent)
async def handle_message_event(event: GroupTypes.MessageEvent):
    # event_data parameter accepts three object types
    # "show_snackbar" type

    await bot.api.messages.send_message_event_answer(
        event_id=event.object.event_id,
        user_id=event.object.user_id,
        peer_id=event.object.peer_id,
        event_data=json.dumps({"type": "show_snackbar", "text": "Сейчас я исчезну"}),
    )


@bot.on.private_message(text="Начать")
async def start_message(message: Message):
    if 'user' not in get(f'http://{url}/api/v1/user/{message.peer_id}').json():
        await message.answer('''Привет!
Кажется, ты не зарегистрирован на сайте под этим аккаунтом
Ссылка на сайт: https://{url}''')
        await bot.state_dispenser.set(message.peer_id, UserState.UNKNOWN)
    else:
        await message.answer('Привет!', keyboard=MAIN_KEYBOARD)


@bot.on.private_message(text="Следующее слово")
async def next_word_message(message: Message):
    word = get(f'http://{url}/api/v1/vocabulary/{message.peer_id}').json()
    answers = set(word['incorrect_words'])
    answers.add(word["word"]["word"])
    user_words[message.peer_id] = {'correct': word["word"]["word"], 'incorrect': set(word['incorrect_words']), 'full_word': word}
    print(answers)
    answer_keyboard = Keyboard(one_time=True, inline=False)
    for answer in answers:
        answer_keyboard.add(Text(answer))
        # answer_keyboard.row()
    print(answer_keyboard.get_json())
    photo_url = word['word']["image"]
    photo_stream = get(photo_url).content
    photo = await PhotoMessageUploader(bot.api).upload(
        photo_stream, peer_id=message.peer_id
    )
    print(word)
    await message.answer(f'''Выбери слово, подходящее к картинке''',
                         keyboard=answer_keyboard.get_json(), attachment=photo)
    await bot.state_dispenser.set(message.peer_id, UserState.UNKNOWN)


@bot.on.private_message()
async def next_word_message(message: Message):
    if message.text in user_words[message.peer_id]['correct']:
        word = user_words[message.peer_id]['full_word']
        photo_url = word['word']["image"]
        photo_stream = get(photo_url).content
        photo = await PhotoMessageUploader(bot.api).upload(
            photo_stream, peer_id=message.peer_id
        )
        print(word)
        await message.answer(
            f'''Верно!
{word["word"]["emoji"]}{word["word"]["word"].capitalize()} — {word["word"]["translation"]}

{word['word']["dictionary"][0]['meanings'][0]['definitions'][0]['definition']}''',
            keyboard=NEXT_KEYBOARD, attachment=photo)
        await bot.state_dispenser.set(message.peer_id, UserState.UNKNOWN)
    else:
        word = user_words[message.peer_id]['full_word']
        photo_url = word['word']["image"]
        photo_stream = get(photo_url).content
        photo = await PhotoMessageUploader(bot.api).upload(
            photo_stream, peer_id=message.peer_id
        )
        print(word)
        await message.answer(
            f'''Не совсем!
        {word["word"]["emoji"]}{word["word"]["word"].capitalize()} — {word["word"]["translation"]}

        {word['word']["dictionary"][0]['meanings'][0]['definitions'][0]['definition']}''',
            keyboard=NEXT_KEYBOARD, attachment=photo)
        await bot.state_dispenser.set(message.peer_id, UserState.UNKNOWN)
    if message.text == 'Дальше':
        word = get(f'http://{url}/api/v1/vocabulary/{message.peer_id}').json()
        photo_url = word['word']["image"]
        photo_stream = get(photo_url).content
        photo = await PhotoMessageUploader(bot.api).upload(
            photo_stream, peer_id=message.peer_id
        )
        print(word)
        await message.answer(f'''{word["word"]["emoji"]}{word["word"]["word"].capitalize()} — {word["word"]["translation"]}
    
{word['word']["dictionary"][0]['meanings'][0]['definitions'][0]['definition']}''',
                             keyboard=NEXT_KEYBOARD, attachment=photo)
        await bot.state_dispenser.set(message.peer_id, UserState.UNKNOWN)



#
# @bot.on.private_message(text="Следующее слово")
# async def next_word_message(message: Message):
#     word = get(f'http://{url}/api/v1/vocabulary/{message.peer_id}').json()
#     photo_url = word['word']["image"]
#     photo_stream = get(photo_url).content
#     photo = await PhotoMessageUploader(bot.api).upload(
#         photo_stream, peer_id=message.peer_id
#     )
#     print(word)
#     await message.answer(f'''{word["word"]["emoji"]}{word["word"]["word"].capitalize()} — {word["word"]["translation"]}
#
# {word['word']["dictionary"][0]['meanings'][0]['definitions'][0]['definition']}''',
#                          keyboard=NEXT_KEYBOARD, attachment=photo)
#     await bot.state_dispenser.set(message.peer_id, UserState.UNKNOWN)


bot.run_forever()
