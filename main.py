import cv2
import numpy as np
from PIL import  ImageGrab, Image
import pyautogui
import time
from pytesseract import pytesseract
from pytesseract import Output
import FreeSimpleGUI as sg
import keyboard
import os.path
from tkinter import filedialog as fd
import random
from configparser import ConfigParser
import re
from collections import Counter
import playsound
from gtts import gTTS
from difflib import SequenceMatcher
from mutagen.mp3 import MP3

#Reading the configuration in config.ini
config = ConfigParser()
config.read('config.ini')

#Updating configuration based on config.ini
path_tesseract=config['options']['path']
confidence = int(float(config['options']['confidence']))
delay = int(config['options']['delay'])
default_tts_voices= ["English (US)", "English (UK)", "Spanish (Mexico)", "Spanish (Spain)", 
                     "French (France)", "French (Canada)", "Portuguese (Brazil)", "Portuguese (Portugal)"]
speeds = ["Normal", "Slow"]


def read_image(x1, y1,x2, y2):
    """Return the text and the image data of a given screen area.
    Arguments: 
    x1 and y1 referring to the top left of the screen area.
    x2 and y2 referring to the bottom right of the screen area.
    """
    cap = ImageGrab.grab(bbox=(x1, y1,x2, y2))
    cap_arr = np.array(cap)
    cv2.imwrite('current_img.png', img=cap_arr)
    image= cv2.imread('current_img.png')
    height, width, _ = image.shape
    pytesseract.tesseract_cmd=path_tesseract
    data = pytesseract.image_to_data(image=image, output_type=Output.DICT)
    text = ''
    img = image
    for i in range(len(data['text'])):
        if float(data['conf'][i] > int(float(config['options']['confidence']))):
            text +=  data['text'][i] + " "

    img = cv2.imencode('.png', cap_arr)[1].tobytes()
    return text, img


def removeCommonWords(sent1,sent2):
  """Return a string formed of non-repeating words in 2 sentences.
  Arguments:
  2 strings
  """
  sent1=list(sent1.split())
  sent2=list(sent2.split())
  sentence = ''
  for i in sent2:
    if i  not in sent1:
      sentence += i
      sentence += " "
  return sentence

def speak(text, voice, speed, pause):
    """
    Converts the input text to speech and plays it.

    Args:
        text (str): The text to be spoken.
    """
    lang, tld = '', ''
    slow = False
    stop = False
    if speed == "Slow":
        slow = True
    if pause == "Yes":
        stop = True

    if voice == 1:
        lang = 'en'
        tld = 'us'
    elif voice == 2:
        lang = 'en'
        tld = 'co.uk'
    elif voice == 3:
        lang = 'es'
        tld = 'com.mx'
    elif voice == 4:
        lang = 'es'
        tld = 'es'
    elif voice == 5:
        lang = 'fr'
        tld = 'fr'
    elif voice == 6:
        lang = 'fr'
        tld = 'ca'
    elif voice == 7:
        lang = 'pt'
        tld = 'com.br'
    elif voice == 8:
        lang = 'pt'
        tld = 'pt'
    if (text != '' and text != ' '):
        tts = gTTS(text=text, lang=lang, tld=tld, slow=slow)
        filename = ''.join(random.choices('0123456789', k=5))
        filename = filename + '.mp3'
        tts.save(filename)
        playsound.playsound(filename, stop) 
        os.remove(filename) 


def apply_options(path, confidence, delay, speed, voice, pause, stop_key):
    """Apply options set in the program onto the config.ini file.
    Arguments:
    All the keys defined in config.ini
    path: Tesseract.exe filepath.
    confidence: Confidence level for Tesseract purposes.
    delay: Time in seconds that the program will sleep for after reading a text.
    speed: (Default TTS only) Speed in Words-Per-Minute that the engine will read the text.
    volume: (Default TTS only) Volume in percentage that the audio will be played at.
    voice: (Default TTS only) Which voice the TTS engine will use for playing the audio.
    stop_key: Keyboard key used to stop the program from continuing. 
    """
    config['options']['path'] = path
    config['options']['confidence'] = str(confidence)
    config['options']['delay']  = str(delay)
    config['options']['speed'] = str(speed)
    config['options']['pause'] = str(pause)
    config['options']['voice']  = str(default_tts_voices.index(voice) + 1)
    config['options']['stop_key'] = stop_key

    with open('config.ini', 'w') as configfile:
        config.write(configfile)

