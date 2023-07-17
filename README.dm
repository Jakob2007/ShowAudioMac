
# FEEL MUSIC
##macOS

## ABOUT
This project is a program to visualize audio in realtime.
The program fetches the data from Soundflower and generates the fft,
which shows the intensety of frequences in a given sample. This is than showen with pygame.

Additionally there are multiple options to visualize highs and lows. This can be extended further.
The code smoothes the output and is compatible with bluethooth speakers.
Desigened for MacOS

## Usage
After you have installed the necessities you have to input the path to the audiodevice executable in the main file and run the main file. 
To compile everything yourself into an app you can run this:
python3.10 -m PyInstaller --noconsole --onefile --windowed --icon=/path/to/icon.png /path/to/main/file.py


## Necessities
Soundflower (https://soundflower.de.softonic.com/mac/download)
Audiodevice (http://whoshacks.blogspot.com/2009/01/change-audio-devices-via-shell-script.html)

## MIT License

Copyright (c) 2023 Jakob Sauer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.