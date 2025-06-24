import json
import sqlite3
import os
from datetime import datetime


class DatabaseManager:
    def __init__(self , db_path="recordings.db"):

        self.conn = sqlite3.connect(db_path)
        #self.conn = None
        self.db_path = db_path
        self.setup_db()


    def connect(self):
        return sqlite3.connect(self.db_path)


    # Create the tables
    def setup_db(self):
        conn = self.connect()
        cursor = conn.cursor()

        # recordings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recordings (
                recording_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                folder TEXT,
                sound_file TEXT,
                transcript_file TEXT,
                analysis_file TEXT,
                transcript TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                names TEXT,
                length INT
            );
        """)


        # ai_analysis table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_analysis (
                analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
                recording_id INTEGER,
                analysis_type TEXT,
                model TEXT,
                temp FLOAT,
                analysis_file TEXT,
                overall_summary TEXT,            -- NEW COLUMN
                analysis_path TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (recording_id) REFERENCES recordings(recording_id)
            );
        """)

        #create speaker name Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recording_names (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recording_id INTEGER,
                name TEXT,
                FOREIGN KEY (recording_id) REFERENCES recordings(recording_id)
            );
        """)

        # speaker profile table v2
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS speaker_profile_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recording_id INTEGER NOT NULL,
                speaker_name TEXT NOT NULL,           -- "Speaker A", or real name like "Jana"
                group_role TEXT,                      -- "partner", "friend", "counselor", etc.
                tone TEXT,
                style TEXT,
                language_level TEXT,
                audience_fit TEXT,
                emotional_intensity TEXT,
                recommendation_style TEXT,
                raw_json TEXT,                        -- full dump for debugging/versioning
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
             """)

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")


    def save_speaker_entries(self , recording_id: int , speakers: dict):
        """
        speakers is the dict with keys 'Speaker A', 'Speaker B', ...
        """
        #print(f"🔔 save_speaker_entries called at now")

        conn = self.connect()  # Open connection once
        cursor = conn.cursor()

        # speakers is already the dict, so no .get() needed here
        print(speakers)

        for speaker_name , data in speakers.items():
            print(speaker_name)
            cursor.execute(
                """
                INSERT INTO speaker_profile_analysis (
                    recording_id,
                    speaker_name,
                    group_role,
                    tone,
                    style,
                    language_level,
                    audience_fit,
                    emotional_intensity,
                    recommendation_style,
                    raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """ ,
                (
                    recording_id ,
                    speaker_name ,
                    data.get("group_role") ,
                    data.get("tone") ,
                    data.get("style") ,
                    data.get("language_level") ,
                    data.get("audience_fit") ,
                    data.get("emotional_intensity") ,
                    data.get("recommendation_style") ,
                    json.dumps(data)
                )
            )

        conn.commit()
        conn.close()


    def load_speaker_entries(self , recording_id: int) -> dict:
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT speaker_name, raw_json FROM speaker_profile_analysis WHERE recording_id = ?" ,
            (recording_id ,)
        )
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return {}

        speakers = {}
        for speaker_name , raw_json in rows:
            speakers[speaker_name] = json.loads(raw_json)
        return speakers


    def get_or_insert_recording(self , filepath):
        filename = os.path.basename(filepath)
        conn = self.connect()
        cursor = conn.cursor()

        # Check if recording already exists
        record = self.get_db_recording(cursor , filename)

        if not record:
            # Read transcript from file
            with open(filepath , 'r' , encoding='utf-8') as file:
                content = file.read()
            length = len(content)

            # Insert into database
            cursor.execute(
                "INSERT INTO recordings (transcript_file, transcript, length) VALUES (?, ?, ?)" ,
                (filename , content , length)
            )
            conn.commit()
            record = self.get_db_recording(cursor , filename)

        conn.close()

        # Pull the ID and transcript from the record
        if isinstance(record , tuple) and len(record) >= 3:
            recording_id = record[0]
            transcript_text = record[2]
        elif isinstance(record , dict) or hasattr(record , "__getitem__"):
            recording_id = record["recording_id"]
            transcript_text = record["transcript"]
        else:
            recording_id = None
            transcript_text = None

        return recording_id , transcript_text


    def get_db_recording(self , cursor , filename):
        cursor.execute(
            "SELECT recording_id, transcript_file, transcript, length FROM recordings WHERE transcript_file = ?" ,
            (filename ,)
        )
        return cursor.fetchone()


    def update_missing_lengths(self): # helping function
        #helper function to update the DB - obsolete
        conn = self.connect()
        cursor = conn.cursor()

        # Select rows where length is NULL
        cursor.execute(
            """
            SELECT recording_id, transcript_file 
            FROM recordings 
            WHERE length IS NULL;
        """
            )
        rows = cursor.fetchall()

        for recording_id , transcript_file in rows:
            if transcript_file:
                # Prepend the folder path
                transcript_path = os.path.join("transcripts" , transcript_file)

                if os.path.exists(transcript_path):
                    try:
                        with open(transcript_path , "r" , encoding="utf-8") as f:
                            content = f.read()
                            length = len(content)  # character count
                    except Exception as e:
                        print(f"Error reading {transcript_path}: {e}")
                        continue

                    # Update the length in the database
                    cursor.execute(
                        """
                        UPDATE recordings 
                        SET length = ? 
                        WHERE recording_id = ?;
                    """ , (length , recording_id)
                        )
                    print(f"Updated recording_id {recording_id} with length {length}")
                else:
                    print(f"File not found for recording_id {recording_id}: {transcript_path}")
            else:
                print(f"No transcript_file entry for recording_id {recording_id}")

        conn.commit()
        conn.close()


    def save_recording(self, timestamp, folder, sound_file, transcript_file=None, analysis_file=None, transcript=None, length=None):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO recordings (timestamp, folder, sound_file, transcript_file, analysis_file, transcript, length)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (timestamp, folder, sound_file, transcript_file, analysis_file, transcript, length))
        conn.commit()
        record_id = cursor.lastrowid
        conn.close()
        return record_id

    def update_transcript(self, recording_id, transcript_file, transcript):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE recordings
            SET transcript_file = ?, transcript = ?
            WHERE recording_id = ?
        """, (transcript_file, transcript, recording_id))
        conn.commit()
        conn.close()


    def save_analysis(self , recording_id , analysis_type , model , temp , analysis_file, token, overall_summary):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO ai_analysis (recording_id, analysis_type, model, temp, analysis_file, tokens_used, overall_summary)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """ , (recording_id , analysis_type , model , temp , analysis_file, token, overall_summary)
            )
        conn.commit()
        conn.close()


    def save_speaker_profile(
            self ,
            recording_id ,
            conversation_tone ,
            speaker_styles ,
            emotional_intensity_score ,
            language_complexity ,
            style_tags ,
            overall_temperature ,
            max_token_recommendation ,
            raw_json
    ):
        """
        Save refined speaker profile analysis to the database.

        :param recording_id: int – ID of the associated recording
        :param conversation_tone: str – Overall tone of the dialogue
        :param speaker_styles: str (JSON) – Describes each speaker's communication style
        :param emotional_intensity_score: int – Emotional heat score (1–10)
        :param language_complexity: str – low / medium / high
        :param style_tags: str (JSON) – Array of short descriptive tags
        :param overall_temperature: float – Suggested OpenAI temp (0.3–1.0)
        :param max_token_recommendation: int – Suggested output token cap for next step
        :param raw_json: str – Full raw JSON response from OpenAI
        """
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO speaker_profile_analysis (
                recording_id,
                conversation_tone,
                speaker_styles,
                emotional_intensity_score,
                language_complexity,
                style_tags,
                overall_temperature,
                max_token_recommendation,
                raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """ ,
            (
                recording_id ,
                conversation_tone ,
                speaker_styles ,
                emotional_intensity_score ,
                language_complexity ,
                style_tags ,
                overall_temperature ,
                max_token_recommendation ,
                raw_json
            )
        )

        conn.commit()
        conn.close()


    def save_speaker_profile_old(self , recording_id , profile_data):
        """
        Save speaker profile analysis to the database.

        :param recording_id: int – ID of the associated recording
        :param profile_data: dict – Parsed profile output from OpenAI
        """
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO speaker_profiles (
                recording_id,
                tone,
                style,
                language_level,
                audience_fit,
                emotional_intensity,
                recommendation_style,
                raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """ , (
                recording_id ,
                profile_data.get("tone") ,
                profile_data.get("style") ,
                profile_data.get("language_level") ,
                profile_data.get("audience_fit") ,
                profile_data.get("emotional_intensity") ,
                profile_data.get("recommendation_style") ,
                json.dumps(profile_data)  # raw backup
            )
            )

        conn.commit()
        conn.close()


    def get_speaker_profile(self , recording_id):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT tone, style, language_level, audience_fit, emotional_intensity, recommendation_style
            FROM speaker_profile_analysis
            WHERE recording_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        """ , (recording_id ,)
            )
        row = cursor.fetchone()
        if row:
            return {
                "tone":                 row[0] ,
                "style":                row[1] ,
                "language_level":       row[2] ,
                "audience_fit":         row[3] ,
                "emotional_intensity":  row[4] ,
                "recommendation_style": row[5]
            }
        return None

