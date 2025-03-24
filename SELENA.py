import requests
import re
import os
import time
import logging
import pygame
import io
import whisper
import numpy as np
import sounddevice as sd
from datetime import date, datetime
from scipy.io.wavfile import write
from gtts import gTTS
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from transformers import pipeline

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load models
whisper_model = whisper.load_model("medium")
generator = pipeline("text-generation", model="Qwen/Qwen2-1.5B")

# Get today's date  
today = date.today().strftime("%A %B %d, %Y")

# Global variable   
driver = None

def generate_response(prompt):
    """Generate AI response using pipeline."""
    response = generator(
        prompt, 
            max_new_tokens=50, 
            do_sample=True, 
            temperature=0.6, 
            return_full_text=False, 
            top_k=50, 
            top_p=0.95
    )[0]['generated_text']
    response = response.replace(prompt, "").strip()
    # Ensure the response ends at a full stop, exclamation mark, or question mark
    truncated_response = re.split(r'(?<=[.!?])\s', response)  # Split at sentence boundaries
    cleaned_response = " ".join(truncated_response[:-1]) if len(truncated_response) > 1 else response  # Remove the last cut-off part

    return cleaned_response.strip()

def speak(text):
    """Convert text to speech and play it using io.BytesIO."""
    pygame.mixer.init()
    tts = gTTS(text=text, lang="en")
    mp3_fp = io.BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    pygame.mixer.music.load(mp3_fp)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
    pygame.mixer.quit()

# Set up Selenium Edge driver with user profile
def create_driver():
    global driver
    if driver is None:
        options = Options()
        user_data_dir = r"C:\Users\Admin\AppData\Local\Microsoft\Edge\User Data\Default"
        options.add_argument(f"user-data-dir={user_data_dir}")
        options.add_argument("profile-directory=Default")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--log-level=3")  # Suppress unnecessary Edge logs
        service = Service(executable_path=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedgedriver.exe")
        driver = webdriver.Edge(service=service, options=options)
    else:
        try:
            driver.switch_to.window(driver.window_handles[0])  # Switch to first tab
            driver.maximize_window()
        except Exception as e:
            logging.error(f"Error switching to existing Edge window: {e}")
            driver.quit()  # Close and restart browser
            driver = None
    return driver

# Function to record audio and transcribe using Whisper
def record_and_transcribe(duration=5, filename="temp.wav"):
    print("Selena: Listening... ", end="")
    samplerate = 16000
    audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype=np.int16)
    sd.wait()
    write(filename, samplerate, audio)
    result = whisper_model.transcribe(filename,language ="en")["text"].strip()
    print(f"({result})")
    return result.lower()


def listen_for_trigger_word():
    while True:
        command = record_and_transcribe(duration=3)
        if "selena" in command:
            return "selena"

def listen_for_command():
    return record_and_transcribe(duration=5)

def handle_mixed_command(command):
    keyword_for = re.findall(r"for (.*)", command)
    keyword_with = re.findall(r"with (.*)", command)
    return keyword_for[0] if keyword_for else keyword_with[0] if keyword_with else ""

def parse_time_to_seconds(command):
    # Pattern to capture hours, minutes, and seconds, prefixed by optional "in" or "after"
    pattern = r"(?:in\s|after\s)?(?:.*?(\d+)\s*hours?)?(?:.*?(\d+)\s*minutes?)?(?:.*?(\d+)\s*seconds?)?"
    match = re.search(pattern, command, re.IGNORECASE)

    if match:
        hours = int(match.group(1)) if match.group(1) else 0
        minutes = int(match.group(2)) if match.group(2) else 0
        seconds = int(match.group(3)) if match.group(3) else 0

        # Calculate total_seconds
        total_seconds = hours * 3600 + minutes * 60 + seconds
        total_seconds = max(total_seconds, 10)  # Ensure at least 10 seconds

        return total_seconds, hours, minutes, seconds
    else:
        return 0, 0, 0, 0

