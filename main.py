from analyse_with_ai import Ai_Analyse
from voice_recording import VoiceApp
from save_data import DatabaseManager
save = DatabaseManager()
app = VoiceApp()


def main_menue():
    print("\nLets analyse our togetherness!\n"
          "here are some opportunity's:\n"
          "\n1. Record a sound file and transcribe\n"
          "2. analysis_global_master ---> all in one prompt\n"
          "3. analysis_global_first_try\n"
          "4. Name the speaker GPT mini\n"
          "5. GROQ Test\n"
          "q for quit\n"
          "\nInterim Helper menue:\n"
          "#i1. list all names in the conversation\n"
          "6. Load a transcript HARDCODED\n"
          "7. Analyse the speaker with GPT 4 MINI\n"
          "8. Print the actual recording\n"
          "9. Loads the sample Triangle of sadness sound file and transcribes\n"
          )
    while True:
        menue_selection = input("\nEnter your next step: (m for show Menue again) ")
        match menue_selection:
            case "1":
                app.record()
                app.transcribe()

            case "2":
                if app.transcript_text:
                    ai = Ai_Analyse(record_id=app.record_id , content=app.transcript_text)
                    ai.analysis_global_master()
                else:
                    print("No transcript loaded. Please load or record one first.")

            case "3":
                if app.transcript_text:
                    ai = Ai_Analyse(record_id=app.record_id , content=app.transcript_text)
                    ai.analysis_global_first_try()
                else:
                    print("Transcript not available.")
                #app.analysis_global_first_try()

            case "4": #name the speaker
                if app.transcript_text:
                    ai = Ai_Analyse(record_id=app.record_id , content=app.transcript_text)
                    ai.name_the_speaker_ai()
                else:
                    print("No transcript available. Please record or load a file first.")
            case "5":  # or whatever number you assign for GROQ analysis
                if app.transcript_text:
                    ai = Ai_Analyse(record_id=app.record_id , content=app.transcript_text)
                    ai.basic_groq_analysing()
                else:
                    print("No transcript loaded. Please load or record one first.")
            case "i1":
                pass
            case "6":
                #filepath = "transcripts/dummy_script_30_min.txt"
                #filepath = "transcripts/couple_Dummy_dialogue_pierre_lena.txt"
                #filepath = "transcripts_prefabricated/Export text - 20250524105941recording.wav (25_05_2025).txt"
                filepath = "transcripts_prefabricated/dummy_generic_romeo_julgit remote add origin https://github.com/gisburn1999/togetherness_conversional_ai.gitiet_30min.txt"

                save.get_or_insert_recording(filepath)
                app.load_existing_recording(filepath)

            case "7": #Analyse the speaker with GPT 4 MINI
                if app.transcript_text:
                    ai = Ai_Analyse(record_id=app.record_id , content=app.transcript_text)
                    result = ai.speaker_analysis()
                    print("\nSpeaker analysis result:\n" , result)
                else:
                    print("No transcript loaded. Please load or record one first.")
            case "8": # print
                app.print_recording()
            case "9":
                #with open("transcripts/output_20250514_191055.txt" , "r" , encoding="utf-8") as f:
                #audio_filepath = "recordings/testfile_talking_with background.m4v"

                #audio_filepath = "recordings/output_20250513_100409.wav"
                audio_filepath = "recordings/triangle_of_sadness_dinner_date_scene.mp3"
                print(
                    f"We will load: {audio_filepath}\n"
                    "a hardcoded SOUNDFILE as samplefile\n"
                    )
                txt_filepath = app.transcribe(filepath=audio_filepath)
                print(txt_filepath)

            case "m" | "M":
                main_menue()

            case "q" | "Q":
                print(f"Always happy to help")
                exit()


def main():
    main_menue()


if __name__ == "__main__":
    main()