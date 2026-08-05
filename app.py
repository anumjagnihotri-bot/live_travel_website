import os
import requests
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from urllib.parse import quote
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)


def fetch_city_data_live(city_name, category="tourism.attraction"):
    """Fetch places around a city using Geoapify APIs."""
    places = []
    try:
        api_key = "2f216ba3bd304e0ab20e594df5d49186"

        # Step 1: Get city coordinates
        geo_url = (
            f"https://api.geoapify.com/v1/geocode/search?text={quote(city_name)}&limit=1&apiKey={api_key}"
        )
        geo_res = requests.get(geo_url, timeout=10)
        data = geo_res.json()
        features = data.get("features", [])
        if not features:
            return []

        lon, lat = features[0]["geometry"]["coordinates"]

        # Step 2: Get nearby places based on category
        places_url = (
            f"https://api.geoapify.com/v2/places?categories={category}"
            f"&filter=circle:{lon},{lat},20000"
            f"&limit=20&apiKey={api_key}"
        )
        p_res = requests.get(places_url, timeout=10)
        pdata = p_res.json()

        for item in pdata.get("features", []):
            props = item.get("properties", {})
            name = props.get("name")
            address = props.get("formatted")
            plat = props.get("lat")
            plon = props.get("lon")
            if name:
                places.append(
                    {
                        "name": name,
                        "place_type": category,
                        "address": address,
                        "lat": plat,
                        "lon": plon,
                    }
                )
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
    body { font-family: Arial, sans-serif; background: #f5f7fa; text-align: center; padding: 40px; }
    input, select { padding: 10px; width: 250px; margin: 5px; }
    button { padding: 10px 18px; background: #007bff; color: white; border: none; cursor: pointer; }
    ul { list-style: none; padding: 0; max-width: 600px; margin: 20px auto; text-align: left; }
    li { background: white; margin-bottom: 8px; padding: 10px; border-radius: 6px; }
  </style>
</head>
<body>
  <h1>Live India Places Finder</h1>
  <form id="searchForm">
    <input type="text" name="city" id="city" placeholder="Enter city name" required />
    <select name="category" id="category">
      <option value="tourism.attraction">Attractions</option>
      <option value="accommodation.hotel">Hotels</option>
      <option value="food_and_drink">Food & Drink</option>
      <option value="shopping">Shopping</option>
    </select>
    <button type="submit">Search</button>
  </form>

  <ul id="results"></ul>

  <script>
    const form = document.getElementById('searchForm');
    const results = document.getElementById('results');

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      results.innerHTML = '<li>Searching...</li>';
      const city = document.getElementById('city').value;
      const category = document.getElementById('category').value;

      try {
        const res = await fetch('/search', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ city, category }),
        });
        const data = await res.json();
        if (!Array.isArray(data) || data.length === 0) {
          results.innerHTML = '<li>No results found.</li>';
          return;
        }

        results.innerHTML = data
          .map(item => `\n            <li>\n              <strong>${item.name}</strong>\n              <div>${item.address || ''}</div>\n            </li>\n          `)
          .join('');
      } catch (err) {
        results.innerHTML = '<li>Error fetching results.</li>';
        console.error(err);
      }
    });
  </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/search', methods=['POST'])
def search():
    payload = request.get_json() or request.form
    city = payload.get('city')
    category = payload.get('category') or 'tourism.attraction'

    if not city:
        return jsonify([])

    results = fetch_city_data_live(city, category)
    return jsonify(results)


if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))
