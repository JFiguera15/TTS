import cv2
import numpy as np
from PIL import  ImageGrab
import pyautogui
import time
from pytesseract import pytesseract
from pytesseract import Output
import pyttsx3
import PySimpleGUI as sg
import keyboard
import uberduck
import random
from configparser import ConfigParser
import re

#Reading the configuration in config.ini
config = ConfigParser()
config.read('config.ini')

#Updating configuration based on config.ini
client = uberduck.UberDuck(config['options']['api_key'], config['options']['secret_key'])
uberduck_voices= []
path_tesseract=config['options']['path']
confidence = int(float(config['options']['confidence']))
delay = int(config['options']['delay'])
default_tts_voices= ["Male", "Female", "Random"]
tts_engines = ["Default TTS", "Uberduck"]


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


def speak_uberduck(text, voices):
    """Reads a text with the specified voices utilizing the uberduck API.
    Arguments:
    text: Text to be read.
    voices: List of potential voices that will be used in the audio.
    """
    voice = random.choice(voices[0])
    client.speak(text, voice, play_sound=True)


def apply_options(path, confidence, delay, speed, volume, voice, api_key, secret_key, stop_key):
    """Apply options set in the program onto the config.ini file.
    Arguments:
    All the keys defined in config.ini
    path: Tesseract.exe filepath.
    confidence: Confidence level for Tesseract purposes.
    delay: Time in seconds that the program will sleep for after reading a text.
    speed: (Default TTS only) Speed in Words-Per-Minute that the engine will read the text.
    volume: (Default TTS only) Volume in percentage that the audio will be played at.
    voice: (Default TTS only) Which voice the TTS engine will use for playing the audio.
    api_key: Uberduck API key.
    secret_key: Uberduck API secret key.
    stop_key: Keyboard key used to stop the program from continuing. 
    """
    config['options']['path'] = path
    config['options']['confidence'] = str(confidence)
    config['options']['delay']  = str(delay)
    config['options']['speed'] = str(speed)
    config['options']['volume'] = str(volume)
    config['options']['voice']  = str(default_tts_voices.index(voice) + 1)
    config['options']['api_key'] = api_key
    config['options']['secret_key'] = secret_key
    config['options']['stop_key'] = stop_key

    with open('config.ini', 'w') as configfile:
        config.write(configfile)


def speak_default(text, volume, speed, voice):
    """Read a text with the default Windows TTS engine.
    volume:Volume in percentage that the audio will be played at.
    speed:Speed in Words-Per-Minute that the engine will read the text.
    voice:Which voice the TTS engine will use for playing the audio.
    """
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    if voice != 2:
        engine.setProperty('voice', voices[voice].id)
    else:
         engine.setProperty('voice', voices[random.choice([0,1])].id)
    engine.setProperty('rate', speed)
    engine.setProperty('volume', volume/100)
    engine.say(text)
    engine.runAndWait()


def get_uberduck_voice_list():
    """Get the voices written in voices.txt"""
    with open('voices.txt') as f:
        voices = f.read().splitlines()
    return voices


def main_window():
    """Create the pysimpleGUI main window's layout."""
    sg.theme('Dark2')
    tab1 = [[sg.Image(filename='', key='image')],
            [sg.Text("Detected Text:", key='detected')],
            [sg.Text("Status:", key='status')],
              [sg.Button('Start'), sg.Button('Stop'), sg.Combo(tts_engines, readonly=True, default_value="Default TTS", key='tts_type')]]
    tab2 = [[sg.Text("Tesseract path:")],
            [sg.Input(default_text=path_tesseract, key='path', 
                      tooltip="The path where the tesseract.exe is located.", readonly=True), sg.FileBrowse()],
            [sg.Text("Confidence Level:")],
            [sg.Slider(range=(0,100), default_value=confidence, orientation='horizontal', key='confidence',
                       tooltip="The higher the number, the more strict it will be with the data it picks up.\nLower numbers can lead to more misreadings.")],
            [sg.Text("Key to stop program:")],
            [sg.InputText(config['options']['stop_key'], key='stop_key', readonly=True), sg.Button("Change")],
            [sg.Text("Default TTS Options:")],
            [sg.Text("Delay:")],
            [sg.Input(default_text=delay, key='delay', 
                      tooltip="Defines how long the program pauses in seconds after reading.\nUseful for text with transitions.")],
            [sg.Text("Speed:")],
            [sg.Spin([i for i in range(1,400)], initial_value=config['options']['speed'], key='speed', 
                     tooltip="The rate in words per minute for the TTS to speak in.")],
            [sg.Text("Volume:")],
            [sg.Slider(range=(0,100), default_value=int(float(config['options']['volume'])), orientation='horizontal', key='volume')],
            [sg.Text("Voice:")],
            [sg.Combo(default_tts_voices, readonly=True, default_value=default_tts_voices[int(float(config['options']['voice'])) - 1], key='default_voice')],
            [sg.Text("Uberduck Options:")],
            [sg.Text("API key:")],
            [sg.InputText(password_char='*', default_text=config['options']['api_key'], key='api_key')],
            [sg.Text("Secret key:")],
            [sg.InputText(password_char='*', default_text=config['options']['secret_key'], key='secret_key')],
            [sg.Text("Voices:")],
            [sg.Listbox(get_uberduck_voice_list(), size=(15,3), key='voice_list', select_mode='multiple',
                        tooltip="List of voices obtained from voices.txt, if you wish to add more, add them to that file.\nIf you select multiple, the program will pick one at random for every utterance.")],
            [sg.HorizontalSeparator()],
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
            elif event == 'Apply':
                #Applies the options onto the config.ini file.
                apply_options(values['path'], values['confidence'], 
                              values['delay'], values['speed'], 
                              values['volume'], values['default_voice'],
                              values['api_key'], values['secret_key'], values['stop_key'])
                uberduck_voices.clear()
                uberduck_voices.append(values['voice_list'])
                sg.popup("Succesfully Applied")
            elif event == 'Test':
                #Tests both TTS engines.
                speak_default('This is the default TTS', int(float(config['options']['volume'])),
                              int(float(config['options']['speed'])), int(config['options']['voice']) - 1)
                if values['api_key'] != ' ' or values['secret_key'] != ' ':
                    speak_uberduck('This is the uberduck Tee Tee Ess', uberduck_voices)
                else:
                    sg.popup("No uberduck keys detected")
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
            txt = re.sub(r'[^0-9A-Za-z ,.\'-]+', '', txt)
            window['image'].update(data=img)
            window.refresh()
            if txt != ' ' and txt != '' and txt != old_txt:
                if old_txt != '' and txt.__contains__(old_txt):
                    txt = removeCommonWords(old_txt, txt).strip()
                window['detected'].update(txt)
                window['status'].update('Status: Processing...')
                window.refresh()
                if values['tts_type'] == 'Default TTS':
                    speak_default(txt, int(float(config['options']['volume'])), 
                                  int(float(config['options']['speed'])), int(config['options']['voice']) - 1)
                    window['status'].update('Status: Processed.')
                else:
                    try:
                        speak_uberduck(txt, uberduck_voices)
                        window['status'].update('Status: Processed.')
                    except Exception as ex:
                        sg.popup_error(ex)
                        recording = False
                old_txt = txt.strip()
            time.sleep(int(config['options']['delay']))