def main_window():
    """Create the pysimpleGUI main window's layout."""
    sg.theme('Dark2')
    tab1 = [[sg.Image(filename='', key='image')],
            [sg.Text("Detected Text:", key='detected')],
            [sg.Text("Status:", key='status')],
              [sg.Button('Start'), sg.Button('Stop')]]
    tab2 = [[sg.Text("Tesseract path:")],
            [sg.Input(default_text=path_tesseract, key='path', 
                      tooltip="The path where the tesseract.exe is located.", readonly=True), sg.FileBrowse()],
            [sg.Text("Confidence Level:")],
            [sg.Slider(range=(0,100), default_value=confidence, orientation='horizontal', key='confidence',
                       tooltip="The higher the number, the more strict it will be with the data it picks up.\nLower numbers can lead to more misreadings.")],
            [sg.Text("Key to stop program:")],
            [sg.InputText(config['options']['stop_key'], key='stop_key', readonly=True), sg.Button("Change")],
            [sg.Text("Delay:")],
            [sg.Input(default_text=delay, key='delay', 
                      tooltip="Defines how long the program pauses in seconds after reading.\nUseful for text with transitions.")],
            [sg.Text("Speed:")],
            [sg.Combo(speeds, readonly=True, default_value=config['options']['speed'], key='speed', 
                     tooltip="The rate in words per minute for the TTS to speak in.")],
            [sg.Text("Pause program when reading:")],
            [sg.Combo(["Yes", "No"], readonly=True, default_value=config['options']['pause'], key='pause', 
                     tooltip="The rate in words per minute for the TTS to speak in.")],
            [sg.Text("Voice:")],
            [sg.Combo(default_tts_voices, readonly=True, default_value=default_tts_voices[int(float(config['options']['voice'])) - 1], key='default_voice')],
            [sg.Button("Test"),sg.Button("Apply")]]
    
    layout = [[sg.TabGroup([[sg.Tab('Main', tab1), sg.Tab('Options', tab2)]], key='tabgroup')]]
    
    return sg.Window("Reader", layout, finalize=True, resizable=True)


if __name__ == '__main__':
    """Main method."""
    window = main_window()
    recording = True
    x1, x2, y1, y2 = 0,0,0,0
    old_txt= ' '
    while True:

        event, values = window.read(timeout=20)
        try:
            if (event == sg.WIN_CLOSED):
                break
            elif event == 'Start':
                #Starts the screen reading function.
                recording = True
                sg.popup("Position the mouse on the top left of the area to be read.", auto_close=True, auto_close_duration= 3)
                x1, y1 = pyautogui.position()
                sg.popup("Position the mouse on the bottom right of the area to be read.", auto_close=True, auto_close_duration= 3)
                x2, y2 = pyautogui.position()
            elif event == 'Stop' or keyboard.is_pressed(values['stop_key']):
                #Stops the screen reading functions.
                sg.popup("Program Stopped")
                recording = False
                window.refresh()
            elif event == 'Apply':
                #Applies the options onto the config.ini file.
                apply_options(values['path'], values['confidence'], 
                              values['delay'], values['speed'], 
                              values['default_voice'], values['pause'],
                              values['stop_key'])
                sg.popup("Succesfully Applied")
            elif event == 'Test':
                #Tests both TTS engines.
                speak("This is a test", int(config['options']['voice']), config['options']['speed'], config['options']['pause'])
                #speak_default('This is the default TTS', int(float(config['options']['volume'])),
                      #        int(float(config['options']['speed'])), int(config['options']['voice']) - 1)
            elif event == 'Change':
                #Changes the key that will be used for stopping the program.
                window['stop_key'].update("Waiting for key...")
                window.refresh()
                k = keyboard.read_key()
                window['stop_key'].update(k)
        except Exception as ex:
            #Displays catched exception.
            sg.PopupError(ex)

        if values['tabgroup'] == 'Options':
            #In case the tab is switched from the main one to the options one, stop reading the screen.
            recording = False

        if recording and x2 != 0:
            #Logic behind reading the screen and detecting/speaking the text.
            txt, img = read_image(x1, y1, x2, y2)
            txt = txt.strip()
            txt = re.sub(r'[|-]+', 'I', txt)
            txt = re.sub(r'[^0-9A-Za-z ,.!?ñáéíóúÁÉÍÓÚâêîôÂÊÎÔãõÃÕçÇ:\'-]+', '', txt)
            window['image'].update(data=img)
            window.refresh()
            if txt != ' ' and txt != '' and txt != old_txt and SequenceMatcher(None, txt, old_txt).ratio() < 0.7:
                if old_txt != '' and txt.__contains__(old_txt):
                    txt = removeCommonWords(old_txt, txt).strip()
                printed_txt = ''
                for i, letter in enumerate(txt):
                    if i % 50 == 0:
                        printed_txt += '\n'
                    printed_txt += letter
                window['detected'].update(printed_txt)
                window['status'].update('Status: Processing...')
                window.refresh()
                speak(txt, int(config['options']['voice']), config['options']['speed'], config['options']['pause'])
                window['status'].update('Status: Processed.')
                old_txt = txt.strip()
            time.sleep(int(config['options']['delay']))