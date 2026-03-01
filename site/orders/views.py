from django.shortcuts import render
from django.http import HttpResponse
import requests
# Create your views here.
def index(request):
	response = requests.get('http://127.0.0.1:8000/') # Данные по всем заказам
	# print(response.status_code)
	if response.status_code == 200:
		data = response.json()
		for key,value in data.items():
			print(value)
			
	return render(request, "orders/index.html", {"context": value})
