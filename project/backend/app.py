from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import numpy as np
import random
import math
import os
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# Simulated traffic data
TRAFFIC_DATA = {
    "current_conditions": {
        "timestamp": datetime.now().isoformat(),
        "congestion_levels": {
            "downtown": 0.75,
            "highways": 0.65,
            "residential": 0.3,
            "commercial": 0.5
        },
        "incidents": [
            {
                "id": 1,
                "type": "accident",
                "location": {"lat": 37.781, "lng": -122.412},
                "severity": "moderate",
                "reported_at": (datetime.now() - timedelta(minutes=15)).isoformat(),
                "description": "Two-vehicle collision, right lane blocked"
            },
            {
                "id": 2,
                "type": "construction",
                "location": {"lat": 37.792, "lng": -122.421},
                "severity": "low",
                "reported_at": (datetime.now() - timedelta(hours=2)).isoformat(),
                "description": "Road work, one lane closed"
            }
        ]
    },
    "historical_data": {
        "congestion_by_hour": {
            "6": 0.3,
            "7": 0.5,
            "8": 0.8,
            "9": 0.7,
            "10": 0.4,
            "11": 0.3,
            "12": 0.4,
            "13": 0.5,
            "14": 0.4,
            "15": 0.5,
            "16": 0.7,
            "17": 0.9,
            "18": 0.8,
            "19": 0.6,
            "20": 0.4
        }
    }
}

