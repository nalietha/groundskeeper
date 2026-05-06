# groundskeeper/views/image_utils.py
from PIL import Image, ImageTk

class GIFImage:
    """A helper class to handle animated GIFs in Tkinter."""
    def __init__(self, filepath):
        self.filepath = filepath
        self.image = Image.open(filepath)
        self.frames = []
        self.load_frames()
        self.current_frame = 0
        self.delay = self.image.info.get('duration', 100)

    def load_frames(self):
        """Extracts each frame from the GIF."""
        try:
            while True:
                frame_image = self.image.copy().convert('RGBA')
                self.frames.append(ImageTk.PhotoImage(frame_image))
                self.image.seek(len(self.frames))
        except EOFError:
            pass

    def get_frame(self):
        """Returns the current frame of the animation."""
        if not self.frames:
            return None
        frame = self.frames[self.current_frame]
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        return frame