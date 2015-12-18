from lib.mBot import *
bot = mBot()
bot.startWithSerial("/dev/ttyUSB0")
while(1):
	try:	
		bot.doMove(100,100)
		print "run forward"
		sleep(2)
		bot.doMove(-100,-100)
		print "run backward"
		sleep(2)
	except Exception,ex:
		print str(ex)