def get_weather():
    api_key = "65879a808f2c8fb51ed0c0b218d1efba"
    city = "Ho Chi Minh"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            main_weather = data["weather"][0]["description"]
            temperature = data["main"]["temp"]
            return f"The current weather in {city} is {main_weather} with a temperature of {temperature}°C."
        else:
            return "Sorry, I couldn't retrieve the weather data right now."
    except requests.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return "Sorry, I couldn't retrieve the weather data due to a network error."

# Main loop
while True:
    trigger = listen_for_trigger_word()
    if trigger:
        print("Selena: Yes, I'm listening.")
        speak("Yes, I'm listening.")
        command = listen_for_command()
        print(f"You: {command}")
        if "what the date today" in command or "what is the date today" in command or "what day is it today" in command or "what is the date" in command or ("what" in command and "date" in command):
            Selena_brain = "Today is " + today
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
                        Selena_brain = f"Playing {search_term}, enjoy watching!"
                    else:
                        Selena_brain = "No suitable video found, excluding Shorts."
                except Exception as e:
                    logging.error(f"Error interacting with Edge: {e}")
                    Selena_brain = "An error occurred while trying to open YouTube in Edge."
                    driver = None  # Reset driver to ensure it's reinitialized next time
            else:
                Selena_brain = "No search term provided for YouTube."
        elif any(word in command for word in ["close youtube", "turn off youtube", "terminate youtube", "shutdown youtube", "kill youtube"]):
            if driver:  # Check if driver exists before quitting
                driver.quit()  # Close the browser
                driver = None  # Ensure driver is reset
                Selena_brain = "YouTube has been closed."
            else:
                Selena_brain = "No active YouTube session to close."
        elif any(word in command for word in ["press play", "press enter"]):
            os.system('powershell -command "(New-Object -ComObject WScript.Shell).SendKeys(\'{ENTER}\')"')
            Selena_brain = "Playing!"
        elif any(word in command for word in ["press space", "press pause"]):
            os.system('powershell -command "(New-Object -ComObject WScript.Shell).SendKeys(\' \')"')
            Selena_brain = "Toggling Play/Pause!"
        elif any(word in command for word in ["next video", "next song"]):
            os.system('powershell -command "(New-Object -ComObject WScript.Shell).SendKeys(\'+n\')"')
            Selena_brain = "Playing next video!"
        elif any(word in command for word in ["previous video", "previous song"]):
            os.system('powershell -command "(New-Object -ComObject WScript.Shell).SendKeys(\'%{LEFT}\')"')
            Selena_brain = "Playing previous video!"
        elif any(word in command for word in ["shut down", "shutdown", "turn off", "power off", "terminate", "initiate shutdown", "schedule power off"]):
            if any(word in command for word in ["cancel shut down", "cancel shutdown", "cancel turn off", "cancel power off"]):
                os.system("shutdown -a")
                logging.info("Shutdown has been cancelled.")
                Selena_brain = "Shutdown has been cancelled."
            elif "now" in command:
                os.system("shutdown -s -t 10")  # If "now" is detected, shutdown in 10s
                Selena_brain = "Shutting down now."
            else:
                time_in_seconds, hours, minutes, seconds = parse_time_to_seconds(command)
                print (time_in_seconds)
                if time_in_seconds > 10:  # Ensures that if no time is detected, it does not default to 10s
                    os.system(f"shutdown -s -t {time_in_seconds}")
                    Selena_brain = f"Shutting down in {hours} hours, {minutes} minutes, and {seconds} seconds."
                else:
                    Selena_brain = "Please specify a valid time for shutdown."
        elif any(word in command for word in ["what the weather", "what is the weather", "what weather"]) or ("tell" in command and "weather" in command) or ("what" in command and "weather" in command):
            Selena_brain = get_weather()
        elif re.search(r'\b(hi|hello)\b', command, re.IGNORECASE):
            Current_hour = datetime.now().hour
            if 5 <= Current_hour < 12:
                welcome = "Good morning"
            elif 12 <= Current_hour < 18:
                welcome = "Good afternoon"
            else:
                welcome = "Good evening"
            Selena_brain = f"{welcome}, how can I help you?"
        elif command == "":
            Selena_brain = "Sorry, I didn't catch that!"
        else:
            Selena_brain = generate_response(command)
        print("Selena: " + Selena_brain)
        speak(Selena_brain)
