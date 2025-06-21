import textwrap
import sounddevice as sd
from dotenv import load_dotenv
from scipy.io.wavfile import write
from datetime import datetime
import os
import numpy as np
from save_data import DatabaseManager
import assemblyai as aai
#import audioop



aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")

#from pydub import AudioSegment

# Load API key from .env
load_dotenv()


class VoiceApp():
    def __init__(self, record_id=None, fs=44000 , filename=None):
        # self.duration = duration
        self.record_id = record_id
        self.timestamp = None
        self.fs = fs
        self.filename = filename or self._generate_filename()
        # self.filename = self._generate_filename()
        self.filepath = None
        self.recording = True
        self.audio = []
        self.transcription_config = aai.TranscriptionConfig(
            speech_model=aai.SpeechModel.best ,
            speaker_labels=True  # Enables speaker diarization
        )
        self.transcript_text = None
        self.analysis_text = None
        self.db = DatabaseManager()



    def get_default_input_device(self, channels=1):
        devices = sd.query_devices()
        for i , dev in enumerate(devices):
            if dev['max_input_channels'] >= channels:
                print(f"Found input device {i}: {dev['name']} ({dev['max_input_channels']} channels)")
                return i
        raise RuntimeError(f"No valid input device found with at least {channels} channel(s).")


    def _record_loop(self):
        input_device_index = self.get_default_input_device(channels=1)
        sd.default.device = (input_device_index , None)

        print("Using input device:" , sd.query_devices(input_device_index)['name'])
        print("...Recording... Press ENTER to stop.")

        with sd.InputStream(samplerate=self.fs , channels=1 , callback=self._callback):
            input()
            self.recording = False


    def _callback(self , indata , frames , time , status):
        if self.recording:
            self.audio.append(indata.copy())
            # Calculate RMS (root mean square) volume
            volume_norm = np.linalg.norm(indata) / np.sqrt(len(indata))
            # print(f"Mic volume level: {volume_norm:.4f}")


    def record(self):
        self.audio = []
        self.recording = True
        self._record_loop()

        audio_data = np.concatenate(self.audio , axis=0)
        print(f"Total chunks recorded: {len(self.audio)}")
        print(f"Concatenated shape: {audio_data.shape}")
        print(f"First 20 samples: {audio_data[:20].flatten()}")

        folder = "recordings"
        os.makedirs(folder , exist_ok=True)

        # Save temporary WAV
        wav_temp = os.path.join(folder , self.filename)
        print(wav_temp)
        write(wav_temp , self.fs , audio_data)

        # Convert to MP3 and delete WAV
        self.convert_to_mp3(wav_temp)
        os.remove(wav_temp)
        if self.filepath:
            print(f":white_check_mark: Saved as {os.path.basename(self.filepath)} in {folder}")
        else:
            print("No file saved")


    def convert_to_mp3(self , wav_filepath):
        self.filepath = os.path.splitext(wav_filepath)[0] + ".mp3"
        audio = AudioSegment.from_wav(wav_filepath)
        audio.export(self.filepath , format="mp3")
        self.filename = os.path.basename(self.filepath)


    def _generate_filename(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{timestamp}_recording.wav"


    def transcribe(self, filepath=None):
        print(":: Transcribing...")
        if filepath:
            self.filepath = filepath
        print(self.filepath)

        if not self.filepath:
            self.filepath = os.path.join("recordings" , self.filename)

        transcript = aai.Transcriber(config=self.transcription_config).transcribe(self.filepath)

        if transcript.status == "error":
            raise RuntimeError(f"Transcription failed: {transcript.error}")

        # Build transcript text
        speaker_lines = []
        if transcript.utterances:
            for u in transcript.utterances:
                speaker = f"Speaker {u.speaker}"
                text = u.text.strip()
                speaker_lines.append(f"{speaker}: {text}")
        else:
            speaker_lines.append("No speaker-labeled utterances found.")

        self.transcript_text = "\n".join(speaker_lines)

        # Save transcript to file
        os.makedirs("transcripts" , exist_ok=True)
        txt_filename = os.path.splitext(self.filename)[0] + ".txt"
        txt_filepath = os.path.join("transcripts" , txt_filename)

        with open(txt_filepath , "w" , encoding="utf-8") as f:
            f.write(self.transcript_text)

        length = len(txt_filepath)

        # save  to DB
        self.record_id = self.db.save_recording(
            timestamp=self.timestamp ,
            folder="recordings" ,
            sound_file=self.filename ,
            transcript_file=txt_filename ,
            transcript=self.transcript_text,
            length=length
        )
        return txt_filepath

    def load_existing_recording(self , filepath):
        self.filepath = filepath
        record_id , transcript_text = self.db.get_or_insert_recording(filepath)
        self.record_id = record_id
        self.transcript_text = transcript_text

        if self.record_id and self.transcript_text:
            print("Recording loaded from database.")
        else:
            print("Could not load recording.")

    def print_recording(self):
        if self.transcript_text is None:
            print("Nothing to show, do a recording first")
        else:

            wrapped_text = textwrap.fill(self.transcript_text , width=80)
            print(f"Here is the full transcript of the last recording:\n{wrapped_text}")





