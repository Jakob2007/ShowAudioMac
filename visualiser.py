
import numpy as np
import colorsys
import pygame
import settings as s
from math import sqrt

# initialize pygame
pygame.init()
s_width, s_height = 1080, 720
screen = pygame.display.set_mode([s_width,s_height], pygame.RESIZABLE)
pygame.display.set_caption("AUDIO")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Marker Felt", 30)

# note names
NOTES = [
		"A2","A#2","H2","C3","C#3","D3","D#3","E3","F3","F#3","G3","G#3",
		"A3","A#3","H3","C4","C#4","D4","D#4","E4","F4","F#4","G4","G#4",
		"A4","A#4","H4","C5","C#5","D5","D#5","E5","F5","F#5","G5","G#5",
		"A5","A#5","H5","C6","C#6","D6","D#6","E6"
		]

def init(minimum_,multiplier_,system_volume_):
	global minimum,multiplier,system_volume
	minimum,multiplier,system_volume = minimum_,multiplier_,system_volume_

def quit():
	pygame.quit()

def color_from_val(val, v=1):
	hsvcol = (val, v, 1)
	col = colorsys.hsv_to_rgb(*hsvcol)
	col = np.array(col)*255
	return col.astype(int)

def mouth(stats):
	# eyes
	y = stats["bass"]
	pygame.draw.rect(screen, (255,255,255), (screen.get_width()/2+85, screen.get_height()/2-90+y, 30, 30))
	pygame.draw.rect(screen, (255,255,255), (screen.get_width()/2-115, screen.get_height()/2-90+y, 30, 30))

	# mouth
	w,h = 150, min(100, stats["voice"])**2 * 5
	pygame.draw.rect(screen, (255, 255, 255), (screen.get_width()/2-w/2, screen.get_height()/2+100-h/4, w, h))

def box(stats):
	box_val = stats["voice"] * s.multiplier

	m = 1.4
	# red
	rect = ((s_width-minimum*150-box_val*m)//2-30, (s_height-minimum*150-box_val*m)//2-30, minimum*150+box_val*m+35, minimum*150+box_val*m+35)
	pygame.draw.rect(screen, (255,0,60), rect)
	# blue
	rect = ((s_width-minimum*150-box_val*m)//2-5, (s_height-minimum*150-box_val*m)//2-5, minimum*150+box_val*m+35, minimum*150+box_val*m+35)
	pygame.draw.rect(screen, (0,10,255), rect)
	# white
	rect = ((s_width-minimum*150-box_val)//2, (s_height-minimum*150-box_val)//2, minimum*150+box_val, minimum*150+box_val)
	pygame.draw.rect(screen, (200,200,200), rect)
	# black
	rect = ((s_width-minimum*130-box_val)//2, (s_height-minimum*130-box_val)//2, minimum*130+box_val, minimum*130+box_val)
	pygame.draw.rect(screen, (0,0,0), rect)
	
	# red
	rect = ((s_width-minimum*50-box_val*m)//2-30, (s_height-minimum*50-box_val*m)//2-30, minimum*50+box_val*m+35, minimum*50+box_val*m+35)
	pygame.draw.rect(screen, (255,0,60), rect)
	# blue
	rect = ((s_width-minimum*50-box_val*m)//2-5, (s_height-minimum*50-box_val*m)//2-5, minimum*50+box_val*m+35, minimum*50+box_val*m+35)
	pygame.draw.rect(screen, (0,10,255), rect)
	# white
	rect = ((s_width-minimum*50-box_val)//2, (s_height-minimum*50-box_val)//2, minimum*50+box_val, minimum*50+box_val)
	pygame.draw.rect(screen, (200,200,200), rect)

def show(FFT,stats,sleep):
	global s_width, s_height

	# get user input
	playerquit = False
	keys = []
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			playerquit = True
		elif event.type == pygame.VIDEORESIZE:
			s_width, s_height = event.w, event.h
		elif event.type == pygame.KEYUP:
				if event.key == pygame.K_ESCAPE:
					playerquit = True
				elif event.key == pygame.K_q:
					playerquit = True
				else:
					keys.append(event.key)

	screen.fill((0,0,0))

	if s.show_note:
		f = font.render(NOTES[stats["note"]], False, color_from_val(stats["note"]/len(NOTES)))
		screen.blit(f, (20,20))
	if s.box:
		box(stats)

	# draw bars
	width = s_width // s.n
	for i,val in enumerate(FFT):
		height = sqrt(val)*s.multiplier+s.minimum
		# set color (white if dropped)
		col = color_from_val(i/len(FFT), v=(8-stats["droped"])/8)
		pygame.draw.rect(screen, (255,0,60), (i*width, s_height//2-height**1.04//2-10, width, height))
		pygame.draw.rect(screen, (0,10,255), (i*width, s_height//2-height//2+10, width, height**1.05))
		pygame.draw.rect(screen, col, (i*width, s_height//2-height//2, width, height))
	if stats["droped"]:
		stats["droped"]-= 1

	if s.face:
		mouth(stats)
	
	pygame.display.flip()
	clock.tick(sleep/2)

	return playerquit,keys