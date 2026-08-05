import os
import requests
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from urllib.parse import quote
from dotenv import load_dotenv
from deep_translator import GoogleTranslator

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)


def fetch_city_data_live(city_name, category="tourism.attraction"):
    places = []

    try:
        api_key = "2f216ba3bd304e0ab20e594df5d49186"

        # Step 1: Get city coordinates (English)
        geo_url = (
            f"https://api.geoapify.com/v1/geocode/search?text={quote(city_name)}&limit=1&lang=en&apiKey={api_key}"
        )

        geo_res = requests.get(geo_url, timeout=10)
        data = geo_res.json()
        features = data.get("features", [])

        if not features:
            return []

        lon, lat = features[0]["geometry"]["coordinates"]

        # Step 2: Get nearby places
        places_url = (
            f"https://api.geoapify.com/v2/places?categories={category}"
            f"&filter=circle:{lon},{lat},20000"
            f"&limit=20&lang=en&apiKey={api_key}"
        )

        p_res = requests.get(places_url, timeout=10)
        pdata = p_res.json()

        for item in pdata.get("features", []):
            props = item.get("properties", {})

            name = props.get("name")
            address = props.get("formatted")
            plat = props.get("lat")
            plon = props.get("lon")

            # Translate name to English if needed
            if name:
                try:
                    translated_name = GoogleTranslator(
                        source="auto", target="en"
                    ).translate(name)
                except:
                    translated_name = name

                places.append({
                    "name": translated_name,
                    "original_name": name,
                    "place_type": category,
                    "address": address,
                    "lat": plat,
                    "lon": plon
                })

    except Exception as e:
        print("ERROR:", e)

    return places


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Live India Places Finder</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f5f7fa;
            text-align: center;
            padding: 40px;
        }
        input, select {
            padding: 10px;
            width: 250px;
            margin: 5px;
        }
        button {
            padding: 10px 18px;
            background: #007bff;
            color: white;
            border: none;
            cursor: pointer;
        }
        ul {
            list-style: none;
            padding: 0;
            max-width: 500px;
            margin: 20px auto;
            text-align: left;
        }
        li {
            background: white;
            margin-bottom: 8px;
            padding: 12px;
            border-radius: 6px;
        }
        small {
            color: #666;
        }
    </style>
</head>
<body>

    <h1>Live India Places Finder</h1>

    <form method="GET" action="/">
        <input type="text" name="city" placeholder="Enter city" value="{{ city }}">

        <select name="category">
            <option value="tourism.attraction" {% if category == 'tourism.attraction' %}selected{% endif %}>Tourist Attractions</option>
            <option value="catering.cafe" {% if category == 'catering.cafe' %}selected{% endif %}>Cafes</option>
            <option value="catering.restaurant" {% if category == 'catering.restaurant' %}selected{% endif %}>Restaurants</option>
            <option value="healthcare.hospital" {% if category == 'healthcare.hospital' %}selected{% endif %}>Hospitals</option>
        </select>

        <button type="submit">Search</button>
    </form>

    {% if places %}
        <h2>Results for {{ city }}</h2>
        <ul>
            {% for place in places %}
                <li>
                    <b>{{ place.name }}</b>

                    {% if place.original_name != place.name %}
                        <br><small>Original: {{ place.original_name }}</small>
                    {% endif %}

                    <br>({{ place.place_type }})
                </li>
            {% endfor %}
        </ul>
    {% elif city %}
        <p>No places found for "{{ city }}"</p>
    {% endif %}

</body>
</html>
"""


@app.route("/")
def home():
    city = request.args.get("city", "").strip()
    category = request.args.get("category", "tourism.attraction")

    places = fetch_city_data_live(city, category) if city else []

    return render_template_string(
        HTML_TEMPLATE,
        city=city,
        category=category,
        places=places
    )


# API endpoint
@app.route("/api/places", methods=["GET", "POST"])
def api_places():
    city = request.args.get("city")
    category = request.args.get("category", "tourism.attraction")

    if not city and request.is_json:
        city = request.json.get("city")
        category = request.json.get("category", "tourism.attraction")

    if not city:
        city = "Mumbai"

    spots = fetch_city_data_live(city, category)

    return jsonify({
        "city": city,
        "category": category,
        "spots": spots
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)





















































































































































