import RPi.GPIO as GPIO
import time
import tkinter as tk
from tkinter import Label
import threading
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from datetime import datetime, timedelta
import os
import subprocess

RPin = 15
BPin = 17

GPIO.setmode(GPIO.BCM)
GPIO.setup(RPin, GPIO.OUT)
GPIO.setup(BPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

count = 0
counts_per_hour = {}
button_previous = GPIO.HIGH
start_time = datetime.now()
time_data = []
count_data = []

BASE_DIR = "/home/anode/KaynesTB"

root = tk.Tk()
root.title("TB PRODUCTION MONITOR")

start_time_label = Label(root, text=f"Start Time: {start_time.strftime('%H:%M:%S')}", font=("Arial", 16))
start_time_label.pack()

elapsed_time_label = Label(root, text="Elapsed Time: 0s", font=("Arial", 16))
elapsed_time_label.pack()

relay_label = Label(root, text="INDEX: STOP", font=("Arial", 16), fg="red")
relay_label.pack()

count_label = Label(root, text="Total Count: 0", font=("Arial", 16))
count_label.pack()

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 8))

def update_graph(frame):
    ax1.clear()
    ax1.set_xlabel("Time (Hours)")
    ax1.set_ylabel("Total Count")
    ax1.set_title("Real-Time Production Count")
    ax1.plot(time_data, count_data, marker='o', linestyle='-')
    
    ax2.clear()
    ax2.set_xlabel("Hour")
    ax2.set_ylabel("Production Count")
    ax2.set_title("Production Count Per Hour")
    
    hours = list(counts_per_hour.keys())
    values = list(counts_per_hour.values())
    
    colors = []
    for v in values:
        if v < 199:
            colors.append('red')
        elif 199<= v <=250:
            colors.append('blue')
        elif 251<= v <= 325:
            colors.append('green')
        else:
            colors.append('goldenrod')
            
    bars = ax2.bar(hours, values, color=colors)
    
    for bar, value in zip(bars, values):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height()/2, str(value), ha='center', va='center', color='white', fontsize=12)
        
ani = animation.FuncAnimation(fig,update_graph, interval=1000)
plt.ion()
plt.show()

def get_folder_name():
    now = datetime.now()
    #compare endofshift
    if now.time() < datetime.strptime("07:00:00", "%H:%M:%S").time():
        folder_date = now - timedelta(days=1)
    else:
        folder_date = now
    return folder_date.strftime("%d-%m-%Y")

def create_folder(base_path, folder_name):
    folder_path = os.path.join(base_path, folder_name)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    return folder_path

def capture_and_save_images():
    folder_name = get_folder_name()
    folder_path = create_folder(BASE_DIR, folder_name)
    
    timestamp = datetime.now().strftime("%H_%M_%S")
    filename = f"image_{timestamp}.png"
    file_path = os.path.join(folder_path, filename)
    
    #CaptureImage
    try:
        subprocess.run(["rpicam-still", "-e", "png", "-o", file_path, "--width 640", "--height 640", "--quality 50"], check=True)
        print(f"Image saved: {file_path}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to capture image:{e}")
        
def read_button():
    global count, button_previous, time_data, count_data
    
    while True:
        button_state = GPIO.input(BPin)
        
        # Detect falling edge (button press)
        if button_state == GPIO.LOW and button_previous == GPIO.HIGH:
            count += 1  # Increment count
            current_hour = datetime.now().strftime("%H")  # Get current hour
            
            # Store count per hour
            if current_hour not in counts_per_hour:
                counts_per_hour[current_hour] = 0
            counts_per_hour[current_hour] += 1
            
            print(f"COUNTNUM: {count}")
            relay_label.config(text="INDEX: RUN", fg="green")
            count_label.config(text=f"Total Count: {count}")
            GPIO.output(RPin, GPIO.HIGH)  # Turn ON relay
            
            # Append data for plotting
            elapsed_seconds = int((datetime.now() - start_time).total_seconds())
            elapsed_time_label.config(text=f"Elapsed Time: {elapsed_seconds}s")
            elapsed_hours = elapsed_seconds / 3600  # Convert to hours
            time_data.append(elapsed_hours)
            count_data.append(count)
            
            #call captureImage function
            capture_and_save_images()
            
            time.sleep(0.2) #debOunceDelay
            
        elif button_state == GPIO.HIGH and button_previous == GPIO.LOW:
            relay_label.config(text="INDEX: STOP", fg="red")
            GPIO.output(RPin, GPIO.LOW)
            
        button_previous = button_state
        time.sleep(0.1)
        
button_thread = threading.Thread(target=read_button, daemon=True)
button_thread.start()

root.mainloop()

GPIO.cleanup()
        

