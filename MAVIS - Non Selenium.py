import speech_recognition as sr
import pyttsx3
import urllib.request
import re
import webbrowser
from datetime import date

# Initialize text-to-speech engine and recognizer
Mavis_mouth = pyttsx3.init()
Mavis_ear = sr.Recognizer()
Mavis_brain = ""

# Get today's date
today = date.today()
today = today.strftime("%A %B %d, %Y")
print(today)

# List available voices and choose a female voice
voices = Mavis_mouth.getProperty('voices')
Mavis_mouth.setProperty('voice', voices[1].id)  # Assuming voice[1] is female, adjust if needed

# Microphone index for UM02
MIC_INDEX = 1

# Function to listen for the trigger word "Mavis" (in any language)
def listen_for_trigger_word():
    with sr.Microphone(device_index=MIC_INDEX) as mic:
        Mavis_ear.adjust_for_ambient_noise(mic)
        print("Mavis: Waiting for command...")
        audio = Mavis_ear.listen(mic)
        try:
            command = Mavis_ear.recognize_google(audio, language="en-US")
            command = command.lower()
            if "Mavis" in command:
                return "Mavis"
            return command
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            return ""

# Function to listen for the actual command in both English and Vietnamese
def listen_for_command():
    with sr.Microphone(device_index=MIC_INDEX) as mic:
        Mavis_ear.adjust_for_ambient_noise(mic)
        print("Mavis: Yes, I'm listening.")
        Mavis_brain = "I'm listening."
        Mavis_mouth.say(Mavis_brain)
        Mavis_mouth.runAndWait()
        audio = Mavis_ear.listen(mic)
        try:
            command = Mavis_ear.recognize_google(audio, language="en-US")
            return command.lower(), 'en'
        except sr.UnknownValueError:
            return "", ""
            
def handle_mixed_command(command):
    if "open youtube" in command:
        keyword_for = re.findall(r"for (.*)", command)
        keyword_search = re.findall(r"search (.*)", command)
        keyword = keyword_for or keyword_search  # Choose whichever phrase is found
        if keyword:
            return keyword[0]
        else:
            return ""

# Main loop
while True:
    trigger = listen_for_trigger_word()
    if "Mavis" in trigger:
        command, lang = listen_for_command()
        print(f"You: {command}")  # Print the recognized command along with the language

        # Handle commands
        if "hello" in command or "hi" in command or "hey" in command or "bonjour" in command:
            Mavis_brain = "Hi, how can I help you?"
        elif "what the date today" in command or "what is the date today" in command or "what day is it today" in command or "what is the date" in command or ("what" in command and "date" in command):
            Mavis_brain = "Today is " + today
        elif "open youtube" in command:
            search_term = handle_mixed_command(command)
            if search_term:
                Mavis_brain = "Opening YouTube and searching for " + search_term
                encoded_search_term = urllib.parse.quote(search_term)
                try:
                    with urllib.request.urlopen(f"http://www.youtube.com/results?search_query={encoded_search_term}") as response:
                        html_content = response.read().decode('utf-8')
                        keyword_id = re.findall(r"watch\?v=(\S{11})", html_content)
                        if keyword_id:
                            url = "http://www.youtube.com/watch?v=" + keyword_id[0]
                            webbrowser.open(url)
                            Mavis_brain = "Opening " + search_term + " on YouTube."
                        else:
                            Mavis_brain = "No video found."
                except Exception as e:
                    Mavis_brain = f"Error: {e}"
            else:
                Mavis_brain = "I didn't catch what to search for."
        elif command == "":
            Mavis_brain = "Sorry, I didn't catch that."
        else:
            Mavis_brain = "Please develop more functions!"

        # Convert the response text to speech
        print("Mavis: " + Mavis_brain)
        Mavis_mouth.say(Mavis_brain)
        Mavis_mouth.runAndWait()
