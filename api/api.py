from fastapi import FastAPI
import mysql.connector
from mysql.connector import errorcode
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Union

config = {
    'host':'127.0.0.1',
    'user':'root',
    'password':'12345',
    'database':'taxi'
}


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5000",  # Django dev server
        "http://localhost:5000",   # на всякий случай
    ],
    allow_credentials=True,
    allow_methods=["*"],  # или укажите конкретно: ["GET", "POST", ...]
    allow_headers=["*"],  # или укажите нужные заголовки
)

@app.get("/")
async def root():
	"""
	Возвращает данные об активных заказах
	"""
	all_orders = {}
	try:
		conn = mysql.connector.connect(**config)
		print("Get data about active orders") # Switch to logging
		cursor = conn.cursor()
		cursor.execute("SELECT * FROM orders where ord_status = 0")
		for row in cursor.fetchall():
			all_orders[row[0]] = row
		conn.close()
	except mysql.connector.Error as err:
		return {"error": err}
	
	return {"result": all_orders}

@app.get("/user_balance/{uuid}")
async def user_balance(uuid):
	"""
	Возвращает баланс пользователя
	"""
	try:
		conn = mysql.connector.connect(**config)
		print(f"Calculating balance for user {uuid}") # Switch to logging
		cursor = conn.cursor()
		balance_q = "SELECT balance FROM users where uuid = %s"
		cursor.execute(balance_q, (uuid,))
		balance = cursor.fetchone()
		conn.close()
	except mysql.connector.Error as err:
		return {"error": err}
	return balance

@app.get("/check_street/{street}/{num}")
async def check_street(street, num):
	"""
	Проверяет существует ли указанный адрес в БД, возвращает булево
	"""
	try:
		conn = mysql.connector.connect(**config)
		print(f"Checking street {street}") # Switch to logging
		cursor = conn.cursor()
		street_q1 = f"SELECT * FROM streets where title = %s"
		cursor.execute(street_q1, (street,))
		row = cursor.fetchall()
		conn.close()
		if row and int(num) <= int(row[0][4]):
			return True, row[0][0]
		else:
			return False, 0
	except mysql.connector.Error as err:
		return {"error": err}

@app.post("/create_order")
async def create_order(data: List[Union[str, int]]):
	"""
	Добавляет новый заказ, возвращает статус и метаданные
	"""
    #data = [user_id, source, qty, result_val, street_pos, timestamp]
	print(data)
	conn = mysql.connector.connect(**config)
	cursor = conn.cursor()
	create_order_q = ("INSERT INTO orders "
					"(uuid, ord_from_s, ord_from_n, ord_to_s, ord_to_n, dtcreate) "
					"VALUES (%s, %s, %s, %s, %s, %s)")
	cursor.execute(create_order_q, (data[0], data[1], data[2], data[3], data[4], data[5],))
	conn.commit()
	conn.close()
	return {
        "status": "ok",
        "user_id": data[0],
        "timestamp": data[5]
    }

		
	#except:
	#	pass
