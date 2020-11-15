from flask_ngrok import run_with_ngrok
from server import app

run_with_ngrok(app)

if __name__ == "__main__":
    app.run()
