import speech_recognition as sr
from datetime import datetime
from logging.config import listen
import pyttsx3
import webbrowser
import wikipedia
import wolframalpha
import pygame
import math
import pyaudio
import threading
import random
import wave
import os
import pygame.mixer
# Speech-engine-initialisation

engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)  # 0 = male , 1 = female
activationWord = 'computer'  # one word only

# Configure Browser
# Set path
opera_path = r"C:\Users\User\AppData\Local\Programs\Opera\opera.exe"
webbrowser.register('opera', None, webbrowser.BackgroundBrowser(opera_path))

# wolfram alpha client
appID = 'XK39XQ-EV4K8V5V52'
wolfram_client = wolframalpha.Client(appID)


# Pygame Initialization

screen_width = 500
screen_height = 500
pygame.init()
pygame.display.set_caption("Computer Visualizer")
screen = pygame.display.set_mode((screen_width, screen_height))
clock = pygame.time.Clock()


# Global variable to control the visualizer
is_speaking = False


def generate_random_amplitude():
    return random.uniform(10, 100)


def draw_sine_wave(amplitude, frequency=0.03):
    screen.fill((0, 0, 0))
    points = []
    if amplitude > 10:
        for x in range(screen_width):
            y = screen_height/2 + int(amplitude * math.sin(x * frequency))
            points.append((x, y))
    else:
        points.append((0, screen_height/2))
        points.append((screen_width, screen_height/2))
    pygame.draw.lines(screen, (104, 210, 214), False, points, 3)
    pygame.display.flip()


def game_loop():
    global is_speaking
    while True:

        amplitude = generate_random_amplitude() if is_speaking else 10
        draw_sine_wave(amplitude)
        frequency = 0.03  # Adjust the frequency as needed
        draw_sine_wave(amplitude, frequency)  # Pass frequency as an argument
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return


def speak(text, rate=120):
    global is_speaking
    def on_start(name):
        global is_speaking
        is_speaking = True


    def on_end(name, completed):
        global is_speaking
        is_speaking = False


    engine.connect('started-utterance', on_start)
    engine.connect('finished-utterance', on_end)
    engine.setProperty('rate', rate)
    engine.say(text)
    engine.runAndWait()


def parse_command():
    listener = sr.Recognizer()
    print('Waiting for command...')

    with sr.Microphone() as source:
        listener.pause_threshold = 2
        input_speech = listener.listen(source)

    try:
        print('Recognizing Speech...')
        query = listener.recognize_google(input_speech, language='en_us')
        print(f'The input speech was: {query}')
    except Exception as exception:
        print('I did not understand, please repeat.')
        speak('I did not understand, please repeat.')
        print(exception)
        return 'None'

    return query


def search_wikipedia(query = ''):
    search_results = wikipedia.search(query)
    if not search_results:
        print('Now wikipedia results.')
        return 'No result received'
    try:
        wiki_page = wikipedia.page(search_results[0])
    except wikipedia.DisambiguationError as error:
        wiki_page = wikipedia.page(error.options[0])
    print(wiki_page.title)
    wiki_summary = str(wiki_page.summary)
    return wiki_summary


def list_or_dictionary(var):
    if isinstance(var, list):
        return var[0]['plaintext']
    else:
        return var['plaintext']


def search_wolframalpha(query = ''):
    responce = wolfram_client.query(query)

    # @success: Wolfram Alpha was able to resolve the query
    # @numpods: Nuber of results returned
    # pod: List of results. This can also contain subpods
    if responce['@success'] == 'false':
        return 'Could not cumpute.'

    # Query resolved
    else:
        result = ''
        # Question
        pod0 = responce['pod'][0]
        pod1 = responce['pod'][1]
        # May contain the answer, has the highest confidence value.
        # If it's primary, or has the title of result or definition, then it's the official result.
        if(('result') in pod1['@title'].lower()) or (pod1.get('@primary', 'false') == 'true') or ('definition' in pod1['@title'].lower()):
            # Get the results
            result = list_or_dictionary(pod1['subpod'])
            # Remove the bracketed section
            return result.split('('[0])
        else:
            question = list_or_dictionary(pod0["subpod"])
            # Remove the bracketed section
            return question.split('('[0])
            speak('Computation failed. Accesing Universal databank.')
            return search_wikipedia(question)


