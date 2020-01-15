from lib.mBot import *
from multiprocessing import freeze_support
if __name__ == '__main__':
	freeze_support()
	bot = mBot()
	#bot.startWithSerial("/dev/ttyUSB0")
	bot.startWithHID()
	tones ={"C3":131,"D3":147,"E3":165,"F3":175,"G3":196,"A3":220,"B3":247,
				"C4":262,"D4":294,"E4":330,"F4":349,"G4":392,"A4":440,"B4":494,
				"C5":523,"D5":587,"E5":659,"F5":698,"G5":784,"A5":880,"B5":988}
	music = ["E4","E4","F4","G4","G4","F4","E4","D4","C4","C4","D4","E4","E4","D4","D4"];
	while(1):
		try:	
			for i in range(0,len(music)):
				bot.doBuzzer(tones[music[i]],500)
				sleep(0.5)
		except ex:
			bot.doBuzzer(0)
		bot.doBuzzer(0)
		sleep(3)