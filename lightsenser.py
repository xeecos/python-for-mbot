from lib.mBot import *

def onLight(value):
	print "light = ",value
	
if __name__ == '__main__':
	bot = mBot()
	#bot.startWithSerial("COM15")
	bot.startWithHID()
	while(1):
		bot.requestLightOnBoard(1,onLight)
		sleep(0.5)