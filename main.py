from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.utils import platform
from kivy.properties import StringProperty
import requests
import json
import datetime

# For Android permissions
if platform == 'android':
    from android.permissions import request_permissions, Permission
    from android.permissions import check_permission

# Firebase configuration - Replace with your own Firebase details
FIREBASE_URL = "https://tracker-55edb-default-rtdb.asia-southeast1.firebasedatabase.app/path/to/data.json"

class GPSHelper:
    def __init__(self, on_location_update=None):
        self.on_location_update = on_location_update
        self.gps = None
        
    def start(self):
        if platform == 'android':
            from plyer import gps
            self.gps = gps
            self.gps.configure(on_location=self._on_location)
            self.gps.start(minTime=1000, minDistance=1)  # Update every 1 second or 1 meter
        else:
            # For testing on non-Android platforms
            Clock.schedule_interval(self._mock_location_update, 3)
    
    def stop(self):
        if platform == 'android':
            self.gps.stop()
        else:
            Clock.unschedule(self._mock_location_update)
    
    def _on_location(self, **kwargs):
        if self.on_location_update and 'lat' in kwargs and 'lon' in kwargs:
            self.on_location_update(kwargs['lat'], kwargs['lon'])
    
    def _mock_location_update(self, dt):
        # Mock location for testing on non-Android platforms
        import random
        lat = 37.7749 + (random.random() - 0.5) * 0.01
        lon = -122.4194 + (random.random() - 0.5) * 0.01
        if self.on_location_update:
            self.on_location_update(lat, lon)

class BusTracker(BoxLayout):
    location_text = StringProperty("Waiting for location...")
    status_text = StringProperty("Tracking: OFF")
    
    def __init__(self, **kwargs):
        super(BusTracker, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 10
        
        # Title
        self.add_widget(Label(text='Bus GPS Tracker', font_size=24, size_hint_y=None, height=50))
        
        # Location display
        self.location_label = Label(text=self.location_text, font_size=18)
        self.add_widget(self.location_label)
        
        # Status display
        self.status_label = Label(text=self.status_text, font_size=18)
        self.add_widget(self.status_label)
        
        # Start/Stop button
        self.tracking_button = Button(text='Start Tracking', size_hint_y=None, height=60)
        self.tracking_button.bind(on_press=self.toggle_tracking)
        self.add_widget(self.tracking_button)
        
        # Initialize GPS helper
        self.gps_helper = GPSHelper(on_location_update=self.update_location)
        self.tracking = False
        
        # Request permissions if on Android
        if platform == 'android':
            self.request_android_permissions()
    
    def request_android_permissions(self):
        if platform == 'android':
            if not check_permission(Permission.ACCESS_FINE_LOCATION):
                request_permissions([
                    Permission.ACCESS_FINE_LOCATION,
                    Permission.ACCESS_COARSE_LOCATION
                ])
    
    def toggle_tracking(self, instance):
        if not self.tracking:
            # Start tracking
            self.tracking = True
            self.tracking_button.text = 'Stop Tracking'
            self.status_text = "Tracking: ON"
            self.status_label.text = self.status_text
            self.gps_helper.start()
        else:
            # Stop tracking
            self.tracking = False
            self.tracking_button.text = 'Start Tracking'
            self.status_text = "Tracking: OFF"
            self.status_label.text = self.status_text
            self.gps_helper.stop()
    
    def update_location(self, lat, lon):
        # Update UI with new location
        self.location_text = f"Location: {lat:.6f}, {lon:.6f}"
        self.location_label.text = self.location_text
        
        # Send data to database
        self.send_location_to_database(lat, lon)
    
    def send_location_to_database(self, lat, lon):
        try:
            # Create location data with timestamp
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            location_data = {
                "latitude": lat,
                "longitude": lon,
                "timestamp": timestamp,
                "bus_id": "bus_001"  # You can make this configurable
            }
            
            # Send data to Firebase
            response = requests.post(FIREBASE_URL, data=json.dumps(location_data))
            
            if response.status_code == 200:
                print("Location data sent successfully")
            else:
                print(f"Failed to send location data: {response.status_code}")
        except Exception as e:
            print(f"Error sending location data: {e}")

class BusTrackerApp(App):
    def build(self):
        return BusTracker()

if __name__ == '__main__':
    BusTrackerApp().run()