from pydub import AudioSegment
from pydub.playback import play


def hello_def():
    sound = AudioSegment.from_file("./audio/startup_sound.mp3", format="mp3")
    play(sound)
    
def goodbye_def():
    sound = AudioSegment.from_file("./audio/shutdown_sound.mp3", format="mp3")
    play(sound)