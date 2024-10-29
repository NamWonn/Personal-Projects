import requests
import speech_recognition as sr
import pyttsx3
import re
from datetime import date, datetime
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)

# Initialize text-to-speech engine and recognizer
Mavis_mouth = pyttsx3.init()
Mavis_mouth.setProperty('rate',180) # Adjust speech rate
Mavis_ear = sr.Recognizer()

# List available voices and choose a female voice
voices = Mavis_mouth.getProperty('voices')
if len(voices) > 2:
    Mavis_mouth.setProperty('voice', voices[2].id)  # Female voice
else:
    Mavis_mouth.setProperty('voice', voices[0].id)  # Default to first voice if no female voice

# Get today's date
today = date.today().strftime("%A %B %d, %Y")

# Global driver variable
driver = None

# Set up Selenium Edge driver with user profile
def create_driver():
    global driver
    if driver is None:  # Only create a new driver if one does not exist
        options = Options()
        user_data_dir = r"C:\Users\Admin\AppData\Local\Microsoft\Edge\User Data\Default"  # Correct path to User Data
        options.add_argument(f"user-data-dir={user_data_dir}")
        options.add_argument("profile-directory=Default")  # Change to the correct profile name
        options.add_argument("--start-maximized")  # Start Edge maximized
        options.add_argument("--disable-blink-features=AutomationControlled")

        service = Service(executable_path=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedgedriver.exe")
        driver = webdriver.Edge(service=service, options=options)
    else:
        try:
            driver.execute_script("window.focus();")  # Focus the window
            driver.maximize_window()
        except Exception as e:
            logging.error(f"Error focusing Edge window: {e}")
            driver = None  # Reset driver to ensure it's reinitialized next time

    return driver

# Function to listen for the trigger word "Mavis"
def listen_for_trigger_word():
    while True:
        try:
            with sr.Microphone() as mic:
                Mavis_ear.adjust_for_ambient_noise(mic, duration=0.5)
                print("Mavis: Waiting for command...")
                audio = Mavis_ear.listen(mic, timeout=5, phrase_time_limit=5)
                command = Mavis_ear.recognize_google(audio, language="en-US").lower()
                if "mavis" in command:
                    return "mavis"
        except sr.WaitTimeoutError:
            continue
        except sr.UnknownValueError:
            continue
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            return ""

# Function to listen for the actual command
def listen_for_command():
    with sr.Microphone() as mic:
        Mavis_ear.adjust_for_ambient_noise(mic)
        audio = None
        try:
            audio = Mavis_ear.listen(mic, timeout=5)
        except sr.WaitTimeoutError:
            return "" 
        if audio:
            try:
                command = Mavis_ear.recognize_google(audio, language="en-US")
                return command.lower()
            except sr.UnknownValueError:
                return ""

def handle_mixed_command(command):
    keyword_for = re.findall(r"for (.*)", command)
    keyword_with = re.findall(r"with (.*)", command)
    return keyword_for[0] if keyword_for else keyword_with[0] if keyword_with else ""

def parse_time_to_seconds(command):
    # Pattern to capture hours, minutes, and seconds, prefixed by optional "in" or "after"
    pattern = r"(?:in\s|after\s)?(?:.*?(\d+)\s*hours?)?(?:.*?(\d+)\s*minutes?)?(?:.*?(\d+)\s*seconds?)?"
    match = re.search(pattern, command, re.IGNORECASE)

    if match:
        hours = int(match.group(1)) if match.group(1) else None
        minutes = int(match.group(2)) if match.group(2) else None
        seconds = int(match.group(3)) if match.group(3) else None
        
        # Calculate total_seconds only if there's at least one time component
        if hours is not None or minutes is not None or seconds is not None:
            total_seconds = (hours or 0) * 3600 + (minutes or 0) * 60 + (seconds or 0)
            total_seconds = max(total_seconds, 10)
        else:
            total_seconds = None

        return total_seconds, hours, minutes, seconds
    else:
        return None, None, None, None
    
# Function to fetch a joke from JokeAPI
def get_joke():
    url = "https://v2.jokeapi.dev/joke/Any"  # You can specify categories like "Programming" by appending ?category=Programming
    try:
        response = requests.get(url, timeout = 5)
        if response.status_code == 200:
            joke_data = response.json()
            
            if joke_data["type"] == "single":
                # Single-part joke
                return joke_data["joke"]
            elif joke_data["type"] == "twopart":
                # Two-part joke
                return f"{joke_data['setup']} ... {joke_data['delivery']}"
        else:
            return "Sorry, I couldn't get a joke at the moment."
    except requests.RequestException as e:
        print(f"Error getting joke: {e}")
        return "Sorry, I couldn't get a joke due to a network error."
    
def get_weather():
    api_key = "65879a808f2c8fb51ed0c0b218d1efba"  # API key
    city = "Ho Chi Minh"  # Fixed location
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    
    try:
        response = requests.get(url, timeout = 5)
        if response.status_code == 200:
            data = response.json()
            main_weather = data["weather"][0]["description"]
            temperature = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            
            weather_report = (
                f"The current weather in {city} is {main_weather} with a temperature of {temperature}°C. "
                f"It feels like {feels_like}°C, with a humidity of {humidity}%."
            )
            return weather_report
        else:
            return "Sorry, I couldn't retrieve the weather data right now."
    except requests.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return "Sorry, I couldn't retrieve the weather data due to a network error."
        
# Main loop
while True:
    trigger = listen_for_trigger_word()
    if trigger:
        print("Mavis: Yes, I'm listening.")
        Mavis_mouth.say("I'm listening.")
        Mavis_mouth.runAndWait()
        os.system("powershell -command \"(New-Object -ComObject WScript.Shell).SendKeys([char]173)\"")
        command = listen_for_command()
        os.system("powershell -command \"(New-Object -ComObject WScript.Shell).SendKeys([char]173)\"")
        print(f"You: {command}")

        if "hello" in command or "hi" in command:
            Current_hour = datetime.now().hour
            if 6 <= Current_hour < 12:
                welcome = "Good morning"
            elif 12 <= Current_hour < 18:
                welcome = "Good afternoon"
            else:
                welcome = "Good evening"
            Mavis_brain = f"{welcome}, how can I help you?"
        elif "what the date today" in command or "what is the date today" in command or "what day is it today" in command or "what is the date" in command or ("what" in command and "date" in command):
            Mavis_brain = "Today is " + today
        elif any(word in command for word in ["open youtube", "play youtube", "find youtube", "search youtube"]):
            search_term = handle_mixed_command(command)
            if search_term:
                try:
                    driver = create_driver()  # Create or get existing driver
                    driver.get(f'https://www.youtube.com/results?search_query={search_term.replace(" ", "+")}')
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.XPATH, '//*[@id="video-title"]'))
                    )
                    video_elements = driver.find_elements(By.XPATH, '//*[@id="video-title"]')
                    first_video = next((video for video in video_elements if 'shorts' not in video.get_attribute('href')), None)
                    if first_video:
                        first_video.click()
                        Mavis_brain = f"Playing {search_term}, enjoy watching!"
                    else:
                        Mavis_brain = "No suitable video found, excluding Shorts."
                except Exception as e:
                    logging.error(f"Error interacting with Edge: {e}")
                    Mavis_brain = "An error occurred while trying to open YouTube in Edge."
                    driver = None  # Reset driver to ensure it's reinitialized next time
            else:
                Mavis_brain = "No search term provided for YouTube."
        elif any(word in command for word in ["shut down", "shutdown", "turn off", "power off", "terminate", "initiate shutdown", "schedule power off"]):
            if any(word in command for word in ["cancel shut down", "cancel shutdown", "cancel turn off", "cancel power off"]):
                os.system("shutdown -a")
                logging.info("Shutdown has been canceled.")
                Mavis_brain = "Shutdown has been canceled."
            elif "now" in command:
                os.system("shutdown -s -t 10")
                Mavis_brain = "Shutting down now."
            else:
                time_in_seconds, hours, minutes, seconds = parse_time_to_seconds(command)
                if time_in_seconds is not None:
                    os.system(f"shutdown -s -t {time_in_seconds}")
                    Mavis_brain = f"Shutting down in {hours} hours, {minutes} minutes, and {seconds} seconds."
                else:
                    Mavis_brain = "Please specify a valid time for shutdown."

        elif any(word in command for word in ["what the weather", "what is the weather", "what weather"]) or ("tell" in command and "weather" in command):
            Mavis_brain = get_weather()
        elif "tell me a joke" in command or "give me a joke" in command or (("tell" in command or "give" in command) and "joke" in command):
            Mavis_brain = get_joke()
        elif command == "":
            Mavis_brain = "Sorry, I didn't catch that!"
        else:
            Mavis_brain = "Please develop for more functions!"

        # Convert the response text to speech
        print("Mavis: " + Mavis_brain)
        Mavis_mouth.say(Mavis_brain)
        Mavis_mouth.runAndWait()