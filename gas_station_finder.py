# Remember to include the different encodings for the different languages

# Including necessary libraries
# telebot - to use the TelegramBot API
# urrlib2 - to connect to yandex (translator) and make requests
# json - to get the text of the responses
import telebot
import urllib2, urllib
import json
import ast

# Token of the telegram Bot
TOKEN_TELEGRAM = '130498184:AAFFJLIMxFV-UR8tlKbZeQi2wzU9Dckkr0w'
# Linking the Bot to this python script
bot = telebot.TeleBot(TOKEN_TELEGRAM)

KEY_PLACES = 'AIzaSyAgFyIkMlchQEzPyV3y6NR50MtZdfDvjic'

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
	

def getCities(input):
	url = 'http://www.gasbuddy.com/Home/Autocomplete?'
	params = { 'query' : input }
	url += urllib.urlencode(params)
	content = urllib2.urlopen(url).read()
	list = ast.literal_eval(content)
	return list

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

# Help parameter. Shows a description on how to use the bot
@bot.message_handler(commands=['help'])
def helpCommand(message):
	try:
		bot.reply_to(message, "Send a location (USA or Canada) and you are done. Or type a name of a city (USA or Canada) and a menu will be displayed, select the city and Gas or Diesel. Alternatively you can enter the commands /gas and /diesel followed by the city name. Using the commands only the most popular city with that name will be displayed.")
	except:
		print "Error"
		return 1



@bot.message_handler(commands=['gas', 'diesel'])
def gasCommand(message):
	command = message.text.split(' ', 1)[0]
	try:
		input = message.text.split(' ', 1)[1]
	except:
		bot.reply_to(message, "Add a city, ex: /gas New York")
		return 4
	cityList = getCities(input)
	if len(cityList) > 0:
		try:
			city = cityList[0]
			for element in cityList:
				if str(element) == input:
					city = str(element)
			station = getPriceGasByCity(city, command)
			bot.reply_to(message, "The cheapest gas station of " + city + " is in the street: " + station.getAddress())
			bot.reply_to(message, "Price: " + station.getPrice())
		except:
			bot.reply_to(message, 'Could not find the prices')
			return 2
	else:
		bot.reply_to(message, 'Could not find the city')
		return 1

	try:
		map_coords = getMapLocation(station.getAddress(), station.getCity())
		location = telebot.types.Location(map_coords[0], map_coords[1])
		bot.send_location(message.chat.id,map_coords[0], map_coords[1])
	except:
		bot.reply_to(message, 'Could not generate the map')
		return 3

@bot.message_handler(content_types=['location'])
def handle_location(message):
	lng = str(message.location.longitude)
	lat = str(message.location.latitude)
	try:
		station = getPriceGasByLocation(lat,lng)
		bot.reply_to(message, "The cheapest gas station of your area is in: " + station.getAddress() + ", " + station.getCity() + ". Name: " + station.getName() + ". Price: " + station.getPrice())
	except:
		bot.reply_to(message, "Could not get the gas station info. Make sure you sent a location of USA or Canada")
		return 1
	try:
		map_coords = getMapLocation(station.getAddress(), station.getCity())
		location = telebot.types.Location(map_coords[0], map_coords[1])
		bot.send_location(message.chat.id,map_coords[0], map_coords[1])
	except:
		bot.reply_to(message, 'Could not generate the map')
		return 2
	

@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo_all(message):
	input = message.text
	try:
		cityList = getCities(input)
		if len(cityList) > 1:
			markup = telebot.types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
			for element in cityList:
				item = telebot.types.KeyboardButton('/gas ' + str(element))
				item2 = telebot.types.KeyboardButton('/diesel ' + str(element))
				markup.add(item, item2)
			bot.send_message(message.chat.id, text='Choose city and type:', reply_markup=markup)
	except:
		bot.reply_to(message, "Problem getting city name, make sure you didn't include special characters")
		return 1

bot.polling()
