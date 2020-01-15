from lib.mBot import *
from multiprocessing import Process,Manager,Array
import threading
from time import sleep
dev = None
hidapi = hid()
hidapi.hid_init()
dev = hidapi.hid_open(0x0416, 0xffff)
exiting = False
def excepthook(exctype, value, traceback):
	global exiting
	exiting = True
	hidapi.hid_close(dev)
	
def __onRead():
	index = 0
	while(1):
		if exiting==True:
			break
		buf = hidapi.hid_read(dev,64)
		l = buf[0]
		if index==10:
			index = 0
			num = hidapi.hid_write(dev,[0,7,0xff,0x55,0x4,1,0x1,0x1,3])
		#num = hidapi.hid_write(dev,[0,12,0xff,0x55,0x9,0x0,0x2,0x8,0x7,0x2,0x0,0x30,0x20,0x30])
		#sleep(0.4)
		#num = hidapi.hid_write(dev,[0,12,0xff,0x55,0x9,0x0,0x2,0x8,0x7,0x2,0x0,0x10,0x10,0x30])
		#sleep(0.4)
		sleep(0.1)
		index += 1


th = threading.Thread(target=__onRead)
th.start()
sys.excepthook = excepthook
while(1):
	sleep(0.1)