# Simple AI model for traffic prediction based on historical data and current conditions
class TrafficPredictionModel:
    def __init__(self):
        # Weights for different factors (would be trained in a real ML model)
        self.time_of_day_weight = 0.4
        self.day_of_week_weight = 0.2
        self.weather_weight = 0.15
        self.incidents_weight = 0.25
        
        # Baseline congestion levels by time (0-23 hours)
        self.baseline_congestion = [
            0.1, 0.05, 0.05, 0.1, 0.2, 0.4,  # 0-5
            0.6, 0.8, 0.9, 0.7, 0.5, 0.6,    # 6-11
            0.7, 0.6, 0.5, 0.6, 0.7, 0.9,    # 12-17
            0.8, 0.6, 0.4, 0.3, 0.2, 0.1     # 18-23
        ]
        
        # Day of week factors (0=Monday, 6=Sunday)
        self.day_factors = [1.0, 1.0, 1.0, 1.0, 1.1, 0.7, 0.6]
        
        # Weather impact factors
        self.weather_impact = {
            "clear": 1.0,
            "cloudy": 1.05,
            "rain": 1.3,
            "snow": 1.8,
            "fog": 1.4,
            "storm": 1.6
        }
    
    def predict_congestion(self, time_of_day, day_of_week, weather, incidents_count):
        # Get baseline congestion for time of day
        base_congestion = self.baseline_congestion[time_of_day]
        
        # Apply day of week factor
        day_factor = self.day_factors[day_of_week]
        
        # Apply weather impact
        weather_factor = self.weather_impact.get(weather, 1.0)
        
        # Calculate incident impact (more incidents = more congestion)
        incident_factor = 1.0 + (incidents_count * 0.1)  # Each incident adds 10% congestion
        
        # Combine factors with weights
        congestion = (
            base_congestion * self.time_of_day_weight +
            base_congestion * day_factor * self.day_of_week_weight +
            base_congestion * weather_factor * self.weather_weight +
            base_congestion * incident_factor * self.incidents_weight
        )
        
        # Ensure congestion is between 0 and 1
        return min(max(congestion, 0.0), 1.0)
    
    def recommend_routes(self, origin, destination, preferences):
        """Generate route recommendations based on traffic predictions"""
        # This would use real routing algorithms and traffic data in production
        # For this demo, we'll generate synthetic routes
        
        # Calculate a direct distance (as the crow flies) between points
        def haversine_distance(lat1, lon1, lat2, lon2):
            R = 6371  # Earth radius in kilometers
            dLat = math.radians(lat2 - lat1)
            dLon = math.radians(lon2 - lon1)
            a = (math.sin(dLat/2) * math.sin(dLat/2) + 
                 math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
                 math.sin(dLon/2) * math.sin(dLon/2))
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            return R * c
        
        direct_distance = haversine_distance(
            origin["lat"], origin["lng"], 
            destination["lat"], destination["lng"]
        )
        
        # Current hour to consider traffic patterns
        current_hour = datetime.now().hour
        current_day = datetime.now().weekday()  # 0=Monday, 6=Sunday
        
        # Count of incidents to factor in
        incidents_count = len(TRAFFIC_DATA["current_conditions"]["incidents"])
        
        # Predict current congestion level
        congestion = self.predict_congestion(
            current_hour, current_day, "clear", incidents_count
        )
        
        # Generate three route options with different characteristics
        routes = []
        
        # Fastest route (slightly longer but less congestion)
        fastest_distance = direct_distance * 1.1
        fastest_congestion = max(congestion * 0.7, 0.1)  # Lower congestion
        fastest_time = (fastest_distance / 60) * (1 + fastest_congestion)  # Base speed 60 km/h
        
        # Shortest route (direct but more congestion)
        shortest_distance = direct_distance
        shortest_congestion = congestion * 1.2  # Higher congestion
        shortest_time = (shortest_distance / 60) * (1 + shortest_congestion)
        
        # Alternative route (longer but least congested)
        alt_distance = direct_distance * 1.3
        alt_congestion = max(congestion * 0.5, 0.1)  # Much lower congestion
        alt_time = (alt_distance / 60) * (1 + alt_congestion)
        
        # Create route paths (for visualization)
        def create_path(start_lat, start_lng, end_lat, end_lng, waypoints=0):
            # Create a simplified path with a few waypoints for visualization
            path = [
                [start_lat, start_lng]
            ]
            
            # Add some waypoints based on a simple interpolation with slight randomness
            for i in range(waypoints):
                progress = (i + 1) / (waypoints + 1)
                lat = start_lat + progress * (end_lat - start_lat) + random.uniform(-0.01, 0.01)
                lng = start_lng + progress * (end_lng - start_lng) + random.uniform(-0.01, 0.01)
                path.append([lat, lng])
                
            path.append([end_lat, end_lng])
            return path
        
        # Create routes with different waypoints for visualization
        routes = [
            {
                "id": 1,
                "name": "Fastest Route",
                "type": "fastest",
                "duration": f"{int(fastest_time * 60)} mins",
                "distance": f"{fastest_distance:.1f} km",
                "congestion": "low" if fastest_congestion < 0.3 else "moderate" if fastest_congestion < 0.7 else "high",
                "path": create_path(
                    origin["lat"], origin["lng"], 
                    destination["lat"], destination["lng"], 
                    waypoints=2
                )
            },
            {
                "id": 2,
                "name": "Shortest Route",
                "type": "shortest",
                "duration": f"{int(shortest_time * 60)} mins",
                "distance": f"{shortest_distance:.1f} km",
                "congestion": "low" if shortest_congestion < 0.3 else "moderate" if shortest_congestion < 0.7 else "high",
                "path": create_path(
                    origin["lat"], origin["lng"], 
                    destination["lat"], destination["lng"], 
                    waypoints=1
                )
            },
            {
                "id": 3,
                "name": "Alternative Route",
                "type": "leastCongested",
                "duration": f"{int(alt_time * 60)} mins",
                "distance": f"{alt_distance:.1f} km",
                "congestion": "low" if alt_congestion < 0.3 else "moderate" if alt_congestion < 0.7 else "high",
                "path": create_path(
                    origin["lat"], origin["lng"], 
                    destination["lat"], destination["lng"], 
                    waypoints=3
                )
            }
        ]
        
        # Filter and sort routes based on user preferences
        if preferences.get("routeType") == "fastest":
            routes.sort(key=lambda r: int(r["duration"].split()[0]))
        elif preferences.get("routeType") == "leastCongested":
            congestion_rank = {"low": 0, "moderate": 1, "high": 2}
            routes.sort(key=lambda r: congestion_rank[r["congestion"]])
        
        if preferences.get("avoidTolls", False):
            # In a real implementation, this would filter out toll roads
            pass
            
        return routes


# Initialize the model
traffic_model = TrafficPredictionModel()

@app.route('/api/traffic/current', methods=['GET'])
def get_current_traffic():
    # Update timestamp to current time
    TRAFFIC_DATA["current_conditions"]["timestamp"] = datetime.now().isoformat()
    return jsonify(TRAFFIC_DATA["current_conditions"])

@app.route('/api/traffic/historical', methods=['GET'])
def get_historical_traffic():
    return jsonify(TRAFFIC_DATA["historical_data"])

@app.route('/api/routes/recommend', methods=['POST'])
def recommend_routes():
    data = request.json
    origin = data.get('origin', {"lat": 37.773, "lng": -122.43})  # Default: San Francisco
    destination = data.get('destination', {"lat": 37.74, "lng": -122.38})
    preferences = data.get('preferences', {})
    
    # Use the AI model to generate recommendations
    routes = traffic_model.recommend_routes(origin, destination, preferences)
    
    return jsonify({
        "routes": routes,
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "traffic_conditions": "moderate"
        }
    })

@app.route('/api/incidents', methods=['GET'])
def get_incidents():
    # Return current traffic incidents
    return jsonify(TRAFFIC_DATA["current_conditions"]["incidents"])

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "version": "1.0.0"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)