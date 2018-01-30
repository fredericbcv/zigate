'''
Created on 22 janv. 2018

@author: sramage
'''
import pyudev
import threading
import logging
import time
import serial
import queue

LOGGER = logging.getLogger('zigate')


class ThreadSerialConnection(object):
    def __init__(self, device, port=None):
        self._port = port
        self.device = device
        self.queue = queue.Queue()
        self._running = True
        self.serial = self.initSerial()
        self.thread = threading.Thread(target=self.listen)
        self.thread.setDaemon(True)
        self.thread.start()

    def initSerial(self):
        self._port = self._find_port(self._port)
        return serial.Serial(self._port, 115200)

    def listen(self):
        while self._running:
            data = self.serial.read(self.serial.in_waiting)
            if data:
                threading.Thread(target=self.device.read_data,args=(data,)).start()
#                 self.device.read_data(data)
            while not self.queue.empty():
                data = self.queue.get()
                self.serial.write(data)
            time.sleep(0.05)

    def send(self, data):
        self.queue.put(data)

    def _find_port(self, port):
        '''
        automatically discover zigate port if needed
        '''
        port = port or 'auto'
        if port == 'auto':
            LOGGER.debug('Searching ZiGate port')
            context = pyudev.Context()
            devices = list(context.list_devices(ID_USB_DRIVER='pl2303'))
            if devices:
                port = devices[0].device_node
                LOGGER.debug('ZiGate found at {}'.format(port))
            else:
                LOGGER.error('ZiGate not found')
                raise Exception('ZiGate not found')
        return port

    def is_connected(self):
        return self.serial.is_open

    def close(self):
        self._running = False
        while self.thread.is_alive():
            time.sleep(0.1)
        self.serial.close()


class ThreadSocketConnection(ThreadSerialConnection):
    def __init__(self, device, host, port=9999):
        self._host = host
        ThreadSerialConnection.__init__(self, device, port)

    def initSerial(self):
        return serial.Serial('socket://{}:{}'.format(self._host, self._port))
