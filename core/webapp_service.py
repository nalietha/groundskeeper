import threading
import os
from flask import Flask, request, render_template, make_response

from core.utils import get_local_ip

current_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(os.path.dirname(current_dir), 'templates')

app = Flask(__name__, template_folder=template_dir)

app.config['NOTIFICATION_SERVICE'] = None
app.config['THEME_SERVICE'] = None
app.config['TRACKING_SERVICE'] = None

def _build_active_timers(theme_service, tracking_service):
    """Formats the currently tracked items for the boiler-pressure display."""
    active_timers = []
    if not tracking_service:
        return active_timers
    for item in tracking_service.get_tracked_items():
        theme = theme_service.get_theme(item['theme_name'])
        if not theme:
            continue
        start_time = item['start_time']
        active_timers.append({
            'theme_name': theme.name,
            'start_time_str': start_time.strftime("%I:%M %p").lstrip('0'),
            # Convert Python datetime to a Javascript-friendly millisecond timestamp
            'started_at_ms': int(start_time.timestamp() * 1000),
            'timer_ms': getattr(theme, 'timer_ms', 0),
        })
    return active_timers


def _render_page(message="", managed_contact="", managed_subscriptions=None,
                 saved_overrides=None, response_cookie_data=None):
    """Renders the web page, pulling saved form values from cookies and letting
    callers override individual pieces (message, managed subscriptions, etc.)."""
    theme_service = app.config['THEME_SERVICE']
    tracking_service = app.config['TRACKING_SERVICE']

    saved = {
        'alias': request.cookies.get('alias', ''),
        'method': request.cookies.get('contact_method', 'email'),
        'email': request.cookies.get('email', ''),
        'phone': request.cookies.get('phone', ''),
        'carrier': request.cookies.get('carrier', '@vtext.com'),
        'theme': request.cookies.get('theme', ''),
        'days': request.cookies.get('days', 'Monday,Tuesday,Wednesday,Thursday,Friday').split(','),
    }
    if saved_overrides:
        saved.update(saved_overrides)

    themes = theme_service.get_all_themes() if theme_service else []

    html_content = render_template(
        'webapp/index.html',
        themes=themes,
        message=message,
        saved_alias=saved['alias'],
        saved_method=saved['method'],
        saved_email=saved['email'],
        saved_phone=saved['phone'],
        saved_carrier=saved['carrier'],
        saved_theme=saved['theme'],
        saved_days=saved['days'],
        active_timers=_build_active_timers(theme_service, tracking_service),
        managed_contact=managed_contact,
        managed_subscriptions=managed_subscriptions or [],
    )

    resp = make_response(html_content)
    if response_cookie_data:
        for key, val in response_cookie_data.items():
            resp.set_cookie(key, val, max_age=31536000)
    return resp


def _contact_from_form(form):
    """Rebuilds the stored contact string from either the subscribe form
    (method + email/phone/carrier) or the manage form (single field)."""
    manual = form.get("manage_contact", "").strip()
    if manual:
        return manual
    if form.get("contact_method", "email") == "sms":
        clean_phone = ''.join(filter(str.isdigit, form.get("phone", "")))
        return f"{clean_phone}{form.get('carrier', '')}"
    return form.get("email", "").strip()


def _handle_subscribe(notification_service, form):
    alias = form.get("alias", "Friend").strip()
    method = form.get("contact_method", "email")
    theme_name = form.get("theme")
    email = form.get("email", "").strip()
    phone = form.get("phone", "").strip()
    carrier = form.get("carrier", "")
    days = form.getlist("days")
    contact = _contact_from_form(form)

    if not (contact and theme_name):
        return _render_page(message="")
    if not days:
        return _render_page(message="Error: You must select at least one day!")

    notification_service.add_subscriber(contact, theme_name, alias, days)
    return _render_page(
        message=f"Schedule saved! {alias} will be notified about {theme_name} on selected days.",
        saved_overrides={
            'alias': alias, 'method': method, 'email': email,
            'phone': phone, 'carrier': carrier, 'theme': theme_name, 'days': days,
        },
        response_cookie_data={
            'alias': alias, 'contact_method': method, 'email': email,
            'phone': phone, 'carrier': carrier, 'theme': theme_name, 'days': ','.join(days),
        },
    )


@app.route("/", methods=["GET", "POST"])
def index():
    notification_service = app.config['NOTIFICATION_SERVICE']

    if request.method != "POST":
        return _render_page()

    form_type = request.form.get("form_type", "subscribe")

    if form_type == "manage":
        contact = _contact_from_form(request.form)
        subs = notification_service.get_subscriptions_for(contact) if contact else []
        message = "" if subs else f"No active subscriptions found for {contact}." if contact else ""
        return _render_page(message=message, managed_contact=contact, managed_subscriptions=subs)

    if form_type == "unsubscribe":
        contact = _contact_from_form(request.form)
        theme_name = request.form.get("theme", "")
        removed = notification_service.remove_subscriber(contact, theme_name)
        message = (f"Unsubscribed from {theme_name}." if removed
                   else f"No subscription to {theme_name} was found for {contact}.")
        return _render_page(message=message, managed_contact=contact,
                            managed_subscriptions=notification_service.get_subscriptions_for(contact))

    if form_type == "unsubscribe_all":
        contact = _contact_from_form(request.form)
        removed = notification_service.remove_all_subscriptions(contact)
        message = (f"Unsubscribed {contact} from all systems." if removed
                   else f"No active subscriptions found for {contact}.")
        return _render_page(message=message, managed_contact=contact, managed_subscriptions=[])

    return _handle_subscribe(notification_service, request.form)


@app.route("/unsubscribe", methods=["GET"])
def unsubscribe():
    """One-click unsubscribe target for the link embedded in notification emails."""
    notification_service = app.config['NOTIFICATION_SERVICE']
    contact = request.args.get("contact", "").strip()
    theme_name = request.args.get("theme", "").strip()

    if not contact:
        return _render_page(message="Invalid unsubscribe link.")

    if theme_name:
        removed = notification_service.remove_subscriber(contact, theme_name)
        message = (f"You've been unsubscribed from {theme_name}." if removed
                   else f"You were not subscribed to {theme_name}.")
    else:
        removed_themes = notification_service.remove_all_subscriptions(contact)
        message = ("You've been unsubscribed from all systems." if removed_themes
                   else "No active subscriptions found.")

    return _render_page(message=message, managed_contact=contact,
                        managed_subscriptions=notification_service.get_subscriptions_for(contact))

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
        return get_local_ip()