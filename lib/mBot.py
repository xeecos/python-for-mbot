import serial
import sys,time
import signal
from time import ctime,sleep
import glob,struct
from multiprocessing import Process,Manager,Array
import threading
import hid

class mSerial():
	ser = None
	def __init__(self):
		print self

	def start(self, port):
		self.ser = serial.Serial(port,115200)
	
	def device(self):
		return self.ser

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

	def writePackage(self,package):
		self.ser.write(package)
		sleep(0.01)

	def read(self):
		return self.ser.read()

	def isOpen(self):
		return self.ser.isOpen()

	def inWaiting(self):
		return self.ser.inWaiting()

	def close(self):
		self.ser.close()
		
class mHID():
	def __init__(self):
		print self
		
	def start(self):
		
		self.manager = Manager()
		self.dict = self.manager.dict()
		self.dict.device = hid.device()
		self.dict.device.open(0x0416, 0xffff)
		#self.dict.device.hid_set_nonblocking(self.device,1)
		print "start"
		self.buffer = []
		self.bufferIndex = 0
	
	def enumerate(self):
		print "enumerate"
		for dev in self.dict.device.enumerate():
			print '------------------------------------------------------------'
			print dev.description()

	def writePackage(self,package):
		buf = []
		buf += [0, len(package)]
		for i in range(len(package)):
			buf += [package[i]]
		n = self.dict.device.write(buf)
		sleep(0.01)

	def read(self):
		c = self.buffer[0]
		self.buffer = self.buffer[1:]
		return unichr(c)
		
	def isOpen(self):
		return True
		
	def inWaiting(self):
		buf = self.dict.device.read(64)
		l = 0
		if len(buf)>0:
			l = buf[0]
		if l>0:
			for i in range(0,l):
				self.buffer += [buf[i+1]]
		return len(self.buffer)
		
	def close(self):
		self.dict.device.close()
		
class mBot():
	def __init__(self):
		print "init mBot"
		signal.signal(signal.SIGINT, self.exit)
		self.manager = Manager()
		self.__selectors = self.manager.dict()
		self.buffer = []
		self.bufferIndex = 0
		self.isParseStart = False
		self.exiting = False
		self.isParseStartIndex = 0
		
	def startWithSerial(self, port):
		self.device = mSerial()
		self.device.start(port)
		self.start()
	
	def startWithHID(self):
		self.device = mHID()
		self.device.start()
		self.start()
	
	def excepthook(self, exctype, value, traceback):
		self.close()
		
	def start(self):
		sys.excepthook = self.excepthook
		th = threading.Thread(target=self.__onRead,args=(self.onParse,))
		th.start()
		
	def close(self):
		self.device.close()
		
	def exit(self, signal, frame):
		self.exiting = True
		sys.exit(0)
		
	def __onRead(self,callback):
		while 1:
			if(self.exiting==True):
				break
			try:	
				if self.device.isOpen()==True:
					n = self.device.inWaiting()
					for i in range(n):
						r = ord(self.device.read())
						callback(r)
					sleep(0.01)
				else:	
					sleep(0.5)
			except Exception,ex:
				print str(ex)
				self.close()
				sleep(1)
				
	def __writePackage(self,pack):
		self.device.writePackage(pack)

	def doRGBLed(self,port,slot,index,red,green,blue):
		self.__writePackage(bytearray([0xff,0x55,0x9,0x0,0x2,0x8,port,slot,index,red,green,blue]))

	def doRGBLedOnBoard(self,index,red,green,blue):
		self.doRGBLed(0x7,0x2,index,red,green,blue)

	def doMotor(self,port,speed):
		self.__writePackage(bytearray([0xff,0x55,0x6,0x0,0x2,0xa,port]+self.short2bytes(speed)))

	def doMove(self,leftSpeed,rightSpeed):
		self.__writePackage(bytearray([0xff,0x55,0x7,0x0,0x2,0x5]+self.short2bytes(-leftSpeed)+self.short2bytes(rightSpeed)))
		
	def doServo(self,port,slot,angle):
		self.__writePackage(bytearray([0xff,0x55,0x6,0x0,0x2,0xb,port,slot,angle]))
	
	def doBuzzer(self,buzzer,time=0):
		self.__writePackage(bytearray([0xff,0x55,0x7,0x0,0x2,0x22]+self.short2bytes(buzzer)+self.short2bytes(time)))

	def doSevSegDisplay(self,port,display):
		self.__writePackage(bytearray([0xff,0x55,0x8,0x0,0x2,0x9,port]+self.float2bytes(display)))
		
	def doIROnBoard(self,message):
		self.__writePackage(bytearray([0xff,0x55,len(message)+3,0x0,0x2,0xd,message]))
		
	def requestLightOnBoard(self,extID,callback):
		self.requestLight(extID,8,callback)
	
	def requestLight(self,extID,port,callback):
		self.__doCallback(extID,callback)
		self.__writePackage(bytearray([0xff,0x55,0x4,extID,0x1,0x3,port]))

	def requestButtonOnBoard(self,extID,callback):
		self.__doCallback(extID,callback)
		self.__writePackage(bytearray([0xff,0x55,0x4,extID,0x1,0x1f,0x7]))
		
	def requestIROnBoard(self,extID,callback):
		self.__doCallback(extID,callback)
		self.__writePackage(bytearray([0xff,0x55,0x3,extID,0x1,0xd]))
		
	def requestUltrasonicSensor(self,extID,port,callback):
		self.__doCallback(extID,callback)
		self.__writePackage(bytearray([0xff,0x55,0x4,extID,0x1,0x1,port]))
		
	def requestLineFollower(self,extID,port,callback):
		self.__doCallback(extID,callback)
		self.__writePackage(bytearray([0xff,0x55,0x4,extID,0x1,0x11,port]))
	
	def onParse(self, byte):
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
		self.__selectors["callback_"+str(extID)](value)
		
	def __doCallback(self, extID, callback):
		self.__selectors["callback_"+str(extID)] = callback

	def float2bytes(self,fval):
		val = struct.pack("f",fval)
		return [ord(val[0]),ord(val[1]),ord(val[2]),ord(val[3])]

	def short2bytes(self,sval):
		val = struct.pack("h",sval)
		return [ord(val[0]),ord(val[1])]