import asyncio
import logging
import sys
import mysql.connector

from os import getenv
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, KeyboardButton, CallbackQuery, ReplyKeyboardMarkup, InlineKeyboardButton
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import os
from dotenv import load_dotenv
import requests

load_dotenv() 
TOKEN = os.getenv("TOKEN")


dp = Dispatcher()
router = Router()

# Определение состояний
class Form(StatesGroup):
	waiting_from = State()
	waiting_to = State()


# Стартовая клавиатура
def get_kb():
	builder = InlineKeyboardBuilder()
	builder.add(InlineKeyboardButton(text="Посмотреть баланс", callback_data="check_balance"))
	builder.add(InlineKeyboardButton(text="Сделать заказ", callback_data="make_order"))
	return builder.as_markup()

# Клавиатура для создания заказа
def get_kb_order():
	builder = InlineKeyboardBuilder()
	builder.add(InlineKeyboardButton(text="Пункт отправления", callback_data="p_from"))
	builder.add(InlineKeyboardButton(text="<- Назад", callback_data="back"))
	return builder.as_markup()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
	"""
	Приветствие и создание клавиатуры для начальной навигации
	"""
	await message.answer(f"Привет! Вот меню для управления:",reply_markup=get_kb())



@router.callback_query(F.data.in_(["check_balance", "make_order"]))
async def callback_handler_main(callback: CallbackQuery):
	"""
	Обработка нажатия в первом меню
	
	:param callback: Description
	:type callback: CallbackQuery
	"""
	if callback.data == "check_balance":
		uuid = callback.from_user.id
		get_balance = requests.get(f"http://127.0.0.1:8000/user_balance/{uuid}")
		balance = get_balance.json()_
		await callback.message.answer(f"Ваш баланс: {balance} рублей")
	elif callback.data == "make_order":
		await callback.message.answer("Заполните следующие данные:", reply_markup = get_kb_order())
	await callback.answer()


@router.callback_query(F.data.in_(["p_from", "back"]))
async def callback_handler_order(callback: CallbackQuery, state: FSMContext):
	"""
	Обработка заказа 
	
	:param callback: Description
	:type callback: CallbackQuery
	:param state: Description
	:type state: FSMContext
	"""
	if callback.data == "p_from":
		await callback.message.answer("Данные вводятся в формате Улица, номер\nОткуда:")
		await state.set_state(Form.waiting_from)
	elif callback.data == "back":
		await callback.message.answer("Привет! Вот меню для управления:",reply_markup=get_kb())

	await callback.answer()

@router.message(Form.waiting_from)
async def process_name(message: types.Message, state: FSMContext):
	"""
	Обработка места посадки и сохранение в FSM
	
	:param message: Description
	:type message: types.Message
	:param state: Description
	:type state: FSMContext
	"""
	try:
		try:
			conv = message.text.split(',')
			street_name = conv[0]
			street_pos = conv[1]
			print(conv)
			if conv:
				check_if_exist = f"SELECT * FROM streets where title = '{street_name}'"
				cnx = mysql.connector.connect(user='root', password='12345', host='127.0.0.1', database='taxi')
				cursor = cnx.cursor()
				cursor.execute(check_if_exist)
				row = cursor.fetchall()
				print(row)
				if row and int(street_pos) <= int(row[0][4]):
					await state.update_data(waiting_from=[row[0][0], street_pos])
					await message.answer(f"Принято. Теперь введите куда направляетесь:")
					await state.set_state(Form.waiting_to)
					print('Sended to next hook')
				else:
					await message.answer("Такого адреса не существует, попробуйте снова:",reply_markup=get_kb_order())
		except:
			await message.answer("Указан неверный формат адреса, попробуйте снова:",reply_markup=get_kb_order())

	except Exception as e:
		print('Error:', e)


@router.message(Form.waiting_to)
async def process_age(message: types.Message, state: FSMContext):
	"""
	Обработка места высадки и сохранение в FSM/MySQL
	
	:param message: Description
	:type message: types.Message
	:param state: Description
	:type state: FSMContext
	"""
	try:
		try:
			conv = message.text.split(',')
			street_name = conv[0]
			street_pos = conv[1]
			print('bwabwaaa')
			if conv:
				check_if_exist = f"SELECT * FROM streets where title = '{street_name}'"
				cnx = mysql.connector.connect(user='root', password='12345', host='127.0.0.1', database='taxi')
				cursor = cnx.cursor()
				cursor.execute(check_if_exist)
				row = cursor.fetchall()
				if row:
					if int(street_pos) <= int(row[0][4]):
						await state.update_data(waiting_to=[row[0][0], street_pos])
						user_data = await state.get_data()
						print(f'bwa {user_data}')
						now = datetime.now()
						order_data = (str(message.from_user.id), user_data["waiting_from"][0], int(user_data["waiting_from"][1]),int(row[0][0]), int(street_pos), now.strftime('%Y-%m-%d %H:%M:%S'))
						create_order = ("INSERT INTO orders "
								"(uuid, ord_from_s, ord_from_n, ord_to_s, ord_to_n, dtcreate) "
								"VALUES (%s, %s, %s, %s, %s, %s)")


						cnx = mysql.connector.connect(user='root', password='12345', host='127.0.0.1', database='taxi')
						cursor = cnx.cursor()
						cursor.execute(create_order, order_data)
						cnx.commit()
						cursor.close()
						cnx.close()

						await message.answer(f"Заказ создан!\nНачинаем поиск водителя...")
						await state.clear() # Сброс состояний 
		except:
			await message.answer("Указан неверный формат адреса, попробуйте снова:",reply_markup=get_kb_order())

	except Exception as e:
		print('Error:', e)

async def main() -> None:
	"""
	Инициализация бота и всех его компонентов
	"""
	bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
	dp.include_router(router)
	await dp.start_polling(bot)


if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO, stream=sys.stdout)
	asyncio.run(main())
