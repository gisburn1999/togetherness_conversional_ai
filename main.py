from analyse_with_ai import Ai_Analyse
from voice_recording import VoiceApp
from save_data import DatabaseManager
import json


save = DatabaseManager()
app = VoiceApp()


def main_menue():
    print("\nLets analyse our togetherness!\n"
          "here are some opportunity's:\n"
          "\n1. Record a sound file and transcribe\n"
          "2. analysis_global_master ---> all in one prompt\n"
          "3. analysis_global_first_try\n"
          "4. Analyse in 2 steps\n"
          "5. GROQ Test\n"
          "q for quit\n"
          "\nInterim Helper menue:\n"
          "t1. evaluate_analysis_with_groq\n"
          
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

            case "4":
                db = DatabaseManager()
                existing_profiles = db.load_speaker_entries(app.record_id)

                # Run Step 1 only if we don’t have profiles yet
                if not existing_profiles:
                    if app.transcript_text:
                        ai = Ai_Analyse(record_id=app.record_id , content=app.transcript_text)
                        ai.analyze_speaker_profile_and_save_entries()
                        existing_profiles = db.load_speaker_entries(app.record_id)  # Reload after save
                    else:
                        print("❌ No transcript available. Please record or load a file first.")


                # At this point, existing_profiles must be present
                if existing_profiles:
                    ai = Ai_Analyse(record_id=app.record_id , content=app.transcript_text)
                    #ai.analysis_global_adaptive()  # ✅ Step 2a – text summary with tone
                    #ai.analyze_relationship_dynamics() # ✅ Step 2b – structured profile JSON
                    analysis_id = ai.analysis_global_adaptive()
                    print(f"DEBUG: analysis_id = {analysis_id}")
                    rating = ai.rate_analysis_by_id(analysis_id)
                    print(rating)
            case "5":
                if app.transcript_text:
                    ai = Ai_Analyse(record_id=app.record_id , content=app.transcript_text)
                    ai.name_the_speaker_ai()
                else:
                    print("No transcript available. Please record or load a file first.")

            case "t1":
                #print("Your credit balance is too low to use Claude")
                if app.transcript_text:
                    ai = Ai_Analyse(record_id=app.record_id , content=app.transcript_text)
                    #ai.evaluate_analysis_with_groq()
                    ai.evaluate_analysis_with_groq(analysis_text=app.transcript_text)

                else:
                    print("No transcript available. Please record or load a file first.")

            case "6":
                #filepath = "transcripts/triangle_of_sadness_dinner_date_scene.txt"
                #filepath = "transcripts/dummy_script_30_min.txt"
                #filepath = "transcripts/couple_Dummy_dialogue_pierre_lena.txt"
                #filepath = "transcripts_prefabricated/Export text - 20250524105941recording.wav (25_05_2025).txt"
                #filepath = "transcripts_prefabricated/dummy_generic_romeo_juliet_30min.txt"
                filepath = "transcripts_prefabricated/Export text - 20250524105941recording.wav (25_05_2025) english.txt"

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