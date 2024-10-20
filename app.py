import requests
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_KEY = os.getenv("API_KEY")
CITIES = ["Delhi", "Mumbai", "Chennai", "Bangalore", "Kolkata", "Hyderabad"]
DAYS = 4  # Forecast for the next 5 days
time_interval = 300 #call again after 5 minutes

class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Weather Monitoring System")
        self.root.attributes('-fullscreen', True)  # Adjusted height for the new dropdown

        # Database setup
        self.conn = sqlite3.connect('weather_data.db')
        self.create_table()

        # City Selection
        tk.Label(root, text="Select City:").pack(pady=10)
        self.city_combobox = ttk.Combobox(root, values=CITIES)
        self.city_combobox.pack(pady=10)

        # Date Selection
        tk.Label(root, text="Select Date:").pack(pady=10)
        self.date_combobox = ttk.Combobox(root)
        self.date_combobox.pack(pady=10)

        # Temperature Unit Selection
        tk.Label(root, text="Select Temperature Unit:").pack(pady=10)
        self.temp_unit_combobox = ttk.Combobox(root, values=["Celsius", "Kelvin"])
        self.temp_unit_combobox.pack(pady=10)
        self.temp_unit_combobox.current(0)  # Default to Celsius

        # Thresholds for alerts
        tk.Label(root, text="Temperature Alert Threshold:").pack(pady=10)
        self.temp_threshold_entry = tk.Entry(root)
        self.temp_threshold_entry.pack(pady=10)

        tk.Label(root, text="Humidity Alert Threshold:").pack(pady=10)
        self.humidity_threshold_entry = tk.Entry(root)
        self.humidity_threshold_entry.pack(pady=10)

        tk.Label(root, text="Wind Speed Alert Threshold:").pack(pady=10)
        self.wind_speed_threshold_entry = tk.Entry(root)
        self.wind_speed_threshold_entry.pack(pady=10)

        # Weather Information Display
        self.weather_info = tk.Text(root, height=10, width=50)
        self.weather_info.pack(pady=20)

        # Fetch Weather Button
        fetch_weather_button = tk.Button(root, text="Fetch Weather", command=self.fetch_weather)
        fetch_weather_button.pack(pady=10)

        # Fetch Humidity and Wind Speed Button
        fetch_humidity_wind_button = tk.Button(root, text="Fetch Humidity & Wind Speed", command=self.fetch_humidity_and_wind)
        fetch_humidity_wind_button.pack(pady=10)

        # Populate date dropdown
        self.populate_dates()

        # Event binding for city selection
        self.city_combobox.bind("<<ComboboxSelected>>", self.populate_dates)

    def create_table(self):
        """Create a table for storing weather summaries if it doesn't exist."""
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS weather_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    city TEXT,
                    date TEXT,
                    main_weather TEXT,
                    current_temp REAL,
                    feels_like REAL,
                    avg_temp REAL,
                    min_temp REAL,
                    max_temp REAL,
                    update_time TEXT
                )
            ''')

    def populate_dates(self, event=None):
        """Populate the date dropdown with the next few days."""
        selected_city = self.city_combobox.get()
        if selected_city:
            self.date_combobox['values'] = [(datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(DAYS + 1)]
            self.date_combobox.current(0)  # Select the first date by default

    def fetch_weather(self):
        """Fetch weather data based on the selected city and date."""
        city = self.city_combobox.get()
        selected_date = self.date_combobox.get()
        
        if not city:
            messagebox.showwarning("Warning", "Please select a city!")
            return
        
        # Fetch the current weather data
        response_current = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}")

        if response_current.ok:
            data_current = response_current.json()
            self.display_weather(data_current, selected_date, city)  # Pass city name
        else:
            messagebox.showerror("Error", "Failed to fetch weather data.")

    def fetch_humidity_and_wind(self):
        """Fetch humidity and wind speed data based on the selected city and date."""
        city = self.city_combobox.get()
        selected_date = self.date_combobox.get()

        if not city:
            messagebox.showwarning("Warning", "Please select a city!")
            return

        # Fetch the current weather data
        response_current = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}")

        if response_current.ok:
            data_current = response_current.json()
            self.display_humidity_and_wind(data_current, selected_date, city)
        else:
            messagebox.showerror("Error", "Failed to fetch weather data.")

    def display_weather(self, data, selected_date, city):
        """Display the weather data in the text widget and plot graphs."""
        self.weather_info.delete(1.0, tk.END)  # Clear previous data

        times = []
        temperatures = []
        temp_unit = self.temp_unit_combobox.get()

        # Initialize variables for main weather and feels-like temperature
        main_weather = None
        feels_like_temp = None
        update_time = None

        # Collect data for the selected date
        for entry in data['list']:
            dt_txt = entry['dt_txt']
            date = dt_txt.split(" ")[0]  # Get date only
            if date == selected_date:
                time = dt_txt.split(" ")[1]
                times.append(time)

                # Extract weather data
                if main_weather is None:
                    main_weather = entry['weather'][0]['main']  # Main weather condition
                    update_time = entry['dt']  # Time of the data update (Unix timestamp)

                # Convert from Kelvin to the selected unit
                temp_kelvin = entry['main']['temp']
                if temp_unit == "Celsius":
                    temp_celsius = temp_kelvin - 273.15
                    temperatures.append(temp_celsius)
                    if feels_like_temp is None:
                        feels_like_kelvin = entry['main']['feels_like']  # Perceived temperature in Kelvin
                        feels_like_temp = feels_like_kelvin - 273.15
                else:  # Kelvin
                    temperatures.append(temp_kelvin)
                    if feels_like_temp is None:
                        feels_like_temp = entry['main']['feels_like']  # Perceived temperature in Kelvin

        # Calculate min and max temperatures from the collected temperatures
        min_temp = min(temperatures) if temperatures else 0
        max_temp = max(temperatures) if temperatures else 0
        avg_temp = (min_temp + max_temp) / 2 if temperatures else 0

        # Convert update time from Unix timestamp to a readable format
        update_time_str = datetime.fromtimestamp(update_time).strftime('%Y-%m-%d %H:%M:%S')

        # Store summary in the database
        self.store_weather_summary(city, selected_date, main_weather, temperatures[0], feels_like_temp, avg_temp, min_temp, max_temp, update_time_str)

        # Display weather data
        self.weather_info.insert(tk.END, f"City: {city}\n")  # Display city name
        self.weather_info.insert(tk.END, f"Main Weather: {main_weather}\n")
        self.weather_info.insert(tk.END, f"Current Temperature: {temperatures[0]:.2f}°{temp_unit[0]}\n")  # Use the first temperature
        self.weather_info.insert(tk.END, f"Feels Like: {feels_like_temp:.2f}°{temp_unit[0]}\n")
        self.weather_info.insert(tk.END, f"Last Updated: {update_time_str}\n")
        self.weather_info.insert(tk.END, f"Selected Date: {selected_date}\n")
        self.weather_info.insert(tk.END, f"Avg Temperature: {avg_temp:.2f}°{temp_unit[0]}\n")
        self.weather_info.insert(tk.END, f"Min Temperature: {min_temp:.2f}°{temp_unit[0]}\n")
        self.weather_info.insert(tk.END, f"Max Temperature: {max_temp:.2f}°{temp_unit[0]}\n")

        # Check against thresholds
        self.check_alerts(temperatures[0], feels_like_temp)

        # Print to console with city name
        print(f"City: {city}, Date: {selected_date}, Main Weather: {main_weather}, Current Temperature: {temperatures[0]:.2f}°{temp_unit[0]}, Feels Like: {feels_like_temp:.2f}°{temp_unit[0]}")

        # Plot the data
        self.plot_weather_graphs(times, temperatures, min_temp, max_temp, avg_temp, temp_unit)

    def display_humidity_and_wind(self, data, selected_date, city):
        """Display humidity and wind speed for the entire day."""
        times = []
        humidities = []
        wind_speeds = []

        # Collect humidity and wind speed for each time entry on the selected date
        for entry in data['list']:
            dt_txt = entry['dt_txt']
            date = dt_txt.split(" ")[0]  # Extract the date portion
            time = dt_txt.split(" ")[1]  # Extract the time portion
            
            if date == selected_date:
                times.append(time)  # Collect all times for the selected date
                humidities.append(entry['main']['humidity'])  # Collect humidity values
                wind_speeds.append(entry['wind']['speed'])  # Collect wind speed values

        # Display humidity and wind speed if data is available
        if humidities and wind_speeds:
        # Print the first entry's humidity and wind speed
            print(f"City: {city}, Date: {selected_date}")
            print(f"First Entry - Time: {times[0]}, Humidity: {humidities[0]}%, Wind Speed: {wind_speeds[0]:.2f} m/s")
        
        # Print summary data like average, max, min
            print(f"Average Humidity: {sum(humidities) / len(humidities):.2f}%, "
              f"Average Wind Speed: {sum(wind_speeds) / len(wind_speeds):.2f} m/s")
            print(f"Max Humidity: {max(humidities)}%, Max Wind Speed: {max(wind_speeds):.2f} m/s")
            print(f"Min Humidity: {min(humidities)}%, Min Wind Speed: {min(wind_speeds):.2f} m/s")
            self.weather_info.insert(tk.END, f"Humidity: {humidities[0]}% at {times[0]}\n")  # Example display for the first entry
            self.weather_info.insert(tk.END, f"Wind Speed: {wind_speeds[0]} m/s at {times[0]}\n")

            # Check against thresholds (optional)
            self.check_alerts(None, None, humidities[0], wind_speeds[0])

            # Plot graphs for the whole day
            self.plot_humidity_and_wind_graphs(times, humidities, wind_speeds)
        else:
            messagebox.showwarning("Warning", "No humidity or wind data available for the selected date.")


    def check_alerts(self, current_temp, feels_like_temp, humidity=None, wind_speed=None):
        """Check for threshold alerts and show a message box if thresholds are exceeded."""
        temp_threshold = self.temp_threshold_entry.get()
        humidity_threshold = self.humidity_threshold_entry.get()
        wind_speed_threshold = self.wind_speed_threshold_entry.get()

        # Check temperature thresholds
        if temp_threshold and current_temp is not None:
            try:
                if current_temp > float(temp_threshold):
                    self.root.after(0, lambda: messagebox.showinfo("Temperature Alert", f"Current temperature {current_temp:.2f} exceeds the threshold of {temp_threshold}°!"))
                if feels_like_temp > float(temp_threshold):
                    self.root.after(0, lambda: messagebox.showinfo("Feels Like Alert", f"Feels like temperature {feels_like_temp:.2f} exceeds the threshold of {temp_threshold}°!"))
            except ValueError:
                self.root.after(0, lambda: messagebox.showwarning("Warning", "Invalid temperature threshold entered!"))

        # Check humidity threshold
        if humidity_threshold and humidity is not None:
            try:
                if humidity > float(humidity_threshold):
                    self.root.after(0, lambda: messagebox.showinfo("Humidity Alert", f"Humidity {humidity}% exceeds the threshold of {humidity_threshold}%!"))
            except ValueError:
                self.root.after(0, lambda: messagebox.showwarning("Warning", "Invalid humidity threshold entered!"))

        # Check wind speed threshold
        if wind_speed_threshold and wind_speed is not None:
            try:
                if wind_speed > float(wind_speed_threshold):
                    self.root.after(0, lambda: messagebox.showinfo("Wind Speed Alert", f"Wind speed {wind_speed} m/s exceeds the threshold of {wind_speed_threshold} m/s!"))
            except ValueError:
                self.root.after(0, lambda: messagebox.showwarning("Warning", "Invalid wind speed threshold entered!"))


    def plot_weather_graphs(self, times, temperatures, min_temp, max_temp, avg_temp, temp_unit):
        """Plot graphs for temperature."""
        plt.figure(figsize=(10, 5))

        # Temperature plot
        plt.plot(times, temperatures, label='Temperature', color='blue')
        plt.axhline(y=min_temp, color='green', linestyle='--', label='Min Temperature')
        plt.axhline(y=max_temp, color='red', linestyle='--', label='Max Temperature')
        plt.axhline(y=avg_temp, color='orange', linestyle='--', label='Avg Temperature')

        plt.title("Temperature Over Time")
        plt.xlabel("Time")
        plt.ylabel(f"Temperature (°{temp_unit[0]})")
        plt.xticks(rotation=45)
        plt.legend()
        plt.tight_layout()
        plt.show()
    
    def plot_humidity_and_wind_graphs(self, times, humidities, wind_speeds):
        """Plot graphs for humidity and wind speed."""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

        # Humidity plot
        ax1.plot(times, humidities, label='Humidity', color='blue')
        ax1.set_title("Humidity Over Time")
        ax1.set_xlabel("Time")
        ax1.set_ylabel("Humidity (%)")
        ax1.legend()
        ax1.grid(True)

        # Wind Speed plot
        ax2.plot(times, wind_speeds, label='Wind Speed', color='orange')
        ax2.set_title("Wind Speed Over Time")
        ax2.set_xlabel("Time")
        ax2.set_ylabel("Wind Speed (m/s)")
        ax2.legend()
        ax2.grid(True)

        plt.tight_layout()
        plt.show()

    def store_weather_summary(self, city, selected_date, main_weather, current_temp, feels_like_temp, avg_temp, min_temp, max_temp, update_time):
        """Store weather summary in the database."""
        with self.conn:
            self.conn.execute('''
                INSERT INTO weather_summary (city, date, main_weather, current_temp, feels_like, avg_temp, min_temp, max_temp, update_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (city, selected_date, main_weather, current_temp, feels_like_temp, avg_temp, min_temp, max_temp, update_time))

    def run(self):
        """Start the GUI main loop."""
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherApp(root)
    app.run()
