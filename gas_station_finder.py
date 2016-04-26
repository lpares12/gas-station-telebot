# Remember to include the different encodings for the different languages

# Including necessary libraries
# telebot - to use the TelegramBot API
# urrlib2 - to connect to yandex (translator) and make requests
# json - to get the text of the responses
import telebot
import urllib2, urllib
import json
import ast
import time

# To avoid warnings in Python < 2.7.9. Not important!
import requests
requests.packages.urllib3.disable_warnings()

# Token of the telegram Bot
TOKEN_TELEGRAM = '130498184:AAFFJLIMxFV-UR8tlKbZeQi2wzU9Dckkr0w'
# Linking the Bot to this python script
bot = telebot.TeleBot(TOKEN_TELEGRAM)

# API Key of Google Maps API
KEY_PLACES = 'AIzaSyAgFyIkMlchQEzPyV3y6NR50MtZdfDvjic'

# Gas Station class to save all its info
class GasStation:
	def __init__(self, name, address, price, type, city):
		self.name = name
		self.address = address
		self.city = city
		self.price = price
		self.type = type # 0 for Cash 1 for Credit
	def getName(self):
		return self.name
	def getAddress(self):
		return self.address
	def getCity(self):
		return self.city
	def getPrice(self):
		return self.price
	def getType(self):
		return self.type
	def __str__(self):
		return str(self.name) + ':' + str(self.city) + ':' + str(self.price)

# Returns a set of coords (lat,lng) in Google Maps given an address name and a city
def getMapLocation(address, city):
	url = 'https://maps.googleapis.com/maps/api/geocode/json?'
	params = { 'key' : KEY_PLACES, 'address' : address+' '+city }
	url += urllib.urlencode(params)
	content = urllib2.urlopen(url).read()
	object_json = json.loads(content)
	
	lat = object_json['results'][0]['geometry']['location']['lat']
	long = object_json['results'][0]['geometry']['location']['lng']
	coords = [lat,long]
	return coords

# Returns a list with the cities that could match given an string of characters
def getCities(input_string):
	url = 'http://www.gasbuddy.com/Home/Autocomplete?'
	params = { 'query' : input_string }
	url += urllib.urlencode(params)
	content = urllib2.urlopen(url).read()
	list_cities = ast.literal_eval(content)
	return list_cities

# Gets info about a gas station given the results of the search
def getStation(object_json):
	cheapest_station = object_json['stations'][0]
	
	price_flag = True if cheapest_station['CheapestFuel']['CreditPrice'] != None else False
	if price_flag == True:
		price = str(cheapest_station['CheapestFuel']['CreditPrice']['Amount'])
	else:
		price = str(cheapest_station['CheapestFuel']['CashPrice']['Amount'])
	name = str(cheapest_station['Name'])
	address = str(cheapest_station['Address'])
	conc_city = str(cheapest_station['City'])
	gasStation = GasStation(name, address, price, price_flag, conc_city)
	return gasStation

# Given a set of coordinates returns the cheapest gas station
# in a GasStation object.
def getPriceGasByLocation(lat, lng):
	url = 'http://www.gasbuddy.com/Home/GeoSearch'
	params = { 'lat' : lat, 'lng' : lng }
	data = urllib.urlencode(params)
        req = urllib2.Request(url, data)
	content = urllib2.urlopen(req).read()
        object_json = json.loads(content)
	return getStation(object_json)

# Given a city returns the cheapest gas station in a GasStation object.
# The command parameter chooses if we are checking for diesel or standard gas.
def getPriceGasByCity(city, command):
	url = 'http://www.gasbuddy.com/Home/Search'
	params = { 's' : city }
	data = urllib.urlencode(params)
	req = urllib2.Request(url, data)
	if command == '/gas':
		req.add_header('Cookie', 'PreferredFuelId=1; PreferredFuelType=A')
	else:
		req.add_header('Cookie', 'PreferredFuelId=4; PreferredFuelType=D')

	content = urllib2.urlopen(req).read()
	object_json = json.loads(content)
	return getStation(object_json)

