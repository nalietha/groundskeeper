import tkinter as tk
from PIL import Image, ImageTk
import qrcode
from .bases import MenuScreen

class QRCodeView(MenuScreen):
    def setup_ui(self):
        title_label = tk.Label(self.content_frame, text="Notification Setup", font=self.fonts["title"])
        title_label.pack(pady=(10, 5))

        desc_label = tk.Label(
            self.content_frame, 
            text="Scan QR code on your phone to subscribe for today's alerts.", 
            font=self.fonts["body"],
            wraplength=self.config.SCREEN_WIDTH - 20,
            justify="center"
        )
        desc_label.pack(pady=(0, 10))

        self.qr_label = tk.Label(self.content_frame)
        self.qr_label.pack(expand=True)

    def tkraise(self, aboveThis=None):
        super().tkraise(aboveThis)
        # Generate the QR code dynamically when the screen is shown
        if 'get_webapp_ip' in self.callbacks:
            ip_address = self.callbacks['get_webapp_ip']()
            url = f"http://{ip_address}:5000/"
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=4,
                border=2,
            )
            qr.add_data(url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Use a smaller percentage of the screen width to leave room for text/buttons
            max_size = int(min(self.config.SCREEN_WIDTH * 0.6, self.config.SCREEN_HEIGHT * 0.45))
            img = img.resize((max_size, max_size), Image.LANCZOS)
            
            self.qr_image = ImageTk.PhotoImage(img)
            self.qr_label.config(image=self.qr_image)
