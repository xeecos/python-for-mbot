import serial
import sys,time
import signal
from time import ctime,sleep
import glob,struct
from multiprocessing import Process,Manager,Array
import threading
from ctypes import *
from ctypes.util import find_library

# Define public classes:

class hid_device_info(object):
    """Describes an HID device found by hid_enumerate()."""

    path                = ''
    vendor_id           = 0
    product_id          = 0
    serial_number       = str('')
    release_number      = 0
    manufacturer_string = str('')
    product_string      = str('')
    usage_page          = 0
    usage               = 0
    interface_number    = 0

    def __init__(self, __hid_device = None):
        """Constructor for class hid_device_info.

        __hid_device argument is for internal use by this module."""
        
        if __hid_device is not None:
            if bool(__hid_device):
                self.path                = __hid_device.path
                self.vendor_id           = __hid_device.vendor_id
                self.product_id          = __hid_device.product_id
                self.serial_number       = __hid_device.serial_number
                self.release_number      = __hid_device.release_number
                self.manufacturer_string = __hid_device.manufacturer_string
                self.product_string      = __hid_device.product_string
                self.usage_page          = __hid_device.usage_page
                self.usage               = __hid_device.usage
                self.interface_number    = __hid_device.interface_number

    def description(self):
        """Return a printable string describing the device."""

        desc = ''
        desc = desc + 'path:                "{:s}"\n'.format(str(self.path.decode('ascii')))
        desc = desc + 'vendor_id:           0x{:04x}\n'.format(self.vendor_id)
        desc = desc + 'product_id:          0x{:04x}\n'.format(self.product_id)
        desc = desc + 'serial_number:       "{:s}"\n'.format(self.serial_number)
        desc = desc + 'release_number:      0x{:04x}\n'.format(self.release_number)
        desc = desc + 'manufacturer_string: "{:s}"\n'.format(self.manufacturer_string)
        desc = desc + 'product_string:      "{:s}"\n'.format(self.product_string)
        desc = desc + 'usage_page:          {:d}\n'.format(self.usage_page)
        desc = desc + 'usage:               {:d}\n'.format(self.usage)
        desc = desc + 'interface_number:    {:d}\n'.format(self.interface_number)
        return desc
    


# Define types for internal use only:

