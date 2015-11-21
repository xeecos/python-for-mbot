import serial
import sys,time,signal
from multiprocessing import Process
from time import ctime,sleep
import struct
import glob
import copy

led = 1
timeIndex = 0

class mSerial():
	ser = None
	def start(self,port,callback):
		self.ser = serial.Serial(port,115200)
		self.parseBuffer = callback
		th = Process(target=self.onRead)
		th.start()

	def serialPorts(self):
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

	def onRead(self):
		while True:
			try:	
				if self.ser.isOpen()==True:
					n = self.ser.inWaiting()
					if n>0: 
						self.parseBuffer(ord(self.ser.read()))
					else:
						sleep(0.01)
				else:	
					sleep(0.5)
			except Exception,ex:
				print str(ex)

	def writePackage(self,package):
		self.ser.write(package)
		sleep(0.01)

class mBot():
	buffer = []
	bufferIndex = 0
	isParseStart = False
	isParseStartIndex = 0
	def __init__(self):
		self.selectors = {}

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
		
	def requestLightOnBoard(self,extID,callback):
		return self.requestLight(extID,8,callback)
	
	def requestLight(self,extID,port,callback):
		self.setCallback(extID,callback)
		return bytearray([0xff,0x55,0x4,extID,0x1,0x3,port])

	def requestButtonOnBoard(self,extID,callback):
		self.setCallback(extID,callback)
		return bytearray([0xff,0x55,0x4,extID,0x1,0x1f,0x7])
		
	def requestIROnBoard(self,extID,callback):
		self.setCallback(extID,callback)
		return bytearray([0xff,0x55,0x3,extID,0x1,0xd])
		
	def requestUltrasonicSensor(self,extID,port,callback):
		self.setCallback(extID,callback)
		return bytearray([0xff,0x55,0x4,extID,0x1,0x1,port])
		
	def requestLineFollower(self,extID,port,callback):
		self.setCallback(extID,callback)
		return bytearray([0xff,0x55,0x4,extID,0x1,0x11,port])
	
	def parseBuffer(self, byte):
		position = 0
		value = 0	
		self.buffer+=[byte]
		bufferLength = len(self.buffer)
		if bufferLength >= 2:
			if (self.buffer[bufferLength-1]==0x55 and self.buffer[bufferLength-2]==0xff):
				self.isParseStart = True
				self.isParseStartIndex = bufferLength-2	
			if (self.buffer[bufferLength-1]==0xa and self.buffer[bufferLength-2]==0xd and self.isParseStart==True):			
				self.isParseStart = False
				position = self.isParseStartIndex+2
				extID = self.buffer[position]
				position+=1
				type = self.buffer[position]
				position+=1
				# 1 byte 2 float 3 short 4 len+string 5 double
				if type == 1:
					value = self.buffer[position]
				if type == 2:
					value = self.readFloat(position)
					if(value<-255 or value>1023):
						value = 0
				if type == 3:
					value = self.readShort(position)
				if type == 4:
					value = self.readString(position)
				if type == 5:
					value = self.readDouble(position)
				if(type<=5):
					self.responseValue(extID,value)
				self.buffer = []

	def readFloat(self, position):
		v = [self.buffer[position], self.buffer[position+1],self.buffer[position+2],self.buffer[position+3]]
		return struct.unpack('<f', struct.pack('4B', *v))[0]
	def readShort(self, position):
		v = [self.buffer[position], self.buffer[position+1]]
		return struct.unpack('<h', struct.pack('2B', *v))[0]
	def readString(self, position):
		l = self.buffer[position]
		position+=1
		s = ""
		for i in Range(l):
			s += self.buffer[position+i].charAt(0)
		return s
	def readDouble(self, position):
		v = [self.buffer[position], self.buffer[position+1],self.buffer[position+2],self.buffer[position+3]]
		return struct.unpack('<f', struct.pack('4B', *v))[0]

	def responseValue(self, extID, value):
		try:	
			print self.selectors["func%d"%extID]
			# self.selectors[extID](value) 
		except Exception,ex:
			print "error",ex

	def setCallback(self,i,v):
		self.selectors["func%d"%i] = 10

	def float2bytes(self,fval):
		val = struct.pack("f",fval)
		return [ord(val[0]),ord(val[1]),ord(val[2]),ord(val[3])]

	def short2bytes(self,sval):
		val = struct.pack("h",sval)
		return [ord(val[0]),ord(val[1])]


#ser = serial.Serial("/dev/ttyUSB0",115200)
ser = mSerial()
bot = mBot()
print(ser.serialPorts())

ser.start("/dev/tty.wchusbserialfd120",bot.parseBuffer)

def onLight(value):
	print value

def requestTestData():
	global ser,bot,led
	while True:
		sleep(0.5)
		try:	
			led = 3 - led
			ser.writePackage(bot.packageRGBLedOnBoard(0x0,0x0,0x0,0x0))
			ser.writePackage(bot.packageRGBLedOnBoard(led,0x0,0x10,0x0))
			# ser.writePackage(bot.packageBuzzer(led*200))
			ser.writePackage(bot.requestLightOnBoard(8,onLight))
		except Exception,ex:
			print str(ex)

t = Process(target = requestTestData)
t.start()




