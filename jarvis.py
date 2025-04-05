import os
import sys
import time
import pyttsx3
import datetime

import datetime

import math
from requests import get
from bs4 import BeautifulSoup
import speech_recognition as sr
from PyQt5 import QtGui
from PyQt5.QtCore import QTimer , QTime, QDate,Qt
from PyQt5.QtGui import QMovie 
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUiType
from wikipedia.wikipedia import search    
from jarvisUI import Ui_jarvisUI
from phi.model.groq import Groq
from phi.agent import Agent
from phi.tools.shell import ShellTools
from phi.tools.duckduckgo import DuckDuckGo
from phi.tools.python import PythonTools
import requests



wapp = "5QX8TU-K8T86LTTTE"

agent = Agent(
    instructions=[
        "You are Benris like AI assistant. You can help me with my daily tasks.",
        "Give response in a way that it can be passed to a Text-to-Speech engine. Not in markdown format.",
    ],
    tools=[
    DuckDuckGo(),
    PythonTools(),
    ],
    model=Groq(id="llama-3.3-70b-versatile", api_key="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"),
    show_tool_calls=True,
    markdown=False,
    debug_mode=True
)

engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')

engine.setProperty('voice',voices[0].id)
def speak(audio):
    engine.say(audio)
    engine.runAndWait()

def wishMe():
    hour = int(datetime.datetime.now().hour)
    if hour>=0 and hour<12:
        speak("good Morning")
    elif hour>12 and hour<17:
        speak("good afternoon")
    else:
        speak("good evening")
    speak("I am benris")
    speak("Checking the internet connection")
    speak("Wait a moment")
    speak("Now I am online")
    now = datetime.datetime.now()
    speak("current time is ")
    speak(now.strftime("%H:%M:%S"))
    speak("I am ready to take commands how may I help you")

def get_weather(city):
    api_key = "your_openweathermap_api_key"  # Replace with your OpenWeatherMap API key
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    complete_url = base_url + "q=" + city + "&appid=" + api_key + "&units=metric"
    response = requests.get(complete_url)
    data = response.json()
    
    if data["cod"] != "404":
        main = data["main"]
        weather = data["weather"][0]
        temperature = main["temp"]
        pressure = main["pressure"]
        humidity = main["humidity"]
        description = weather["description"]
        weather_report = (f"The temperature in {city} is {temperature} degrees Celsius with "
                          f"{description}. The atmospheric pressure is {pressure} hPa and "
                          f"the humidity is {humidity}%.")
        return weather_report
    else:
        return "City not found."
    

def convert_size(size_bytes):
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 2)
   print("%s %s" % (s, size_name[i]))
   return "%s %s" % (s, size_name[i])

class MainThread(QThread):
    def __init__(self):
        super(MainThread,self).__init__()

    def run(self):
        self.TaskExecution() 

    def takecommands(self):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            print("Listening...")
            r.pause_threshold = 1
            r.energy_threshold = 390
            audio = r.listen(source)
        try:
            print("recognizing....")
            query = r.recognize_google(audio,language='en-in')
            print(f"user said : {query}\n")

        except Exception as e:
            error = "say that again please... or check your internet connection"
            print(error)
            return error
        return query
    
    def TaskExecution(self):
       
        while True:
            self.query = self.takecommands().lower() 
            res= agent.run(self.query)
            speak(res.content)
            # if "explorer" in self.query:
            #     speak("opening windows explorer")
            #     pyautogui.hotkey('win','e')
            
            # elif "ip address" in self.query:
            #     ip = get('https://api.ipify.org').text
            #     print(ip)
            #     speak(f"your ip address is {ip}")
           
       
            # elif "system status" in self.query:
            #     cpu_stats = str(psutil.cpu_percent())
            #     memory_in_use = convert_size(psutil.virtual_memory().used)
            #     total_memory = convert_size(psutil.virtual_memory().total)
            #     final_res = f"Currently {cpu_stats} percent of CPU, {memory_in_use} of RAM out of total {total_memory}  is being used "
            #     speak(final_res)
            # elif "take screenshot" in self.query or "take a screenshot" in self.query or "capture the screen" in self.query:
            #     speak("By what name do you want to save the screenshot?")
            #     name = self.takecommands().lower()
            #     speak("Alright sir, taking the screenshot")
            #     img = pyautogui.screenshot()
            #     name = f"{name}.png"
            #     img.save(name)
            #     speak("The screenshot has been succesfully captured")
            # elif "switch the window" in self.query or "switch window" in self.query:
            #     speak("Okay sir, Switching the window")
            #     pyautogui.hotkey('alt','tab')
            # elif "show all open windows" in self.query:
            #     speak("okay showing currently active windows")
            #     pyautogui.hotkey('win','tab')
            # elif "task manager" in self.query:
            #     speak("starting task manager")
            #     pyautogui.hotkey('ctrl','shift','esc')
           
            # elif "command prompt" in self.query:
            #     speak("launching command prompt")
            #     os.system("start /B start cmd.exe @cmd /k")
           
           
            # elif "launch" in self.query:
            #     speak("searching in the system...")
            #     n_app= self.query = self.query.replace("launch","")
            #     speak(f"ok opening {n_app}")
            #     pyautogui.hotkey('win','q')
            #     time.sleep(3)
            #     pyautogui.write(n_app,interval=0.1)
            #     pyautogui.press('enter')    
            #     time.sleep(1)
            #     speak(f"{n_app} is openned successfully")
            # elif "show me notifications" in self.query:
            #     speak("okay here is notification center")
            #     pyautogui.hotkey('win','a')
            # elif "desktop" in self.query:
            #     speak("okay minimizing all the windows")
            #     pyautogui.hotkey('win','d')
            # elif "type" in self.query:
            #     speak("what do you want to write?")
            #     write = self.takecommands()
            #     speak("writing...")
            #     pyautogui.write(write,interval=0.1)
            
           
            if 'bye' in self.query or "chala ja" in self.query:
                speak("goodbye have a nice day")
                exit()  
            
startExecution = MainThread()

class MainThread(QThread):
    # ...existing code...

    def TaskExecution(self):
        while True:
            self.query = self.takecommands().lower()
            res = agent.run(self.query)
            speak(res.content)
            
            # Add the following code to handle weather queries
            if "weather" in self.query:
                speak("Please tell me the city name.")
                city = self.takecommands().lower()
                weather_report = get_weather(city)
                speak(weather_report)     
class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_jarvisUI()
        self.ui.setupUi(self)
        self.ui.pushButton.clicked.connect(self.startTask)

    def startTask(self):
        self.ui.movie = QtGui.QMovie("D:\python automation\jarvis\circle.gif")
        self.ui.label_2.setMovie(self.ui.movie)
        self.ui.movie.start()
        self.ui.movie = QtGui.QMovie("D:\python automation\jarvis\load.gif")
        self.ui.label_3.setMovie(self.ui.movie)
        self.ui.movie.start()
        startExecution.start()

app = QApplication(sys.argv)
jarvis = Main()
jarvis.show()
exit(app.exec_())