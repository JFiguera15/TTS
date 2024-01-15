import uberduck
from pydub import AudioSegment
from pydub.playback import play

client = uberduck.UberDuck('pub_ubsqfhozqtaaojxinp', 'pk_32ac9ac7-e610-4cf1-8700-08a1034db1b3')
voices = uberduck.get_voices(return_only_names = True)

speech = input('Enter speech: ')
voice = input('Enter voice or enter "LIST" to see list of voices: ')

if voice == 'LIST':
    print('Available voices:\n')
    for voice in sorted(voices): # sorting the voice list in alphabetical order
        print(voice)
    exit()

if voice not in voices:
    print('Invalid voice')
    exit()

client.speak(speech, voice, play_sound = True)


print('Spoke voice')