class hid:
	class __c_hid_device_info(Structure):
		"""struct hid_device_info, ctypes version. For internal use by this binding."""
		pass
	# Variables for internal use only:
	__hidapi  = None                          # libhidapi
	__libpath = ''                            # library path
	__BUFSIZE = 256                           # string buffer size
	__c_hid_device_info_p = POINTER(__c_hid_device_info)
	__c_hid_device_info._fields_ = [('path',                c_char_p),
                                ('vendor_id',           c_ushort),
                                ('product_id',          c_ushort),
                                ('serial_number',       c_wchar_p),
                                ('release_number',      c_ushort),
                                ('manufacturer_string', c_wchar_p),
                                ('product_string',      c_wchar_p),
                                ('usage_page',          c_ushort),
                                ('usage',               c_ushort),
                                ('interface_number',    c_int),
                                ('next',                __c_hid_device_info_p)]

	# For internal use only: Load the hidapi library.
	def __load_hidapi(self):
		"""Load the hidapi library. For internal use only."""


		if self.sharedObject.__hidapi is None:
			# Search for the hidapi library.
			self.__libpath = find_library('hidapi') or\
						find_library('hidapi-libusb') or\
						find_library('hidapi-hidraw')
			if self.__libpath is None:
				raise RuntimeError('Could not find the hidapi shared library.')

			# Load the hidapi library.
			self.sharedObject.__hidapi = CDLL(self.__libpath)
			assert self.sharedObject.__hidapi is not None
			# Define argument and return types for the hidapi library functions.
			self.sharedObject.__hidapi.hid_close.argtypes                     = [c_void_p]
			self.sharedObject.__hidapi.hid_enumerate.argtypes                 = [c_ushort, c_ushort]
			self.sharedObject.__hidapi.hid_enumerate.restype                  = hid.__c_hid_device_info_p
			self.sharedObject.__hidapi.hid_error.argtypes                     = [c_void_p]
			self.sharedObject.__hidapi.hid_error.restype                      = c_wchar_p
			self.sharedObject.__hidapi.hid_free_enumeration.argtypes          = [hid.__c_hid_device_info_p]
			self.sharedObject.__hidapi.hid_get_feature_report.argtypes        = [c_void_p, c_void_p, c_int]
			self.sharedObject.__hidapi.hid_get_indexed_string.argtypes        = [c_void_p, c_int, c_wchar_p, c_int]
			self.sharedObject.__hidapi.hid_get_manufacturer_string.argtypes   = [c_void_p, c_wchar_p, c_int]
			self.sharedObject.__hidapi.hid_get_product_string.argtypes        = [c_void_p, c_wchar_p, c_int]
			self.sharedObject.__hidapi.hid_get_serial_number_string.argtypes  = [c_void_p, c_wchar_p, c_int]
			self.sharedObject.__hidapi.hid_open.argtypes                      = [c_ushort, c_ushort, c_wchar_p]
			self.sharedObject.__hidapi.hid_open.restype                       = c_void_p
			self.sharedObject.__hidapi.hid_open_path.argtypes                 = [c_char_p]
			self.sharedObject.__hidapi.hid_open_path.restype                  = c_void_p
			self.sharedObject.__hidapi.hid_read.argtypes                      = [c_void_p, c_void_p, c_int]
			self.sharedObject.__hidapi.hid_read_timeout.argtypes              = [c_void_p, c_void_p, c_int, c_int]
			self.sharedObject.__hidapi.hid_send_feature_report.argtypes       = [c_void_p, c_void_p, c_int]
			self.sharedObject.__hidapi.hid_set_nonblocking.argtypes           = [c_void_p, c_int]
			self.sharedObject.__hidapi.hid_write.argtypes                     = [c_void_p, c_void_p, c_int]


	# Define Python wrappers for hidapi library functions:
	def hid_close(self,device):
		"""Close an HID device.

		Arguments:
			device: A device handle returned by hid_open().

		Returns:
			None"""

		assert self.sharedObject.__hidapi is not None
		self.sharedObject.__hidapi.hid_close(device)


	def hid_enumerate(self,vendor_id=0, product_id=0):
		"""Enumerate the HID devices.

		This function returns a list of hid_device_info objects
		describing all of the HID devices which match vendor_id and product_id.
		If vendor_id is set to the default of 0, then any vendor matches.
		If product_id is set to the default of 0, then any product matches.
		If both are set to the default of 0, then all HID devices will be returned.

		Arguments:
			vendor_id:  The 16-bit vendor ID (VID) of devices to be enumerated.

			product_id: The 16-bit product ID (PID) of devices to be enumerated.

		Returns:
			List of hid_device_info objects, or an empty list."""

		assert self.sharedObject.__hidapi is not None

		# Init empty list of hid_device_info objects to be returned
		hid_list   = []

		# Call hid_enumerate() to get linked list of struct hid_device_info
		hid_list_p = self.sharedObject.__hidapi.hid_enumerate(vendor_id, product_id)

		# Create a Python list of hid_device_info class instances
		if bool(hid_list_p):
			dev = hid_list_p[0]
			while dev is not None:
				hid_list.append(hid_device_info(dev))
				if bool(dev.next):
					dev = dev.next[0]
				else:
					dev = None
					
		# Free library resources and return
		self.sharedObject.__hidapi.hid_free_enumeration(hid_list_p)
		return hid_list


	def hid_error(self,device):
		"""Get a string describing the last error which occurred.

		Arguments:
			device: A device handle returned by hid_open().

		Returns:
			String describing the last error that occurred, or None if no
			error has occurred."""
		
		assert self.sharedObject.__hidapi is not None
		err = self.sharedObject.__hidapi.hid_error(device)
		return err


	def hid_exit(self):
		"""Clean up hidapi library resources.

		Arguments:
			None

		Returns:
			None"""
		
		assert self.sharedObject.__hidapi is not None
		if self.sharedObject.__hidapi.hid_exit() != 0:
			raise RuntimeError('hid_exit() failed.')


	def hid_get_feature_report(self,device, data):
		"""Get a feature report from a HID device.

		Set the first byte of data[] to the Report ID of the report to be read, and
		make the size of data equal to the size of the desired report plus one more byte
		for the report ID number.

		*** This function is not adequately tested, because the author has not yet
		*** identified a device which uses feature reports with which to test the
		*** code.

		Arguments:
			device: A device handle returned by hid_open().

			data: A bytearray to be sent to the device as the feature report
				  request. Set the first byte to the desired report ID, or
				  0x00 if the device does not use numbered reports.

		Returns:
			Bytearray containing report from device. The first byte
			will be the report number.
			Raises RuntimeError exception if an error occurs."""
		
		assert self.sharedObject.__hidapi is not None

		buf = (c_ubyte * len(data))()
		cast(buf, POINTER(c_ubyte))
		for n in range(len(data)):
			buf[n] = chr(data[n])
		num = self.sharedObject.__hidapi.hid_get_feature_report(device, buf, len(data))
		if num < 0:
			raise RuntimeError('hid_get_feature_report() failed.')
		ba = bytearray(num)
		for n in range(num):
			ba[n] = buf[n]
		return ba


	def hid_get_indexed_string(self,device, string_index):
		"""Get a string from an HID device, based on its string index.

		Arguments:
			device: A device handle returned by hid_open().

			string_index: String index number to be fetched.

		Returns:
			Requested unicode string.
			Raises RuntimeError exception if error occurs."""

		
		assert self.sharedObject.__hidapi is not None

		buf = create_unicode_buffer(__BUFSIZE)
		val = self.sharedObject.__hidapi.hid_get_indexed_string(device, string_index, buf, __BUFSIZE)
		if val == -1:
			raise RuntimeError('Error getting indexed string.')
		else:
			return buf.value


		
	def hid_get_manufacturer_string(self,device):
		"""Get the manufacturer string from an HID device.

		Arguments:
			device: A device handle returned by hid_open().

		Returns:
			Manufacturer unicode string.
			Raises RuntimeError exception if error occurs."""
		
		assert self.sharedObject.__hidapi is not None

		buf = create_unicode_buffer(__BUFSIZE)
		val = self.sharedObject.__hidapi.hid_get_manufacturer_string(device, buf, __BUFSIZE)
		if val == -1:
			raise RuntimeError('Error getting manufacturer string.')
		else:
			return buf.value


	def hid_get_product_string(self,device):
		"""Get the product string from an HID device.

		Arguments:
			device: A device handle returned by hid_open().

		Returns:
			Product unicode string.
			Raises RuntimeError exception if error occurs."""
		
		assert self.sharedObject.__hidapi is not None

		buf = create_unicode_buffer(__BUFSIZE)
		val = self.sharedObject.__hidapi.hid_get_product_string(device, buf, __BUFSIZE)
		if val == -1:
			raise RuntimeError('Error getting product string.')
		else:
			return buf.value


	def hid_get_serial_number_string(self,device):
		"""Get the serial number string from an HID device.

		Arguments:
			device: A device handle returned by hid_open().

		Returns:
			Serial number unicode string.
			Raises RuntimeError exception if error occurs."""
		
		assert self.sharedObject.__hidapi is not None

		buf = create_unicode_buffer(__BUFSIZE)
		val = self.sharedObject.__hidapi.hid_get_serial_number_string(device, buf, __BUFSIZE)
		if val == -1:
			raise RuntimeError('Error getting serial number string.')
		else:
			return buf.value



	def hid_init(self):
		"""Initialize the hidapi library.

		User code must call this function before calling any other functions
		defined by this module."""

		
		self.manager = Manager()
		self.sharedObject = self.manager.dict()
		self.sharedObject.__hidapi = None
		if self.sharedObject.__hidapi is None:
			self.__load_hidapi()
		assert self.sharedObject.__hidapi is not None
		if self.sharedObject.__hidapi.hid_init() != 0:
			raise RuntimeError('hid_init() failed.')


	def hid_open(self,vendor_id, product_id, serial_number=None):
		"""Open an HID device by its VID and PID.

		Specify the desired device by vendor ID (VID), product ID (PID),
		and an optional serial number.

		If serial_number is None, open the first device found with the specified
		VID and PID.

		Arguments:
			vendor_id:  The 16-bit vendor ID (VID) of the device to be opened.

			product_id: The 16-bit product ID (PID) of the device to be opened.

			serial_number: Optional serial number Unicode string.

		Returns:
			Handle to opened device.
			Raises RuntimeError exception if device cannot be opened."""

		assert self.sharedObject.__hidapi is not None
		dev = self.sharedObject.__hidapi.hid_open(vendor_id, product_id, serial_number)
		if bool(dev):
			return dev
		else:
			raise RuntimeError('Could not open device.')
		

	def hid_open_path(self,path):
		"""Open an HID device by its path name.

		The path name be determined by calling hid_enumerate(), or a
		platform-specific path name can be used (eg: /dev/hidraw0 on Linux).

		Arguments:
			path: Path name of the device to open.

		Returns:
			Handle to opened device.
			Raises RuntimeError exception if device cannot be opened."""

		assert self.sharedObject.__hidapi is not None
		dev = self.sharedObject.__hidapi.hid_open_path(path)
		if bool(dev):
			return dev
		else:
			raise RuntimeError('Could not open device.')
		

	def hid_read(self, device, length):
		"""Read an Input report from a HID device.

		Input reports are returned to the host through the INTERRUPT IN endpoint.
		The first byte will contain the Report number if the device uses numbered
		reports.

		Arguments:
			device: A device handle returned by hid_open().

			length: Number of bytes to be read. For devices with multiple reports,
					include an extra byte for the report number.

		Returns:
			bytearray containing data that was read.
			Raises RuntimeError exception if an error occurs."""

		assert self.sharedObject.__hidapi is not None

		buf = (c_ubyte * length)()
		cast(buf, POINTER(c_ubyte))
		num = self.sharedObject.__hidapi.hid_read(device, buf, length)
		if num < 0:
			raise RuntimeError('hid_read() failed.')
		ba = bytearray(num)
		for n in range(num):
			ba[n] = (buf[n])
		return ba


	def hid_read_timeout(self, device, length, milliseconds):
		"""Read an Input report from a HID device with timeout.

		Input reports are returned to the host through the INTERRUPT IN endpoint.
		The first byte will contain the Report number if the device uses numbered
		reports.

		Arguments:
			device: A device handle returned by hid_open().

			length: Number of bytes to be read. For devices with multiple reports,
					include an extra byte for the report number.

			milliseconds: Timeout in milliseconds, or -1 for blocking read.

		Returns:
			bytearray containing data that was read.
			If no packet was available to be read within the timeout,
			returns an empty bytearray.
			Raises RuntimeError exception if an error occurs."""

		assert self.sharedObject.__hidapi is not None

		buf = (c_ubyte * length)()
		cast(buf, POINTER(c_ubyte))
		num = self.sharedObject.__hidapi.hid_read_timeout(device, buf, length, milliseconds)
		if num < 0:
			raise RuntimeError('hid_write() failed.')
		ba = bytearray(num)
		for n in range(num):
			ba[n] = (buf[n])
		return ba


	def hid_send_feature_report(self, device, data):
		"""Send a Feature report to the device.

		Feature reports are sent over the Control endpoint as a Set_Report
		transfer. The first byte of data[] must contain the Report ID. For
		devices which only support a single report, this must be set to 0x00.
		The remaining bytes contain the report data. Since the Report ID is
		mandatory, calls to hid_send_feature_report() will always contain one
		more byte than the report contains. For example, if a hid report is
		16 bytes long, 17 bytes must be passed to hid_send_feature_report():
		the Report ID (or 0x00, for devices which do not use numbered reports),
		followed by the report data (16 bytes). In this example, the length
		passed in would be 17.

		*** This function is not adequately tested, because the author has not yet
		*** identified a device which uses feature reports with which to test the
		*** code.

		Arguments:
			device: A device handle returned by hid_open().

			data: A bytearray containing the data to be written.

		Returns:
			Actual number of bytes written.
			Raises RuntimeError exception if an error occurs."""
		
		assert self.sharedObject.__hidapi is not None

		buf = (c_ubyte * len(data))()
		cast(buf, POINTER(c_ubyte))
		for n in range(len(data)):
			buf[n] = chr(data[n])
		num = self.sharedObject.__hidapi.hid_send_feature_report(device, buf, len(data))
		if num == -1:
			raise RuntimeError('hid_send_feature_report() failed.')
		return num


	def hid_set_nonblocking(self, device, nonblock):
		"""Set the device handle to be non-blocking.

		In non-blocking mode calls to hid_read() will return immediately with
		a value of 0 if there is no data to be read. In blocking mode,
		hid_read() will wait (block) until there is data to read before
		returning. Nonblocking can be turned on and off at any time.

		Arguments:
			device: A device handle returned by hid_open().

			nonblock: Set to True or 1 to enable nonblocking mode.
					  Set to False or 0 to disable nonblocking mode.

		Returns:
			None
			Raises RuntimeError exception if error occurs."""

		assert self.sharedObject.__hidapi is not None

		if nonblock:
			nb = 1
		else:
			nb = 0

		if self.sharedObject.__hidapi.hid_set_nonblocking(device, nb) == -1:
			raise RuntimeError('Error while changing nonblocking mode.')

		

	def hid_write(self, device, data):
		"""Write an Output report to a HID device.

		The first byte of the data argument  must contain the Report ID. For
		devices which only support a single report, this must be set to 0x00.
		The remaining bytes contain the report data. Since the Report ID is
		mandatory, calls to hid_write() will always contain one more byte
		than the report contains. For example, if a hid report is 16 bytes
		long, 17 bytes must be passed to hid_write(), the Report ID (or 0x00,
		for devices with a single report), followed by the report data (16
		bytes). In this example, the length passed in would be 17.

		hid_write() will send the data on the first OUT endpoint, if one
		exists. If it does not, it will send the data through the Control
		Endpoint (Endpoint 0).

		Arguments:
			device: A device handle returned by hid_open().

			data: A bytearray containing the data to be written.

		Returns:
			Actual number of bytes written.
			Raises RuntimeError exception if an error occurs."""
		
		assert self.sharedObject.__hidapi is not None
		buf = (c_ubyte * len(data))()
		cast(buf, POINTER(c_ubyte))
		#buf = create_string_buffer(len(data))
		for n in range(len(data)):
			buf[n] = data[n]
		num = self.sharedObject.__hidapi.hid_write(device, buf, len(data))
		if num == -1:
			raise RuntimeError('hid_write() failed.')
		return num


	# Define additional convenience functions:

	def hid_lib_path(self):
		"""Return path of loaded hidapi library.

		Arguments:
			none

		Returns:
			String containing path of loaded hidapi library."""
		
		assert self.sharedObject.__hidapi is not None

		return self.__libpath

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
		self.dict.device = hid()
		self.dict.device.hid_init()
		self.device = self.dict.device.hid_open(0x0416, 0xffff)
		#self.dict.device.hid_set_nonblocking(self.device,1)
		print "start"
		self.buffer = []
		self.bufferIndex = 0
	
	def enumerate(self):
		print "enumerate"
		for dev in self.dict.device.hid_enumerate():
			print '------------------------------------------------------------'
			print dev.description()

	def writePackage(self,package):
		buf = []
		buf += [0, len(package)]
		for i in range(len(package)):
			buf += [package[i]]
		n = self.dict.device.hid_write(self.device,buf)
		sleep(0.01)

	def read(self):
		c = self.buffer[0]
		self.buffer = self.buffer[1:]
		return unichr(c)
		
	def isOpen(self):
		return True
		
	def inWaiting(self):
		buf = self.dict.device.hid_read(self.device,64)
		l = 0
		if len(buf)>0:
			l = buf[0]
		if l>0:
			for i in range(0,l):
				self.buffer += [buf[i+1]]
		return len(self.buffer)
		
	def close(self):
		self.dict.device.hid_close(self.device)
		
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
					else:
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