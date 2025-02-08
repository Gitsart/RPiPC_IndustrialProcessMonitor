import RPi.GPIO as GPIO
import time
import tkinter as tk
from tkinter import Label
import threading
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from datetime import datetime

# Define GPIO pins
RELAY_PIN = 14  # GPIO14 for the relay
BUTTON_PIN = 15  # GPIO15 for the button

# Set up GPIO
GPIO.setmode(GPIO.BCM)  
GPIO.setup(RELAY_PIN, GPIO.OUT)  # Set relay as output
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Set pull-up resistor

# Variables
count = 0  # Total button presses
hourly_count = 0  # Count for the current hour
counts_per_hour = {}  # Dictionary to store hourly counts
button_previous = GPIO.HIGH  # To detect button press
start_time = time.time()
time_data = []
count_data = []

# GUI Window Setup
root = tk.Tk()
root.title("Relay Monitor")

# Relay State Label
relay_label = Label(root, text="Relay: OFF", font=("Arial", 16), fg="red")
relay_label.pack()

# Total Count Label
count_label = Label(root, text="Total Count: 0", font=("Arial", 16))
count_label.pack()

# Hourly Count Label
hourly_label = Label(root, text="Count This Hour: 0", font=("Arial", 16))
hourly_label.pack()
 
# Matplotlib Figure Setup
fig, ax = plt.subplots()
ax.set_xlabel("Time (Hours)")
ax.set_ylabel("Total Count")
ax.set_title("Real-Time Button Press Count")

# Function to update graph
def update_graph(frame):
    ax.clear()
    ax.set_xlabel("Time (Hours)")
    ax.set_ylabel("Total Count")
    ax.set_title("Real-Time Button Press Count")
    ax.plot(time_data, count_data, marker='o', linestyle='-')

# Start Matplotlib Animation
ani = animation.FuncAnimation(fig, update_graph, interval=1000)
plt.ion()
plt.show()

# Function to handle button press
def read_button():
    global count, hourly_count, button_previous, start_time, time_data, count_data

    while True:
        button_state = GPIO.input(BUTTON_PIN)
        
        # Detect falling edge (button press)
        if button_state == GPIO.LOW and button_previous == GPIO.HIGH:
            count += 1  # Increment count
            hourly_count += 1  # Increment hourly count
            current_hour = datetime.now().strftime("%H:%M")  # Get current hour

            # Store count per hour
            if current_hour not in counts_per_hour:
                counts_per_hour[current_hour] = 0
            counts_per_hour[current_hour] += 1

            print(f"COUNTNUM: {count}")
            relay_label.config(text="Relay: ON", fg="green")
            count_label.config(text=f"Total Count: {count}")
            hourly_label.config(text=f"Count This Hour: {hourly_count}")
            GPIO.output(RELAY_PIN, GPIO.HIGH)  # Turn ON relay
            
            # Append data for plotting
            elapsed_time = (time.time() - start_time) / 3600  # Convert to hours
            time_data.append(elapsed_time)
            count_data.append(count)

            time.sleep(0.2)  # Debounce delay

        # Detect rising edge (button release)
        elif button_state == GPIO.HIGH and button_previous == GPIO.LOW:
            relay_label.config(text="Relay: OFF", fg="red")
            GPIO.output(RELAY_PIN, GPIO.LOW)  # Turn OFF relay
        
        button_previous = button_state  # Update button state
        time.sleep(0.1)  # Small delay

# Run button press detection in a separate thread
button_thread = threading.Thread(target=read_button, daemon=True)
button_thread.start()

# Run the GUI
root.mainloop()

# Cleanup GPIO on exit
GPIO.cleanup()
