import threading
import socket
from flask import Flask, request, render_template_string, make_response

app = Flask(__name__)
# We will inject the notification_service and theme_service into the app context
app.config['NOTIFICATION_SERVICE'] = None
app.config['THEME_SERVICE'] = None

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Groundskeeper Notifications</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; padding: 20px; max-width: 400px; margin: auto; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; }
        input[type="text"], select { width: 100%; padding: 8px; box-sizing: border-box; }
        button { background-color: #4CAF50; color: white; padding: 10px 15px; border: none; cursor: pointer; width: 100%; }
        .success { color: green; margin-bottom: 15px; }
    </style>
</head>
<body>
    <h2>Notification Signup</h2>
    <p>Sign up to receive alerts for today.</p>
    
    {% if message %}
        <div class="success">{{ message }}</div>
    {% endif %}

    <form method="POST" action="/">
        <div class="form-group">
            <label for="contact">Email or SMS Gateway (e.g. 5551234567@vtext.com):</label>
            <input type="text" id="contact" name="contact" value="{{ saved_contact }}" required>
        </div>
        
        <div class="form-group">
            <label for="theme">Select Item to Track:</label>
            <select id="theme" name="theme">
                {% for theme in themes %}
                    <option value="{{ theme.name }}" {% if theme.name == saved_theme %}selected{% endif %}>{{ theme.name }}</option>
                {% endfor %}
            </select>
        </div>
        
        <button type="submit">Subscribe for Today</button>
    </form>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    message = ""
    theme_service = app.config['THEME_SERVICE']
    notification_service = app.config['NOTIFICATION_SERVICE']
    
    saved_contact = request.cookies.get('contact', '')
    saved_theme = request.cookies.get('theme', '')
    
    response_cookie_data = None

    if request.method == "POST":
        contact = request.form.get("contact")
        theme_name = request.form.get("theme")
        
        if contact and theme_name:
            if notification_service.add_subscriber(contact, theme_name):
                message = f"Successfully subscribed {contact} to {theme_name} alerts for today!"
            else:
                message = f"You are already subscribed to {theme_name} alerts today."
                
            saved_contact = contact
            saved_theme = theme_name
            response_cookie_data = {'contact': contact, 'theme': theme_name}
                
    themes = theme_service.get_all_themes() if theme_service else []
    html_content = render_template_string(HTML_TEMPLATE, themes=themes, message=message, saved_contact=saved_contact, saved_theme=saved_theme)
    
    resp = make_response(html_content)
    if response_cookie_data:
        # Max age is 1 year (31536000 seconds)
        resp.set_cookie('contact', response_cookie_data['contact'], max_age=31536000)
        resp.set_cookie('theme', response_cookie_data['theme'], max_age=31536000)
        
    return resp

class WebAppService:
    def __init__(self, notification_service, theme_service, port=5000):
        self.port = port
        app.config['NOTIFICATION_SERVICE'] = notification_service
        app.config['THEME_SERVICE'] = theme_service
        self.thread = None

    def start(self):
        """Starts the Flask app in a background thread."""
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print(f"WebAppService started on port {self.port}")

    def _run(self):
        # We run the flask app, binding to all interfaces so phones can connect
        # Using use_reloader=False because we are running in a thread
        app.run(host='0.0.0.0', port=self.port, debug=False, use_reloader=False)

    def get_local_ip(self):
        """Attempts to find the local IP address on the network."""
        try:
            # We connect to an external IP (doesn't actually send a packet)
            # just to get the socket's local address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