# This function is executed when someone types text in the inline!
@bot.inline_handler(lambda query: len(query.query) > 0)
def query_with_text(inline_query):
	try:
		query = inline_query.query
		cities = getCities(query)
		cities_found = []
		i = 0
		for city in cities:
			cities_found.append(telebot.types.InlineQueryResultArticle(str(i), str(city) + " (Gas)", telebot.types.InputTextMessageContent('/gas ' + str(city))))
			i += 1
			cities_found.append(telebot.types.InlineQueryResultArticle(str(i), str(city) + " (Diesel)", telebot.types.InputTextMessageContent('/diesel ' + str(city))))
			i += 1
			if i > 48:
				break
		bot.answer_inline_query(inline_query.id, cities_found)	
	except Exception as e:
		print e.message

# Help parameter. Shows a description on how to use the bot
@bot.message_handler(commands=['help'])
def helpCommand(message):
	try:
		bot.send_message(message.chat.id, "Send a location (USA or Canada) and you are done :D You can also use inline mode! Alternatively send a name of a city and a menu will be displayed to help you choose. If you want you can use the commands /gas and /diesel directly followed by a city name. Using the commands only the most popular city with that name will be displayed.")
	except:
		print "Error in help"
		return 1

# Function that gets called when the commands gas or diesel ar entered
@bot.message_handler(commands=['gas', 'diesel'])
def gasCommand(message):
	command = message.text.split(' ', 1)[0]
	try:
		input_city = message.text.split(' ', 1)[1]
	except:
		bot.send_message(message.chat.id, "You should add a city, ex: /gas New York")
		return 4
	try:
		cityList = getCities(input_city)
	except:
		bot.send_message(message.chat.id, "I'm sorry :S I wasn't able to find the cities!")		
		return 5
	if len(cityList) > 0:
		try:
			city = cityList[0]
			for element in cityList:
				if str(element) == input_city:
					city = str(element)
			station = getPriceGasByCity(city, command)
			bot.send_message(message.chat.id, "The cheapest gas station of " + station.getCity() + " is in the street: " + station.getAddress() + ". Price: " + station.getPrice())
		except:
			bot.send_message(message.chat.id, "I couldn't find the prices :'(")
			return 2
	else:
		bot.send_message(message.chat.id, "I couldn't find the city :'(")
		return 1

	try:
		map_coords = getMapLocation(station.getAddress(), station.getCity())
		location = telebot.types.Location(map_coords[0], map_coords[1])
		bot.send_location(message.chat.id,map_coords[0], map_coords[1])
	except:
		bot.send_message(message.chat.id, "I couldn't generate the map :'(")
		return 3

# Function that gets called when a location is sent
@bot.message_handler(content_types=['location'])
def handle_location(message):
	lng = str(message.location.longitude)
	lat = str(message.location.latitude)
	try:
		station = getPriceGasByLocation(lat,lng)
		bot.send_message(message.chat.id, "The cheapest gas station of your area is in: " + station.getAddress() + ", " + station.getCity() + ". Name: " + station.getName() + ". Price: " + station.getPrice())
	except:
		bot.send_message(message.chat.id, "I couldn't get the gas station info. Just make sure you sent a location of USA or Canada")
		return 1
	try:
		map_coords = getMapLocation(station.getAddress(), station.getCity())
		location = telebot.types.Location(map_coords[0], map_coords[1])
		bot.send_location(message.chat.id,map_coords[0], map_coords[1])
	except:
		bot.send_message(message.chat.id, "I couldn't generate the map :'(")
		return 2
	

# Function that gets called when it recieves a message
@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo_all(message):
	input = message.text
	try:
		cityList = getCities(input)
		if len(cityList) > 0:
			markup = telebot.types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
			for element in cityList:
				item = telebot.types.KeyboardButton('/gas ' + str(element))
				item2 = telebot.types.KeyboardButton('/diesel ' + str(element))
				markup.add(item, item2)
			bot.send_message(message.chat.id, text='Choose city and type:', reply_markup=markup)
		else:
			bot.send_message(message.chat.id, "I couldn't find the city. Does it exist? :v")		
	except:
		bot.send_message(message.chat.id, "I had a problem getting the cities, did you include any special character?")
		return 1


# Queries will be held every 3 seconds
def main():
	bot.polling()
	while True:
		time.sleep(3)

if __name__ == '__main__':
	main()
