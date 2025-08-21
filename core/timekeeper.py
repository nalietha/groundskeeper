import time, datetime

class Timekeeper:

    def __init__(self, startTime, moodObj):
        self.brewStartTime = startTime
        self.brewMood = moodObj
        pass

    def Standby(this):
        try: 
            while True:
                # Display Brew start time
                print(f"Brewed At: {this.brewStartTime}")

                # Display Mood
                print(f"{this.brewMood.emoji} {this.brewMood.message}")
                # Check mood change every 5 minutes
                if currTime.minutes % 5 == 0: 
                    this.brewMood = UpdateMood()

        except KeyboardInterrupt:
            # return to Start Splash screen
            state_manager.StartMenu()