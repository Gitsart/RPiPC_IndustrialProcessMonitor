""import RPi.GPIO as GPIO
import time
import tkinter as tk
from tkinter import Label
import threading
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from datetime import datetime

# Define GPIO pins
RPin = 15  # GPIO14 for the relay
BPin = 17  # GPIO15 for the button

# Set up GPIO
GPIO.setmode(GPIO.BCM)  
GPIO.setup(RPin, GPIO.OUT)  # Set relay as output
GPIO.setup(BPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Set pull-up resistor

# Variables
count = 0  # Total button presses
counts_per_hour = {}  # Dictionary to store hourly counts
button_previous = GPIO.HIGH  # To detect button press
start_time = datetime.now()
time_data = []
count_data = []

# GUI Window Setup
root = tk.Tk()
root.title("TB PRODUCTION MONITOR")

# Start Time Label
start_time_label = Label(root, text=f"Start Time: {start_time.strftime('%H:%M:%S')}", font=("Arial", 16))
start_time_label.pack()

# Elapsed Time Label
elapsed_time_label = Label(root, text="Elapsed Time: 0s", font=("Arial", 16))
elapsed_time_label.pack()

# Relay State Label
relay_label = Label(root, text="INDEX: STOP", font=("Arial", 16), fg="red")
relay_label.pack()

# Total Count Label
count_label = Label(root, text="Total Count: 0", font=("Arial", 16))
count_label.pack()

# Matplotlib Figure Setup
fig, ax = plt.subplots(figsize=(6, 5))

# Function to update bar graph
def update_graph(frame):
    ax.clear()
    ax.set_xlabel("Hour")
    ax.set_ylabel("Production Count")
    ax.set_title("Production Count Per Hour")
    
    hours = list(counts_per_hour.keys())
    values = list(counts_per_hour.values())
    
    # Assign colors based on count ranges
    colors = []
    for v in values:
        if v < 70:
            colors.append('red')
        elif 71 <= v <= 150:
            colors.append('blue')
        elif 151 <= v <= 250:
            colors.append('green')
        else:
            colors.append('gold')
    
    bars = ax.bar(hours, values, color=colors)
    
    # Add text inside bars
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()/2, str(value), ha='center', va='center', color='white', fontweight='bold')

# Start Matplotlib Animation
ani = animation.FuncAnimation(fig, update_graph, interval=1000)
plt.ion()
plt.show()

# Function to handle button press
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
            
            time.sleep(0.2)  # Debounce delay

        # Detect rising edge (button release)
        elif button_state == GPIO.HIGH and button_previous == GPIO.LOW:
            relay_label.config(text="INDEX: STOP", fg="red")
            GPIO.output(RPin, GPIO.LOW)  # Turn OFF relay
        
        button_previous = button_state  # Update button state
        time.sleep(0.1)  # Small delay

# Run button press detection in a separate thread
button_thread = threading.Thread(target=read_button, daemon=True)
button_thread.start()

# Run the GUI
root.mainloop()

# Cleanup GPIO on exit
GPIO.cleanup()
