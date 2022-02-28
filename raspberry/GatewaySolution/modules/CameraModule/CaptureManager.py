from threading import Thread
import time


class CaptureManager:
	def __init__(self, videoFeed, interval):

		self.vf = videoFeed
		self.stopped = False

		self.lastFrame = None
		self.interval = interval

	def start(self):

		Thread(target=self.update, args=()).start()
		return self

	def update(self):

		while True:

			if self.stopped:
				return

			(ret, frame) = self.vf.read()

			if ret:
				self.lastFrame = frame

			time.sleep(self.interval)

	
	def getLastFrame(self):
		return self.lastFrame

	def stop(self):
		# indicate that the thread should be stopped
		self.stopped = True        