def record_audio(file_name, duration=30, chunk=1024, format=pyaudio.paInt16, channels=1, rate=44100):
    audio = pyaudio.PyAudio()

    # Open recording stream
    stream = audio.open(format=format, channels=channels,
                        rate=rate, input=True,
                        frames_per_buffer=chunk)

    print("Recording...")
    frames = []

    # Record audio for the specified duration
    for i in range(0, int(rate / chunk * duration)):
        data = stream.read(chunk)
        frames.append(data)

    # Stop recording
    print("Recording finished.")

    # Convert the audio data to the required format
    audio_data = b''.join(frames)

    # Save audio to file
    wf = wave.open(file_name, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(audio.get_sample_size(format))
    wf.setframerate(rate)
    wf.writeframes(audio_data)
    wf.close()

    print("Voice recording saved.")


pygame.mixer.init()


# Function to find the path of the last recorded audio log file
def find_last_audio_log():
    # Directory where audio logs are stored
    directory = "audio-logs"

    # Get a list of files in the directory
    files = os.listdir(directory)

    # Filter out non-audio log files
    audio_files = [file for file in files if file.endswith(".wav")]

    # Sort the audio files based on modification time
    audio_files.sort(key=lambda x: os.path.getmtime(os.path.join(directory, x)), reverse=True)

    # Return the path of the first (last recorded) audio log file
    if audio_files:
        return os.path.join(directory, audio_files[0])
    else:
        return None


# Function to play the last recorded audio log
def play_last_audio_log():
    # Find the path of the last recorded audio log
    audio_file_path = find_last_audio_log()

    if audio_file_path:
        # Load the audio file
        audio = pygame.mixer.Sound(audio_file_path)

        audio.set_volume(10)

        # Play the audio
        audio.play()

        # Wait for the audio to finish playing
        while pygame.mixer.get_busy():
            continue
    else:
        print("No audio log found.")


run_game = True



# Main Loop
if __name__ == '__main__':
    visualizer_thread = threading.Thread(target=game_loop)
    visualizer_thread.start()
    speak('Initializing system.')

    while True:
        # Parse as a list
        query = parse_command().lower().split()

        if query[0] == activationWord:
            query.pop(0)

            # List Command
            if query[0] == 'say':
                if 'hello' in query:
                    speak('Hello there.')
                else:
                    query.pop(0)  # remove say
                    speech = ' '.join(query)
                    speak(speech)

            if query[0] == 'do' and query[1] == 'you' and query[2] == 'know' and query[3] == 'me':
                    speak('You are Nicotopis.You created me.')


            # Navigation
            if query[0] == 'go' and query[1] == 'to':
                destination = query[2]
                speak(f'Opening {destination}')
                query = ' '.join(query[2:]) + '.com'
                webbrowser.get('opera').open_new(query)


            # wikipedia
            if query[0] == 'search' and query[1] == 'for':
                query = ' '.join(query[2:])
                speak('Accesing universal databank.')
                speak(search_wikipedia(query))

            # Wolfram Alpha
            if query[0] == 'compute' or query[0] == 'calculate':
                query = ' '.join(query[1:])
                speak('Calculating...')
                try:
                    result = search_wolframalpha(query)
                    speak(result)
                except:
                    speak('unable to compute')

            # Note-Taking
            if query[0] == 'text' and query[1] == 'log':
                speak('Ready to write your notes')
                newNote = parse_command().lower()
                now = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
                with open('note_%s.txt' % now, 'w') as newFile:
                    newFile.write(newNote)
                speak('Note written.')

            # Audio-Log
            if query[0] == 'record' and query[1] == 'audio' and query[2] == 'log':
                speak('Starting voice recording.')
                file_name = "audio-logs/recording_{}.wav".format(datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
                record_audio(file_name)
                speak('Voice recording saved.')

            # Last-Audio-Log
            if query[0] == 'find' and query[1] == 'last' and query[2] == 'log':
                speak('Finding last recorded log.')
                play_last_audio_log()

            # Close
            if query[0] == 'terminate':
                speak('Terminating.')
                pygame.quit()
                break
