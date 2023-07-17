
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

FFT_SAMPLE_POINTS = 64

icon = pygame.image.load('gitVersion/icon.png')
pygame.display.set_icon(icon)

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

def request_source(audio):
	opt = ", ".join([f'"{d["name"]}"' for d in sd.query_devices() if d["max_output_channels"] > 0])
	script = f"choose from list {{{opt}}} with title \"Choose output device:\""
	command = ['osascript', '-e', script]
	device = subprocess.run(command, capture_output=True, text=True).stdout

	audio.speaker = sd.OutputStream(samplerate=audio.fs, blocksize=BUFFERSIZE_playback, device=device)
	audio.speaker.start()

	p = "~/Library/Application Support/ShowSound"
	if not os.path.isdir(p): os.makedirs(p)
	with open(os.path.join(p, "deafultDevice"), "w") as file:
		file.write(device)

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

		os.system(f"{path} output 'Soundflower (2ch)'")
		atexit.register(change_to_normal_speaker)

		device_info = sd.query_devices("Soundflower (2ch)", 'input')
		self.fs = int(device_info['default_samplerate'])

		self.mic = sd.InputStream(samplerate=self.fs, blocksize=BUFFERSIZE_playback, device="Soundflower (2ch)")
		self.mic.start()

		try:
			p = "~/Library/Application Support/ShowSound"
			with open(os.path.join(p, "deafultDevice"), "r") as file:
				device = file.read()
		except:
			device = sd.query_devices()[sd.default.device[0]]["name"]
		self.speaker = sd.OutputStream(samplerate=self.fs, blocksize=BUFFERSIZE_playback, device=device)
		self.speaker.start()
		print(f"using {device[:-1]}")

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
	MULTEPLY = 2000000
	MAIN_COLOR = (200,200,200)

	def __init__(self, audio):
		self.audio = audio

		pygame.init()
		self.width, self.height = 1080, 720
		self.screen = pygame.display.set_mode((self.width,self.height), pygame.RESIZABLE)
		pygame.display.set_caption("Show Sound")
		
		self.clock = pygame.time.Clock()

	def handle_input(self):
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				self.audio.is_running = False
			elif event.type == pygame.VIDEORESIZE:
				self.width = event.w
				self.height = event.h
			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_SPACE:
					t = Thread(target=request_source, args=(self.audio,))
					t.daemon = True
					t.start()

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

		fft = get_fft(self.audio.audio_data)[::]
		for i, val in enumerate(fft):
			angle = (i) * (math.pi / (len(fft)-1))

			# length = math.sqrt(val) * (320 - 20*(i%2)) * (i+2) + self.height/2*.5 + (60 * (i%2))
			length = math.sqrt(val) * 250 * (i+2) + self.height/2*.5

			start_x1 = center_x + int(math.cos(angle- math.pi/2) * (120 - length/5))
			start_y1 = center_y + int(math.sin(angle- math.pi/2) * (120 - length/5))
			start_x2 = center_x + int(math.cos(2*math.pi-angle- math.pi/2) * (120 - length/5))
			start_y2 = center_y + int(math.sin(2*math.pi-angle- math.pi/2) * (120 - length/5))

			end_x1 = center_x + int(math.cos(angle- math.pi/2) * length)
			end_y1 = center_y + int(math.sin(angle- math.pi/2) * length)
			end_x2 = center_x + int(math.cos(2*math.pi-angle- math.pi/2) * length)
			end_y2 = center_y + int(math.sin(2*math.pi-angle- math.pi/2) * length)

			col = color_from_val((i+.5)/(len(fft)/2), min(1, math.sqrt(val) * (i+2)))
			pygame.draw.line(self.screen, col, (start_x1, start_y1), (end_x1, end_y1), 10)
			pygame.draw.line(self.screen, col, (start_x2, start_y2), (end_x2, end_y2), 10)

		col = color_from_val(0, min(1, math.sqrt(fft[5]*10)))
		pygame.draw.circle(self.screen, (75,0,0), (center_x, center_y), fft[5] * 20000 + self.height/2*.26)
		pygame.draw.circle(self.screen, col, (center_x, center_y), fft[5] * 20000 + self.height/2*.24)

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
