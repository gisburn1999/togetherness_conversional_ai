import sqlite3
import os


class DatabaseManager:
    def __init__(self , db_path="recordings.db"):
        self.db_path = db_path
        self.setup_db()


    def connect(self):
        return sqlite3.connect(self.db_path)


    # Create the tables
    def setup_db(self):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE recordings ADD COLUMN length INT;")
        except sqlite3.OperationalError:
                # Column already exists

            pass

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


    def update_missing_lengths(self):
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


    def save_analysis(self , recording_id , analysis_type , model , temp , analysis_file, token):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO ai_analysis (recording_id, analysis_type, model, temp, analysis_file, tokens_used)
            VALUES (?, ?, ?, ?, ?, ?)
        """ , (recording_id , analysis_type , model , temp , analysis_file, token)
            )
        conn.commit()
        conn.close()