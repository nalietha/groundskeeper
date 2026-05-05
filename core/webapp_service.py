import threading
import socket
import os
from datetime import datetime
from flask import Flask, request, render_template, make_response

current_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(os.path.dirname(current_dir), 'templates')

app = Flask(__name__, template_folder=template_dir)

app.config['NOTIFICATION_SERVICE'] = None
app.config['THEME_SERVICE'] = None
app.config['TRACKING_SERVICE'] = None

@app.route("/", methods=["GET", "POST"])
def index():
    message = ""
    theme_service = app.config['THEME_SERVICE']
    notification_service = app.config['NOTIFICATION_SERVICE']
    tracking_service = app.config['TRACKING_SERVICE']
    
    # Load all saved preferences
    saved_alias = request.cookies.get('alias', '')
    saved_method = request.cookies.get('contact_method', 'email')
    saved_email = request.cookies.get('email', '')
    saved_phone = request.cookies.get('phone', '')
    saved_carrier = request.cookies.get('carrier', '@vtext.com')
    saved_theme = request.cookies.get('theme', '')
    
    # Load saved days (default to Mon-Fri if no cookie exists)
    saved_days_str = request.cookies.get('days', 'Monday,Tuesday,Wednesday,Thursday,Friday')
    saved_days = saved_days_str.split(',')
    
    response_cookie_data = None

    if request.method == "POST":
        alias = request.form.get("alias", "Friend").strip()
        method = request.form.get("contact_method", "email")
        theme_name = request.form.get("theme")
        
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        carrier = request.form.get("carrier", "")
        
        # Get the list of checked days from the form
        days = request.form.getlist("days")
        
        if method == "sms":
            clean_phone = ''.join(filter(str.isdigit, phone))
            contact = f"{clean_phone}{carrier}"
        else:
            contact = email
        
        if contact and theme_name:
            if not days:
                message = "Error: You must select at least one day!"
            else:
                notification_service.add_subscriber(contact, theme_name, alias, days)
                message = f"Schedule saved! {alias} will be notified about {theme_name} on selected days."
                
                # Update saved variables for the UI
                saved_alias, saved_method = alias, method
                saved_email, saved_phone, saved_carrier = email, phone, carrier
                saved_theme = theme_name
                saved_days = days
                
                response_cookie_data = {
                    'alias': alias, 'contact_method': method,
                    'email': email, 'phone': phone, 'carrier': carrier, 
                    'theme': theme_name, 'days': ','.join(days)
                }

    # Format active timers for the template
    active_timers = []
    if tracking_service:
        for item in tracking_service.get_tracked_items():
            theme = theme_service.get_theme(item['theme_name'])
            if not theme: continue
            
            start_time = item['start_time']
            timer_ms = getattr(theme, 'timer_ms', 0)
            
            active_timers.append({
                'theme_name': theme.name,
                'start_time_str': start_time.strftime("%I:%M %p").lstrip('0'),
                # Convert Python datetime to a Javascript-friendly millisecond timestamp
                'started_at_ms': int(start_time.timestamp() * 1000),
                'timer_ms': timer_ms
            })

    themes = theme_service.get_all_themes() if theme_service else []
    
    html_content = render_template(
        'webapp/index.html', 
        themes=themes, 
        message=message, 
        saved_alias=saved_alias,
        saved_method=saved_method,
        saved_email=saved_email,
        saved_phone=saved_phone,
        saved_carrier=saved_carrier,
        saved_theme=saved_theme,
        saved_days=saved_days,   
        active_timers=active_timers
    )
    
    resp = make_response(html_content)
    if response_cookie_data:
        for key, val in response_cookie_data.items():
            resp.set_cookie(key, val, max_age=31536000)
        
    return resp

class WebAppService:
    def __init__(self, notification_service, theme_service, tracking_service, port=5000):
        self.port = port
        app.config['NOTIFICATION_SERVICE'] = notification_service
        app.config['THEME_SERVICE'] = theme_service
        app.config['TRACKING_SERVICE'] = tracking_service
        self.thread = None

    def start(self):
        """Starts the Flask app in a background thread."""
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print(f"WebAppService started on port {self.port}")

    def _run(self):
        # By default Flask looks for templates in a folder relative to the script
        # Since we are running from groundskeeper.py at the root, 'templates' should be at the root.
        app.run(host='0.0.0.0', port=self.port, debug=False, use_reloader=False)

    def get_local_ip(self):
        """Attempts to find the local IP address on the network."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"