import serial
import sys,threading,time
from time import ctime,sleep
import struct
import glob

buffer = []
bufferIndex = 0
isParseStart = False
isParseStartIndex = 0
timeIndex = 0

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

def parseBuffer(bytes):
	position = 0
	value = 0
	for i in range(bytes.length):
		buffer+=[bytes[i]]
		if buffer.length >= 2:
			if (buffer[buffer.length-1]==0x55 & buffer[buffer.length-2]==0xff):
				isParseStart = True
				isParseStartIndex = buffer.length-2
			if (buffer[buffer.length-1]==0xa & buffer[buffer.length-2]==0xd & isParseStart==True):
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
						if(value<-255|value>1023):
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
	return struct.unpack('<f', struct.pack('4b', *v))[0]
def readShort(position):
	v = [buffer[position], buffer[position+1]]
	return struct.unpack('<h', struct.pack('2b', *v))[0]
def readString(position):
	l = buffer[position]
	position+=1
	s = ""
	for i in Range(l):
		s += buffer[position+i].charAt(0)
	return s
def readDouble(position):
	v = [buffer[position], buffer[position+1],buffer[position+2],buffer[position+3]]
	return struct.unpack('<f', struct.pack('4b', *v))[0]
def responseValue(extId,value):
	print extId+":"+value
def readLoop():
	while True:
		try:	
			if ser.isOpen():
				n = ser.inWaiting()
				if n>0:
					parseBuffer(ser.read(n))
				sleep(0.01)
				timeIndex += 1
				if timeIndex > 100:
					timeIndex = 0
					requestData()
			else:	
				sleep(1)
		except Exception,ex:
			print str(ex)
def requestData():
	try:	
		if ser.isOpen():	
			ser.write([0xff,0x55,0x4,0x2,0x1,31,0x1])
	except Exception,ex:
		print str(ex)
class ReadSerialThread(threading.Thread):
    def run(self):
		readLoop()

print(serialPorts())
ser = serial.Serial("/dev/tty.wchusbserial14130",115200)
thread = ReadSerialThread()
thread.start()


