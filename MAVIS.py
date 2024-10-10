import speech_recognition as sr
import pyttsx3
import re
from datetime import date
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Initialize text-to-speech engine and recognizer
Mavis_mouth = pyttsx3.init()
Mavis_ear = sr.Recognizer()

# Get today's date
today = date.today().strftime("%A %B %d, %Y")
print(today)

# List available voices and choose a female voice
voices = Mavis_mouth.getProperty('voices')
Mavis_mouth.setProperty('voice', voices[2].id)

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
        driver.execute_script("window.focus();")  # Focus the window
        driver.maximize_window()

    return driver

# Function to listen for the trigger word "Mavis"
def listen_for_trigger_word():
    with sr.Microphone() as mic:
        Mavis_ear.adjust_for_ambient_noise(mic)
        print("Mavis: Waiting for command...")
        audio = Mavis_ear.listen(mic)
        try:
            command = Mavis_ear.recognize_google(audio, language="en-US")
            return command.lower() if "Mavis" in command.lower() else ""
        except (sr.UnknownValueError, sr.RequestError) as e:
            logging.error(f"Listening error: {e}")
            return ""

# Function to listen for the actual command
def listen_for_command():
    with sr.Microphone() as mic:
        Mavis_ear.adjust_for_ambient_noise(mic)
        print("Mavis: I'm listening for your command...")
        audio = Mavis_ear.listen(mic)
        try:
            command = Mavis_ear.recognize_google(audio, language="en-US")
            return command.lower()
        except (sr.UnknownValueError, sr.RequestError) as e:
            logging.error(f"Command recognition error: {e}")
            return ""

def handle_mixed_command(command):
    keyword_for = re.findall(r"for (.*)", command)
    keyword_search = re.findall(r"search (.*)", command)
    return keyword_for[0] if keyword_for else keyword_search[0] if keyword_search else ""

# Main loop
try:
    while True:
        trigger = listen_for_trigger_word()
        if trigger:
            command = listen_for_command()
            print(f"You: {command}")

            if "hello" in command or "hi" in command:
                Mavis_response = "Hi, how can I help you?"
            elif "what the date today" in command:
                Mavis_response = "Today is " + today
            elif "open youtube" in command:
                search_term = handle_mixed_command(command)
                if search_term:
                    try:
                        driver = create_driver()  # Create or get existing driver
                        driver.get(f'https://www.youtube.com/results?search_query={search_term.replace(" ", "+")}')

                        # Wait for the page to load and the elements to be present
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_all_elements_located((By.XPATH, '//*[@id="video-title"]'))
                        )

                        video_elements = driver.find_elements(By.XPATH, '//*[@id="video-title"]')
                        first_video = next((video for video in video_elements if 'shorts' not in video.get_attribute('href')), None)

                        if first_video:
                            first_video.click()
                            Mavis_response = f"Playing: {search_term}, enjoy watching!"
                        else:
                            Mavis_response = "No suitable video found, excluding Shorts."
                    except Exception as e:
                        logging.error(f"Error interacting with Edge: {e}")
                        Mavis_response = "An error occurred while trying to open YouTube in Edge."
                        driver = None  # Reset driver to ensure it's reinitialized next time
                else:
                    Mavis_response = "No search term provided for YouTube."
            elif command == "":
                Mavis_response = "Sorry, I didn't catch that!"
            else:
                Mavis_response = "Please develop more functions!"

            # Convert the response text to speech
            print("Mavis: " + Mavis_response)
            Mavis_mouth.say(Mavis_response)
            Mavis_mouth.runAndWait()
except KeyboardInterrupt:
    print("Shutting down...")
finally:
    if driver is not None:
        driver.quit()  # Ensure the driver closes if it was created
