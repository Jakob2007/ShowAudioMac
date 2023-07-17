
from scipy.fft import fft
import sounddevice as sd
import colorsys
import math

import pygame

from threading import Thread
import numpy as np
import subprocess
import atexit
import time
import os
import re

path = r"/Users/Jakob/Documents/Python/Sound/Audiodevice/audiodevice"

BUFFERSIZE_playback = 128
BUFFERSIZE_show = BUFFERSIZE_playback * 4

FFT_SAMPLE_POINTS = 128

BT_DEVICE = "bt"

def get_fft(buffer):
	FFT = 2.0/FFT_SAMPLE_POINTS * np.abs(fft(buffer)[:FFT_SAMPLE_POINTS])
	return np.array(FFT)

def color_from_val(val, v=1):
	hsvcol = (val, v, 1)
	col = colorsys.hsv_to_rgb(*hsvcol)
	col = np.array(col)*255
	return col.astype(int)

def change_to_normal_speaker():
	cmdList = [path, "output", "list"]
	speaker = subprocess.check_output(cmdList).decode("utf-8").split("\n")[0]
	os.system(f"{path} output '{speaker}'")
	print(f"changed to {speaker}")

def get_volume():
	cmd = "osascript -e 'get volume settings'"
	process = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True)
	output = process.stdout.strip().decode('ascii')

	pattern = re.compile(r"output volume:(\d+), input volume:(\d+), "
						r"alert volume:(\d+), output muted:(true|false)")
	volume, _, _, muted = pattern.match(output).groups()
	volume = int(volume)
	if volume and muted == "false":
		return volume
	return 0

class Audio_keeper:
	def replay(self):
		while self.is_running:
			audio = self.mic.read(BUFFERSIZE_playback)[0]
			self.speaker.write(audio * 200)
			audio = (audio[:,0] + audio[:,1]) / 2
			
			if len(self.audio_data) >= BUFFERSIZE_show:
				self.audio_data = self.audio_data[BUFFERSIZE_playback:]
				self.is_data_available = True
			self.audio_data.extend(audio)

	def update_volume(self):
		while self.is_running:
			self.system_volume = get_volume()
			time.sleep(1)

	def __init__(self):
		self.is_running = True
		self.is_data_available = False
		self.audio_data = []
		self.system_volume = 0
		self.volume_history = [0] * 20

		change_to_normal_speaker()
		os.system(f"{path} output 'Soundflower (2ch)'")
		atexit.register(change_to_normal_speaker)

		device_info = sd.query_devices("Soundflower (2ch)", 'input')
		self.fs = int(device_info['default_samplerate'])

		self.mic = sd.InputStream(samplerate=self.fs, blocksize=BUFFERSIZE_playback, device="Soundflower (2ch)")
		self.mic.start()

		try:
			self.speaker = sd.OutputStream(samplerate=self.fs, blocksize=BUFFERSIZE_playback, device=BT_DEVICE)
			print("BT")
		except:
			self.speaker = sd.OutputStream(samplerate=self.fs, blocksize=BUFFERSIZE_playback, device='Built-in Output')
			print("Built-in")
		self.speaker.start()

		self.replay_thread = Thread(target=self.replay)
		self.volume_thread = Thread(target=self.update_volume)
		self.replay_thread.daemon = True
		self.volume_thread.daemon = True
		self.replay_thread.start()
		self.volume_thread.start()

	def quit(self):
		sd.stop()
		self.mic.stop()
		self.speaker.stop()


class Visualizer:
	MULTEPLY = 5000000
	MAIN_COLOR = (200,200,200)

	def __init__(self, audio):
		self.audio = audio

		pygame.init()
		self.width, self.height = 1080, 720
		self.screen = pygame.display.set_mode((self.width,self.height), pygame.RESIZABLE)
		pygame.display.set_caption("feel sound")
		
		self.clock = pygame.time.Clock()

	def handle_input(self):
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				self.audio.is_running = False
			elif event.type == pygame.VIDEORESIZE:
				self.width = event.w
				self.height = event.h
			elif event.type == pygame.KEYDOWN:
				pass

	def show(self):
		self.screen.fill((0,0,0))

		if not self.audio.system_volume:
			self.audio.system_volume = get_volume()
			return

		for i, val in enumerate(self.audio.audio_data):
			x1 = self.width / BUFFERSIZE_show * (i + .5)
			x2 = self.width / BUFFERSIZE_show * (BUFFERSIZE_show - i - .5)
			y = self.height / 2
			offset = val / (self.audio.system_volume * 2) * self.MULTEPLY

			pygame.draw.circle(self.screen, self.MAIN_COLOR, (x1, y+offset), 3)
			pygame.draw.circle(self.screen, self.MAIN_COLOR, (x1, y-offset), 3)

			pygame.draw.circle(self.screen, (75,0,0), (x2, y+offset + 75), 3)
			pygame.draw.circle(self.screen, (75,0,0), (x2, y-offset - 75), 3)
			pygame.draw.circle(self.screen, (0,75,0), (x2, y+offset + 85), 3)
			pygame.draw.circle(self.screen, (0,75,0), (x2, y-offset - 85), 3)
			pygame.draw.circle(self.screen, (0,0,75), (x2, y+offset + 95), 3)
			pygame.draw.circle(self.screen, (0,0,75), (x2, y-offset - 95), 3)

		center_x = self.width // 2
		center_y = self.height // 2

		fft = get_fft(self.audio.audio_data)[::4]
		for i, val in enumerate(fft):
			angle = (i) * (math.pi / (len(fft)-1))

			length = math.sqrt(val) * (320 - 20*(i%2)) * (i+2) + 180 + (50 * (i%2))

			end_x1 = center_x + int(math.cos(angle- math.pi/2) * length)
			end_y1 = center_y + int(math.sin(angle- math.pi/2) * length)
			end_x2 = center_x + int(math.cos(2*math.pi-angle- math.pi/2) * length)
			end_y2 = center_y + int(math.sin(2*math.pi-angle- math.pi/2) * length)

			col = color_from_val((i+.5)/(len(fft)/2))
			pygame.draw.circle(self.screen, col, (end_x1, end_y1), 5)
			pygame.draw.circle(self.screen, col, (end_x2, end_y2), 5)

		pygame.display.flip()
		self.clock.tick(self.audio.fs / BUFFERSIZE_playback / 2)

def main():
	audio = Audio_keeper()
	visualizer = Visualizer(audio)

	while audio.is_running:
		if audio.is_data_available:
			visualizer.handle_input()
			visualizer.show()
			audio.is_data_available = False

	audio.quit()

if __name__ == "__main__" :
	main()
