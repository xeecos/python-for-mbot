# Python Library for mBot
Table of contents
=================

  * [Description](#description)
  * [Software Dependencies](#software-dependencies)
  * [Installation](#installation)
  * [Usage](#usage)

Description
-----------
A Python interface to control and communicate with mBot robot kit from Makeblock

This has been tested with:

* the Raspberry PI.
* the Intel Edison.

It works on Linux, Windows 7 and OS X.

Software Dependencies
---------------------

* Python (http://python.org/download/)
* Cython (http://cython.org/#download)
* cython-hidapi (https://github.com/trezor/cython-hidapi)
* pyserial

Installation
-------

install python 2.7.x ( http://python.org/downloads )

  ```
  for windows: set path x:/Python27 x:/Python27/Scripts
  Install Microsoft Visual C++ Compiler for Python 2.7
  ( http://www.microsoft.com/en-us/download/confirmation.aspx?id=44266 )
  ```
  ```
  [sudo] pip install cython
  [sudo] pip install pyserial
  [sudo] pip install hidapi
  ```
Usage
-----------------
 ```
  git clone https://github.com/xeecos/python-for-mbot
 ```
 Edit lightsensor.py
  
  using usb serial or bluetooth serial:
  
  change the serial port name "COMX" for your mBot on system
  ```
  bot.startWithSerial("COM15")
  ```
  
  using wireless HID:
  
  ```
  bot.startWithHID()
  ```
  ```
  [sudo] python lightsensor.py
  ```
