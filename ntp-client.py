"""
NTP client
NTP packet:
    0              1               2               3
    0 1 2 3 4 5 6 7 0 1 2 3 4 5 6 7 0 1 2 3 4 5 6 7 0 1 2 3 4 5 6 7
   -----------------------------------------------------------------
   |LI | VN  |Mode |    Stratum    |      Poll     |   Precision   |
   -----------------------------------------------------------------
   |                              Root Delay			   |
   -----------------------------------------------------------------
   |                           Root Dispersion                     |
   -----------------------------------------------------------------
   |                         Reference Identifier                  |
   -----------------------------------------------------------------
   |                          Reference Timestamp                  |
   -----------------------------------------------------------------
   |                          Originate Timestamp                  |
   -----------------------------------------------------------------
   |                           Receive Timestamp                   |
   -----------------------------------------------------------------
   |                          Transmit Timestamp                   |
   -----------------------------------------------------------------
   |                        Key Identifier(optional)               |
   -----------------------------------------------------------------
   |                        Message Digest(optional)               |
   -----------------------------------------------------------------
"""
import socket
import struct
import time
from datetime import date,datetime
from win32api import SetSystemTime,GetLastError




class NTP_PACKET():
	_FORMAT = "!B B b b 11I"

	def __init__(self,VN = 2,mode = 3,transmit = 0):
		self.LI = 0
		self.VN = VN
		self.mode = mode
		self.stratum = 0
		self.poll = 0
		self.precision = 0
		self.root_delay = 0
		self.root_disperation = 0
		self.ref_id = 0
		self.ref = 0
		self.originate = 0
		self.receive = 0
		self.transmit = transmit

	def pack(self):
		return struct.pack(NTP_PACKET._FORMAT,
			(self.LI << 6) + (self.VN << 3) + self.mode,
			self.stratum,
			self.poll,
			self.precision,
			int(self.root_delay) + self.get_fraction(self.root_delay,16),
			int(self.root_disperation) + self.get_fraction(self.root_disperation,16),
			self.ref_id,
			int(self.ref),
			self.get_fraction(self.ref,32),
			int(self.originate),
			self.get_fraction(self.originate,32),
			int(self.receive),
			self.get_fraction(self.receive,32),
			int(self.transmit),
			int(self.get_fraction(self.transmit,32)))

	def unpack(self,data):
		unpacked_data = struct.unpack(NTP_PACKET._FORMAT,data)

		self.LI = unpacked_data[0] >> 6 
		self.VN = unpacked_data[0] >> 3
		self.mode = unpacked_data[0] & 0b111

		self.stratum = unpacked_data[1]
		self.pool = unpacked_data[2]
		self.precision = unpacked_data[3]

		self.root_delay = (unpacked_data[4] >> 16) + (unpacked_data[4] & 0xFFFF) / 2**16
		self.root_disperation = (unpacked_data[5] >> 16) + (unpacked_data[5] & 0xFFFF) / 2**16

		self.ref_id = (str((unpacked_data[6] >> 24) & 0xFF) + " ") + \
					  (str((unpacked_data[6] >> 16) & 0xFF) + " ") + \
					  (str((unpacked_data[6] >> 8) & 0xFF) + " ")  + \
					  str(unpacked_data[6] & 0xFF)

		self.ref = unpacked_data[7] + unpacked_data[8] / 2 ** 32
		self.originate = unpacked_data[9] + unpacked_data[10] / 2 ** 32
		self.receive = unpacked_data[11] + unpacked_data[12] / 2 ** 32
		self.transmit = unpacked_data[13] + unpacked_data[14] / 2 ** 32

		return self


	def get_fraction(self,number,precision):
		return ((number - int(number)) * 2 ** precision)


class NTP_SOCKET():
	def __init__(self):
		self.create_socket()

	def create_socket(self):
		self.socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
		self.socket.settimeout(1.5)
		return socket

	def send(self):
		domain_name = "pool.ntp.org"
		port = 123

		package = self.create_packet()
		self.socket.sendto(package,(domain_name,port))

	def create_packet(self):
		now_time = time.time() + ((date(1970,1,1) - date(1900,1,1)).days * 24 * 3600)

		package = NTP_PACKET(VN = 2,mode = 3,transmit = now_time).pack()
		return package

	def receive_data(self):
		return self.socket.recv(48)


class MAIN_CLASS():
	def __init__(self):
		self.main()

	def main(self):
		socket = NTP_SOCKET()
		socket.send()

		data = socket.receive_data()
		self.unpacked_data = NTP_PACKET().unpack(data)

		self.time = self.output_time()

		try:
			SetSystemTime(self.time.year,self.time.month,self.time.weekday(),
			self.time.day,self.time.hour,self.time.minute,
			self.time.second,self.time.microsecond // 1000)
		except:
			pass

	def output_time(self):
		time_delta = self.unpacked_data.receive - self.unpacked_data.transmit
		t = datetime.utcfromtimestamp(time.time() + time_delta)
		return t

MAIN_CLASS()
