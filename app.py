import os
import requests
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from urllib.parse import quote

app = Flask(__name__)
CORS(app)  # This enables CORS for all routes so your friend's frontend can connect

def fetch_city_data_live(city_name):
    places = []
    try:
        api_key = "2f216ba3bd304e0ab20e594df5d49186"
        
        # 1. Get coordinates for the city
        geo_url = f"https://api.geoapify.com/v1/geocode/search?text={quote(city_name)}&apiKey={api_key}"
        geo_res = requests.get(geo_url, timeout=10)
        
        if geo_res.status_code == 200:
            features = geo_res.json().get("features", [])
            if features:
                coords = features[0]["geometry"]["coordinates"]
                lon, lat = coords[0], coords[1]
                
                # 2. Fetch all requested categories near those coordinates
                categories_list = (
                    "tourism.attraction,"
                    "catering.restaurant,"
                    "catering.cafe,"
                    "healthcare.hospital,"
                    "healthcare.pharmacy,"
                    "public_transit.bus,"
                    "leisure.park"
                )
                
                places_url = f"https://api.geoapify.com/v2/places?categories={categories_list}&filter=circle:{lon},{lat},10000&limit=50&apiKey={api_key}"
                p_res = requests.get(places_url, timeout=10)
                
                if p_res.status_code == 200:
                    for item in p_res.json().get("features", []):
                        props = item.get("properties", {})
                        name = props.get("name")
                        cats = props.get("categories", [])
                        
                        if name:
                            # Assign the correct place_type based on Geoapify categories
                            place_type = "attraction"
                            if any("catering.restaurant" in c for c in cats):
                                place_type = "restaurant"
                            elif any("catering.cafe" in c for c in cats):
                                place_type = "cafe"
                            elif any("healthcare.hospital" in c for c in cats):
                                place_type = "hospital"
                            elif any("healthcare.pharmacy" in c for c in cats):
                                place_type = "medical"
                            elif any("public_transit.bus" in c for c in cats):
                                place_type = "bus stop"
                            elif any("leisure.park" in c for c in cats):
                                place_type = "park"
                                
                            places.append({"name": name, "place_type": place_type})
    except Exception as e:
        print(f"Error: {e}")
        
    return places   
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Live India Travel Guide</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f8f9fa; color: #333; padding: 20px; text-align: center; }
        h1 { color: #2c3e50; }
        .search-box { margin: 20px auto; }
        input[type="text"] { padding: 10px; width: 300px; font-size: 16px; border: 1px solid #ccc; border-radius: 4px; }
        button { padding: 10px 20px; font-size: 16px; background: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #2980b9; }
        ul { list-style: none; padding: 0; max-width: 400px; margin: 20px auto; text-align: left; }
        li { background: white; padding: 10px 15px; margin-bottom: 8px; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
</head>
<body>
    <h1>Live India Travel Finder</h1>
    <p>Search any city in India to pull live tourist spots instantly</p>
    
    <div class="search-box">
        <form method="GET" action="/">
            <input type="text" name="city" placeholder="e.g., Mumbai, Delhi, Jaipur, Pune..." value="{{ city }}">
            <button type="submit">Search Live</button>
        </form>
    </div>

    <div>
        {% if places %}
            <h3>Top Attractions in {{ city }}:</h3>
            <ul>
                {% for place in places %}
                    <li><strong>{{ place.name }}</strong> ({{ place.place_type }})</li>
                {% endfor %}
            </ul>
        {% elif city %}
            <p>No spots found for "{{ city }}". Try another city!</p>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def home():
    city = request.args.get("city", "").strip()
    places = []
    if city:
        places = fetch_city_data_live(city)
    return render_template_string(HTML_TEMPLATE, places=places, city=city)

@app.route("/api/travel", methods=["GET", "POST"])
def api_travel():
    city = request.args.get("city")
    if not city and request.is_json:
        data = request.get_json()
        city = data.get("city")
    
    if not city:
        city = "Mumbai"

    spots = fetch_city_data_live(city)

    return jsonify({
        "city": city,
        "spots": spots
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)