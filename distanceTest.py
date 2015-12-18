from lib.mBot import *
bot = mBot()
bot.startWithSerial("/dev/ttyUSB0")
def onDistance(dist):
	if dist<10:
		bot.doMove(-100,-100)
		print "run forward"
		sleep(0.2)
		bot.doMove(-100,100)
		print "turn left"
		sleep(0.2)
	bot.doMove(100,100)
	print "run forward"
	
while(1):
	try:	
		bot.requestUltrasonicSensor(1,3,onDistance)
		sleep(0.1)
	except Exception,ex:
		print str(ex)