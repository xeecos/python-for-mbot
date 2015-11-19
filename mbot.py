import serial
import sys,threading,time,signal
from time import ctime,sleep
import struct
import glob

buffer = []
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
				sleep(1)
		except Exception,ex:
			print str(ex)
			
def requestData():
	global timeIndex
	timeIndex += 1
	if timeIndex > 100:
		timeIndex = 0
		try:	
			if ser.isOpen():	
				#[0xff,0x55,0x4,0x2,0x1,31,0x1]
				ser.write(packageRGBLed(7,0,0x10,0x0,0x0))
		except Exception,ex:
			print str(ex)
			
def packageRGBLed(port,index,red,green,blue)
	return bytearray([0xff,0x55,0x8,0x0,0x2,0x8,port,index,red,green,blue])
	
def exitHandler(signum, frame):
	global is_loop
	is_loop = False
	print "receive a signal %d, is_exit = %d"%(signum, is_loop)

class ReadSerialThread(threading.Thread):
    def run(self):
		readLoop()

print(serialPorts())
signal.signal(signal.SIGINT, exitHandler)
signal.signal(signal.SIGTERM, exitHandler)
ser = serial.Serial("/dev/tty.wchusbserialfa130",115200)
thread = ReadSerialThread()
thread.setDaemon(True)
thread.start()
while True:
	alive = thread.isAlive()
	if not alive:
		break

