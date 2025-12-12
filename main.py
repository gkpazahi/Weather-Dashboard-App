import tkinter as tk
from tkinter import ttk, messagebox
import requests
import os
from PIL import Image, ImageTk
from io import BytesIO
from dotenv import load_dotenv
import threading
from datetime import datetime

# Load environment variables to get the API KEY.
load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")

# open weatherMap url
BASE_URL = "http://api.openweathermap.org/data/2.5/weather"

class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Real-Time Weather App")
        self.root.geometry("700x500")
        self.root.configure(bg="#f0f8ff")
        
        # Center the window
        self.center_window()
        
        # Configure styles
        self.setup_styles()
        
        # Initialize UI
        self.setup_ui()
        
        # Check API key
        if not API_KEY:
            messagebox.showerror("Configuration Error", 
                                "API key not found. Please set OPENWEATHER_API_KEY in .env file")
            self.root.destroy()
    
    def center_window(self):
        """Center the window on the screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_styles(self):
        """Configure widget styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        self.colors = {
            'bg': '#f0f8ff',
            'primary': '#4a90e2',
            'secondary': '#7cb342',
            'accent': '#ff9800',
            'text': '#333333'
        }
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(main_frame, 
                              text="Weather Forecast", 
                              font=("Arial", 24, "bold"),
                              fg=self.colors['primary'],
                              bg=self.colors['bg'])
        title_label.pack(pady=(0, 20))
        
        # Input section
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(input_frame, 
                text="Enter City (e.g., 'London,GB' or 'New York,US'):",
                font=("Arial", 10),
                bg=self.colors['bg']).pack(anchor=tk.W)
        
        self.city_entry = ttk.Entry(input_frame, font=("Arial", 12), width=40)
        self.city_entry.pack(side=tk.LEFT, padx=(0, 10), pady=5)
        self.city_entry.bind('<Return>', lambda e: self.get_weather_threaded())
        
        # Buttons frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)
        
        self.get_weather_btn = ttk.Button(btn_frame, 
                                         text="Get Weather", 
                                         command=self.get_weather_threaded,
                                         style="Accent.TButton")
        self.get_weather_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = ttk.Button(btn_frame, 
                                   text="Clear", 
                                   command=self.clear_display)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Loading indicator
        self.loading_label = tk.Label(main_frame, text="", font=("Arial", 10), bg=self.colors['bg'])
        self.loading_label.pack(pady=5)
        
        # Weather display frame
        self.weather_frame = ttk.LabelFrame(main_frame, text="Weather Information", padding=15)
        self.weather_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Initialize weather labels
        self.setup_weather_labels()
        
        # Add footer with timestamp
        self.timestamp_label = tk.Label(main_frame, 
                                       text="", 
                                       font=("Arial", 8),
                                       fg="#666666",
                                       bg=self.colors['bg'])
        self.timestamp_label.pack(side=tk.BOTTOM, pady=5)
    
    def setup_weather_labels(self):
        """Initialize weather display labels"""
        # City and icon
        self.city_icon_frame = ttk.Frame(self.weather_frame)
        self.city_icon_frame.pack(fill=tk.X, pady=5)
        
        self.city_label = tk.Label(self.city_icon_frame, 
                                  text="", 
                                  font=("Arial", 20, "bold"),
                                  fg=self.colors['primary'])
        self.city_label.pack(side=tk.LEFT)
        
        self.icon_label = tk.Label(self.city_icon_frame)
        self.icon_label.pack(side=tk.LEFT, padx=10)
        
        # Weather details
        details_frame = ttk.Frame(self.weather_frame)
        details_frame.pack(fill=tk.X, pady=10)
        
        self.temp_label = tk.Label(details_frame, 
                                  text="", 
                                  font=("Arial", 16),
                                  fg=self.colors['accent'])
        self.temp_label.pack(anchor=tk.W)
        
        self.feels_like_label = tk.Label(details_frame, 
                                        text="", 
                                        font=("Arial", 10),
                                        fg="#666666")
        self.feels_like_label.pack(anchor=tk.W)
        
        self.humidity_label = tk.Label(details_frame, 
                                      text="", 
                                      font=("Arial", 12))
        self.humidity_label.pack(anchor=tk.W, pady=2)
        
        self.wind_label = tk.Label(details_frame, 
                                  text="", 
                                  font=("Arial", 12))
        self.wind_label.pack(anchor=tk.W, pady=2)
        
        self.desc_label = tk.Label(details_frame, 
                                  text="", 
                                  font=("Arial", 14, "italic"))
        self.desc_label.pack(anchor=tk.W, pady=5)
        
        self.error_label = tk.Label(self.weather_frame, 
                                   text="", 
                                   font=("Arial", 12),
                                   fg="red")
        self.error_label.pack()
    
    def show_loading(self, show=True):
        """Show or hide loading indicator"""
        if show:
            self.loading_label.config(text="Fetching weather data...")
            self.get_weather_btn.config(state=tk.DISABLED)
            self.clear_btn.config(state=tk.DISABLED)
        else:
            self.loading_label.config(text="")
            self.get_weather_btn.config(state=tk.NORMAL)
            self.clear_btn.config(state=tk.NORMAL)
    
    def get_weather_threaded(self):
        """Fetch weather data in a separate thread"""
        city = self.city_entry.get().strip()
        
        if not city:
            messagebox.showwarning("Input Required", 
                                  "Please enter a city name (e.g., 'London,GB')")
            return
        
        self.show_loading()
        thread = threading.Thread(target=self.fetch_weather, args=(city,), daemon=True)
        thread.start()
    
    def fetch_weather(self, city):
        """Fetch weather data from API"""
        try:
            params = {
                "q": city,
                "appid": API_KEY,
                "units": "metric"
            }
            
            response = requests.get(BASE_URL, params=params, timeout=10)
            data = response.json()
            
            # Schedule UI update on main thread
            self.root.after(0, self.update_weather_display, data)
            
        except requests.exceptions.Timeout:
            self.root.after(0, self.show_error, "Request timed out. Please try again.")
        except requests.exceptions.ConnectionError:
            self.root.after(0, self.show_error, "Network error. Please check your connection.")
        except Exception as e:
            self.root.after(0, self.show_error, f"An error occurred: {str(e)}")
        finally:
            self.root.after(0, self.show_loading, False)
    
    def update_weather_display(self, data):
        """Update UI with weather data"""
        if data.get("cod") != 200:
            self.show_error(data.get("message", "City not found"))
            return
        
        try:
            # Extract weather data
            weather_info = {
                "city": data["name"],
                "country": data["sys"]["country"],
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "humidity": data["main"]["humidity"],
                "pressure": data["main"]["pressure"],
                "wind_speed": data["wind"]["speed"],
                "wind_deg": data["wind"].get("deg", 0),
                "description": data["weather"][0]["description"],
                "icon": data["weather"][0]["icon"]
            }
            
            # Update labels
            self.city_label.config(text=f"{weather_info['city']}, {weather_info['country']}")
            self.temp_label.config(text=f"🌡 Temperature: {weather_info['temperature']:.1f}°C")
            self.feels_like_label.config(text=f"(Feels like: {weather_info['feels_like']:.1f}°C)")
            self.humidity_label.config(text=f"💧 Humidity: {weather_info['humidity']}%")
            self.wind_label.config(text=f"💨 Wind: {weather_info['wind_speed']} m/s")
            self.desc_label.config(text=f"{weather_info['description'].title()}")
            
            # Load and display weather icon
            self.load_weather_icon(weather_info['icon'])
            
            # Update timestamp
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.timestamp_label.config(text=f"Last updated: {current_time}")
            
            # Clear error if any
            self.error_label.config(text="")
            
        except KeyError as e:
            self.show_error(f"Unexpected API response format. Missing key: {e}")
    
    def load_weather_icon(self, icon_code):
        """Load and display weather icon"""
        try:
            icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
            response = requests.get(icon_url, timeout=5)
            img_data = Image.open(BytesIO(response.content))
            img_data = img_data.resize((100, 100), Image.Resampling.LANCZOS)
            icon_image = ImageTk.PhotoImage(img_data)
            
            self.icon_label.config(image=icon_image)
            self.icon_label.image = icon_image  # Keep reference
            
        except Exception:
            # If icon fails to load, just remove any existing icon
            self.icon_label.config(image="")
    
    def show_error(self, message):
        """Display error message"""
        self.error_label.config(text=f"Error: {message}")
        self.clear_weather_display()
    
    def clear_weather_display(self):
        """Clear weather display fields"""
        self.city_label.config(text="")
        self.temp_label.config(text="")
        self.feels_like_label.config(text="")
        self.humidity_label.config(text="")
        self.wind_label.config(text="")
        self.desc_label.config(text="")
        self.icon_label.config(image="")
        self.timestamp_label.config(text="")
    
    def clear_display(self):
        """Clear all inputs and display"""
        self.city_entry.delete(0, tk.END)
        self.clear_weather_display()
        self.error_label.config(text="")
        self.city_entry.focus()

def main():
    """Main application entry point"""
    root = tk.Tk()
    
    # Set window icon (optional - add an icon file)
    try:
        root.iconbitmap('weather.ico')
    except:
        pass
    
    app = WeatherApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()