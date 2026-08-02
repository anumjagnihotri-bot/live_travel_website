Create a new file start_tunnel.py in the same folder as app.py:

from pyngrok import ngrok

public_url = ngrok.connect(5000)
print(f"Public URL: {public_url}")

# Keep the script running so the tunnel stays open
input("Press Enter to exit and close the tunnel...\n")