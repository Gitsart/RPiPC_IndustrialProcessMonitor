import RPi.GPIO as GPIO
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
counts_per_shift = {}  # Dictionary to store shift-wise counts
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
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 10))  # Two subplots (Bar + Scatter)

# Function to determine shift name
def get_shift(hour):
    if 7 <= hour < 15:
        return "Shift A"
    elif 15 <= hour < 23:
        return "Shift B"
    else:
        return "Shift C"

# Function to update graphs
def update_graph(frame):
    ax1.clear()
    ax2.clear()
    
    # --- Bar Graph: Production Count per Shift ---
    ax1.set_xlabel("Date and Shift")
    ax1.set_ylabel("Production Count")
    ax1.set_title("Production Count Per Shift")
    
    shift_labels = []
    values = []
    colors = []
    
    for key, count in counts_per_shift.items():
        date, shift = key.split(" - ")
        shift_labels.append(f"{date}\n{shift}")
        values.append(count)
        
        # Assign colors based on count range
        if count < 70:
            colors.append("red")
        elif 71 <= count <= 150:
            colors.append("blue")
        elif 151 <= count <= 250:
            colors.append("green")
        else:
            colors.append("gold")
    
    bars = ax1.bar(shift_labels, values, color=colors)
    
    # Add count values inside bars
    for bar, value in zip(bars, values):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height()/2, str(value), 
                 ha='center', va='center', color='white', fontsize=12, fontweight='bold')
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    # --- Scatter Plot: Individual Production Events ---
    ax2.set_xlabel("Time")
    ax2.set_ylabel("Production Event")
    ax2.set_title("Production Events Over Time")
    
    if time_data:
        ax2.scatter(time_data, count_data, color="blue", marker="o", label="Production Event")
        ax2.legend()
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

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
            now = datetime.now()
            date_str = now.strftime("%Y-%m-%d")
            shift = get_shift(now.hour)
            shift_key = f"{date_str} - {shift}"
            
            # Store count per shift
            if shift_key not in counts_per_shift:
                counts_per_shift[shift_key] = 0
            counts_per_shift[shift_key] += 1
            
            # Store individual production events for scatter plot
            time_data.append(now.strftime("%H:%M:%S"))
            count_data.append(count)
            
            print(f"COUNTNUM: {count}")
            relay_label.config(text="INDEX: RUN", fg="green")
            count_label.config(text=f"Total Count: {count}")
            GPIO.output(RPin, GPIO.HIGH)  # Turn ON relay
            
            # Update elapsed time
            elapsed_seconds = int((now - start_time).total_seconds())
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
