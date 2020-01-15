from lib.mBot import *
bot = mBot()
#bot.startWithSerial("/dev/ttyUSB0")
bot.startWithHID()
while(1):
	bot.doMove(100,100)
	sleep(2)
	bot.doMove(-100,-100)
	sleep(2)
	bot.doMove(0,0)
	sleep(2)