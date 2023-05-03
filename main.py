
import numpy as np

import sounddevice as sd
from scipy.fft import fft

from threading import Thread
from time import sleep
import subprocess
import atexit
import os
import re

import visualiser
import settings as s


path = "/Users/Jakob/documents/python/Sound/Audiodevice/audiodevice"

Mic = None
Speaker = None
running = True

def get_fft(buffer, samplePoints):
	FFT = 2.0/samplePoints * np.abs(fft(buffer)[:samplePoints])
	return np.array(FFT)

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

def change_to_normal_speaker():
	cmdList = [path, "output", "list"]
	speaker = subprocess.check_output(cmdList).decode("utf-8").split("\n")[0]
	os.system(f"{path} output '{speaker}'")
	print(f"changed to {speaker}")

def replay(dest):
	global running
	while running:
		audio = Mic.read(s.buffersize)[0]
		#audio = np.array(audio, dtype=object)
		dest[0] = audio * dest[2]
		dest[1] = True
		if s.backplay:
			try:
				Speaker.write(dest[0])
			except: break

def quit_():
	visualiser.quit()
	sd.stop()
	Mic.stop()
	Speaker.stop()

	change_to_normal_speaker()

def main(): 
	global running, Mic, Speaker

	# audio multiplier
	loudness = 100

	# change output to soundflower
	change_to_normal_speaker()
	os.system(f"{path} output 'Soundflower (2ch)'")

	# change to normal speaker when program is stopped
	atexit.register(quit_)

	# get sample rate
	device_info = sd.query_devices("Soundflower (2ch)", 'input')
	fs = int(device_info['default_samplerate'])
	
	# initialize soudflower microphone
	Mic = sd.InputStream(samplerate=fs, blocksize=s.buffersize, device="Soundflower (2ch)")
	Mic.start()

	# initialize speaker as Bluetooth speaker if possible
	try:
		# set delay if BT box has built in buffer
		delay = s.bt_delay
		Speaker = sd.OutputStream(samplerate=fs, blocksize=s.buffersize, device=s.bt)
		print("BT")
	# initialize speaker as normal speaker otherwise
	except:
		delay = 0
		Speaker = sd.OutputStream(samplerate=fs, blocksize=s.buffersize, device='Built-in Output')
		print("Built-in")
	Speaker.start()

	print("starts listning")

	# initialize variables
	FFTs = []
	delay_buffer = []
	system_volume = get_volume()
	stats = {"average":0, "voice":0, "droped":0, "bass":.01}
	activ = True

	# initialize visualiser
	visualiser.init(s.minimum,s.multiplier,system_volume)

	# start thread to playback audio
	data = [[], False, loudness]
	thread = Thread(target=replay, args=(data,))
	thread.start()

	while True:
		if activ:
			# set data package for audio replay and wait for audio
			data[2] = loudness
			while not data[1]: sleep(.001)
			data[1] = False
			buffer = data[0]
			# make 2-channel 1
			if len(buffer[0]) == 2:
				buffer = (buffer[:,0] + buffer[:,1]) / 2

			# manage delay
			FFT_prev = get_fft(buffer, s.n)
			delay_buffer.insert(0,FFT_prev.copy())
			if len(delay_buffer)*(s.buffersize / fs) >= delay:
				FFT = delay_buffer.pop()
			else:
				FFT = np.zeros(s.n)

			# make output smoth
			FFTs.insert(0,FFT.copy())
			if len(FFTs) > s.smothness:
				FFTs.pop()
			FFT = np.array(FFTs).sum(axis=0)/s.smothness

			# set stats for data analasys
			stats["note"] = np.argmax(FFT)
			stats["prev"] = stats["average"]
			stats["average"] = sum(FFT) / len(FFT)
			stats["voice"] = sum(FFT[15:50]) / len(FFT[15:50])

			# check if beat dropped
			b = sum(FFT[:10]) / len(FFT[:10])
			if b:
				if s.flash and (b / stats["bass"]) > 4:
					stats["droped"] = 8
				stats["bass"] = b
			else:
				stats["bass"] = .1

		else:
			# idle
			FFT = np.zeros(s.n)
			stats = {"average":0, "voice":0, "droped":0, "bass":.01}

		# show fft
		playerquit,keys = visualiser.show(FFT,stats,fs/s.buffersize)
		# check if user quit
		if playerquit:
			running = False
			break

		# check for user input
		if visualiser.pygame.K_SPACE in keys:
			if activ:
				activ = False
				change_to_normal_speaker()
			else:
				activ = True
				os.system(f"{path} output 'Soundflower (2ch)'")
		if visualiser.pygame.K_PLUS in keys:
			loudness = min(loudness+10,300)
		if visualiser.pygame.K_MINUS in keys:
			loudness = max(loudness-10,10)
		if visualiser.pygame.K_b in keys:
			visualiser.s.box = not visualiser.s.box
		if visualiser.pygame.K_f in keys:
			visualiser.s.face = not visualiser.s.face
		if visualiser.pygame.K_l in keys:
			visualiser.s.leds = not visualiser.s.leds


if __name__ == "__main__":
	main()
