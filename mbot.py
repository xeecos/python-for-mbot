import serial
import sys,threading,time,signal
from time import ctime,sleep
import struct
import glob

buffer = []
packageList = []
bufferIndex = 0
timeIndex = 0
isParseStart = False
isParseStartIndex = 0
is_loop = True

def serialPorts():
	if sys.platform.startswith('win'):
		ports = ['COM%s' % (i + 1) for i in range(256)]
	elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
		ports = glob.glob('/dev/tty[A-Za-z]*')
	elif sys.platform.startswith('darwin'):
		ports = glob.glob('/dev/tty.*')
	else:
		raise EnvironmentError('Unsupported platform')
	result = []
	for port in ports:
		s = serial.Serial()
		s.port = port
		s.close()
		result.append(port)
	return result

def parseBuffer(byte):
	global buffer,isParseStart,isParseStartIndex
	position = 0
	value = 0	
	buffer+=[byte]
	bufferLength = len(buffer)
	if bufferLength >= 2:
		if (buffer[bufferLength-1]==0x55 and buffer[bufferLength-2]==0xff):
			isParseStart = True
			isParseStartIndex = bufferLength-2	
		if (buffer[bufferLength-1]==0xa and buffer[bufferLength-2]==0xd and isParseStart==True):			
			isParseStart = False
			position = isParseStartIndex+2
			extId = buffer[position]
			position+=1
			type = buffer[position]
			position+=1
			# 1 byte 2 float 3 short 4 len+string 5 double
			if type == 1:
				value = buffer[position]
			if type == 2:
				value = readFloat(position)
				if(value<-255 or value>1023):
					value = 0
			if type == 3:
				value = readShort(position)
			if type == 4:
				value = readString(position)
			if type == 5:
				value = readDouble(position)
			if(type<=5):
				responseValue(extId,value)
			buffer = []
def readFloat(position):
	v = [buffer[position], buffer[position+1],buffer[position+2],buffer[position+3]]
	return struct.unpack('<f', struct.pack('4B', *v))[0]
def readShort(position):
	v = [buffer[position], buffer[position+1]]
	return struct.unpack('<h', struct.pack('2B', *v))[0]
def readString(position):
	l = buffer[position]
	position+=1
	s = ""
	for i in Range(l):
		s += buffer[position+i].charAt(0)
	return s
def readDouble(position):
	v = [buffer[position], buffer[position+1],buffer[position+2],buffer[position+3]]
	return struct.unpack('<f', struct.pack('4B', *v))[0]

def responseValue(extId,value):
	print extId
	print value

def readLoop():
	global is_loop
	while is_loop:
		try:	
			if ser.isOpen():
				n = ser.inWaiting()
				if n>0: 
					parseBuffer(ord(ser.read()))
				else:
					sleep(0.01)
				requestData()
			else:	
				sleep(0.5)
		except Exception,ex:
			print str(ex)
led = 1
def requestData():
	global timeIndex,led,bot
	timeIndex += 1
	if timeIndex > 50:
		timeIndex = 0
		try:	
			if ser.isOpen():	
				led = 3 - led
				addPackage(bot.packageRGBLedOnBoard(0x0,0x0,0x0,0x0))
				addPackage(bot.packageRGBLedOnBoard(led,0x0,0x10,0x0))
				# addPackage(bot.packageBuzzer(led*200))
				addPackage(bot.requestLightOnBoard(8))
		except Exception,ex:
			print str(ex)

def addPackage(package):
	packageList.append(package)
	sendFirstPackage()

def sendFirstPackage():
	if len(packageList) > 0:
		ser.write(packageList[0])
		packageList.pop(0)
		sleep(0.01)

class mBot():
	def packageRGBLed(self,port,index,red,green,blue):
		return bytearray([0xff,0x55,0x8,0x0,0x2,0x8,port,index,red,green,blue])

	def packageRGBLedOnBoard(self,index,red,green,blue):
		return self.packageRGBLed(0x7,index,red,green,blue)

	def packageMotor(self,port,speed):
		return bytearray([0xff,0x55,0x6,0x0,0x2,0xa,port]+short2bytes(speed))

	def packageMove(self,leftSpeed,rightSpeed):
		return bytearray([0xff,0x55,0x7,0x0,0x2,0x5]+short2bytes(leftSpeed)+short2bytes(rightSpeed))
		
	def packageServo(self,port,slot,angle):
		return bytearray([0xff,0x55,0x6,0x0,0x2,0xb,port,slot,angle])
	
	def packageBuzzer(self,buzzer):
		return bytearray([0xff,0x55,0x5,0x0,0x2,0x22]+short2bytes(buzzer))

	def packageSevSegDisplay(self,port,display):
		return bytearray([0xff,0x55,0x8,0x0,0x2,0x9,port]+float2bytes(display))
		
	def packageIROnBoard(self,message):
		return bytearray([0xff,0x55,len(message)+3,0x0,0x2,0xd,message])
		
	def requestLightOnBoard(self,extID):
		return self.requestLight(extID,8)
	
	def requestLight(self,extID,port):
		return bytearray([0xff,0x55,0x4,extID,0x1,0x3,port])

	def requestButtonOnBoard(self,extID):
		return bytearray([0xff,0x55,0x4,extID,0x1,0x1f,0x7])
		
	def requestIROnBoard(self,extID):
		return bytearray([0xff,0x55,0x3,extID,0x1,0xd])
		
	def requestUltrasonicSensor(self,extID,port):
		return bytearray([0xff,0x55,0x4,extID,0x1,0x1,port])
		
	def requestLineFollower(self,extID,port):
		return bytearray([0xff,0x55,0x4,extID,0x1,0x11,port])
	
def exitHandler(signum, frame):
	global is_loop
	is_loop = False
	print "receive a signal %d, is_exit = %d"%(signum, is_loop)

def float2bytes(fval):
	val = struct.pack("f",fval)
	return [ord(val[0]),ord(val[1]),ord(val[2]),ord(val[3])]

def short2bytes(sval):
	val = struct.pack("h",sval)
	return [ord(val[0]),ord(val[1])]

class ReadSerialThread(threading.Thread):
    def run(self):
		readLoop()

print(serialPorts())
signal.signal(signal.SIGINT, exitHandler)
signal.signal(signal.SIGTERM, exitHandler)
ser = serial.Serial("/dev/tty.wchusbserialfa130",115200)
#ser = serial.Serial("/dev/ttyUSB0",115200)
thread = ReadSerialThread()
thread.setDaemon(True)
thread.start()
bot = mBot()

while True:
	alive = thread.isAlive()
	if not alive:
		break

