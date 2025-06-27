"""Quickstart
Install the openai package using the following pip command:
pip install openai"""
import json
import os
import textwrap
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()
import anthropic
from groq import Groq
from save_data import DatabaseManager
import inspect

open_ai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))   #here or as self?
# Initialize the AI client
claude_client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_KEY"))


class Ai_Analyse():
    def __init__(self, record_id=None, content=None):
        self.record_id = record_id
        self.content = content
        self.transcript_text = None
        self.model_open_ai = "gpt-4o-mini"
        self.db = DatabaseManager()


    def load_from_voice_app(self, voice_app):
        self.record_id = voice_app.record_id
        self.content = voice_app.transcript_text



    def name_the_speaker_ai(self):
        response = open_ai_client.chat.completions.create(
            model=self.model_open_ai,
            messages=[
                {
                    "role":    "system" ,
                    "content": "You are an expert at analyzing dialogue transcripts and identifying any real names that are mentioned within the conversation, even if they are only used once."
                } ,
                {
                    "role":    "user" ,
                    "content": (
                        "Below is a transcript. Please return a list of speakers, assigning real names when mentioned in the dialogue. "
                        "For example: Speaker C (NAME A, maybe or can be also NAME A1), Speaker B, Speaker A. "
                        "Do not invent names — only use what’s actually spoken."
                    )
                } ,
                {
                    "role":    "user" ,
                    "content": self.content
                }
            ],
            temperature=0.0,
            max_tokens=200 # token as answer
        )

        # Display the generated text
        text = response.choices[0].message.content
        wrapped_text = textwrap.fill(text , width=80)
        print("result done with GPT40 mini")
        print(wrapped_text)

    def analysis_global_master(self, temp = 0.8):
        db = DatabaseManager()
        response = open_ai_client.chat.completions.create(
        model = self.model_open_ai ,
            messages=[
                {
                    "role":    "system" ,
                    "content": (
                        "You act as an AI trained to analyze couple dialogues from natural conversations. "
                        "Your job is to detect emotional and communication patterns, extract names if available, and provide helpful relationship insights."
                    )
                } ,
                {
                    "role":    "user" ,
                    "content": (
                        "Here is a transcript of a conversation between two people. "
                        "Please analyze it and return your answer in the following format:\n\n"

                        "**Names:**\n"
                        "- Speaker A: [Extracted name or 'Speaker A']\n"
                        "- Speaker B: [Extracted name or 'Speaker B']\n\n"

                        "**Speaker A Problems:**\n"
                        "- List the main emotional or communication problems this person shows.\n\n"

                        "**Speaker B Problems:**\n"
                        "- List the main emotional or communication problems this person shows.\n\n"

                        "**Shared Problems:**\n"
                        "- List problems that affect both or their relationship.\n\n"

                        "**Conclusions:**\n"
                        "- Summarize what is happening beneath the surface.\n\n"

                        "**Solutions:**\n"
                        "- Suggest specific, actionable strategies to improve their communication or relationship.\n\n"

                        "Please keep your answer concise but detailed enough for understanding.\n\n"
                        "Transcript:\n"
                    )
                } ,
                {"role": "user" , "content": self.content} ,
            ] ,
            temperature=temp ,
            max_tokens=600 ,
        )
        text = response.choices[0].message.content
        print(text)
        tokens_used = response.usage.total_tokens
        # save in sql
        analysis_type = inspect.currentframe().f_code.co_name
        db.save_analysis(
            recording_id=self.record_id ,
            analysis_type=analysis_type ,
            model=self.model_open_ai ,
            temp=temp ,
            analysis_file=text ,
            token=tokens_used

        )


    def analysis_global_first_try(self , temp=0.8):
        db = DatabaseManager()

        # Step 1: Create the prompt
        messages = [
            {"role":    "system" ,
             "content": "You are an AI trained to analyze couple dialogues from natural conversations."} ,
            {"role": "user" , "content": (
                "Here is a conversation transcript between two people. "
                "Please analyze and output in this exact format, replacing Speaker A and Speaker B with actual names if mentioned in the transcript. "
                "If no names are found, use Speaker A and Speaker B.\n\n"
                "Speaker A Problems (or [Name]):\n"
                "- List the main emotional or communication problems this person shows.\n\n"
                "Speaker B Problems (or [Name]):\n"
                "- List the main emotional or communication problems this person shows.\n\n"
                "Shared Problems:\n"
                "- List problems that affect both or their relationship.\n\n"
                "Conclusions & Explanation:\n"
                "- Summarize what is happening beneath the surface and what could help resolve their conflict.\n\n"
                "Overall Summary:\n"
                "- Provide a concise one-line psychological summary that encapsulates the overall emotional state and relationship dynamics.\n\n"
                "Please keep your answer concise but detailed enough for understanding.\n\n"
                "**Do not use any markdown formatting (like bold or asterisks).**"
                "Transcript:\n"
            )} ,
            {"role": "user" , "content": self.content}
        ]

        # Step 2: Get response from OpenAI
        response = open_ai_client.chat.completions.create(
            model=self.model_open_ai ,
            messages=messages ,
            temperature=temp ,
            max_tokens=600
        )

        full_text = response.choices[0].message.content
        tokens_used = response.usage.total_tokens

        # Step 3: Extract overall summary and analysis text
        overall_summary = ""
        analysis_text = full_text

        if "Overall Summary:" in full_text:
            parts = full_text.split("Overall Summary:")
            analysis_text = parts[0].strip()
            summary_lines = parts[1].strip().split("\n")
            if summary_lines:
                overall_summary = summary_lines[0].strip()

        # Step 4: Save to DB
        db.save_analysis(
            recording_id=self.record_id ,
            analysis_type="global_adaptive_analysis" ,
            model=self.model_open_ai ,
            temp=temp ,
            analysis_file=analysis_text ,
            overall_summary=overall_summary ,
            token=tokens_used
        )

        # Step 5: Debug output
        print("\n🧠 Global Adaptive Analysis:\n")
        print(full_text)


    def analysis_global_first_try_(self, temp = 0.8):
        db = DatabaseManager()
        response = open_ai_client.chat.completions.create(
        model = self.model_open_ai ,
        messages = [
            {"role":    "system" ,
             "content": "You are an AI trained to analyze couple dialogues from natural conversations."} ,
            {"role": "user" , "content": (
                "Here is a conversation transcript between two people. "
                "Please analyze and output in this exact format, replacing Speaker A and Speaker B with actual names if mentioned in the transcript. "
                "If no names are found, use Speaker A and Speaker B.\n\n"
                "Speaker A Problems (or [Name]):\n"
                "- List the main emotional or communication problems this person shows.\n\n"
                "Speaker B Problems (or [Name]):\n"
                "- List the main emotional or communication problems this person shows.\n\n"
                "Shared Problems:\n"
                "- List problems that affect both or their relationship.\n\n"
                "Conclusions & Explanation:\n"
                "- Summarize what is happening beneath the surface and what could help resolve their conflict.\n\n"
                "Overall Summary:\n"
                "- Provide a concise one-line psychological summary that encapsulates the overall emotional state and relationship dynamics.\n\n"
                "Please keep your answer concise but detailed enough for understanding.\n\n"
                "Transcript:\n"
            )} ,
            {"role": "user" , "content": self.content} ,
        ] ,
        temperature = temp ,
        max_tokens = 300 ,
        )
        text = response.choices[0].message.content
        print(text)
        tokens_used = response.usage.total_tokens

        # save in sql
        analysis_type = inspect.currentframe().f_code.co_name
        db.save_analysis(
            recording_id=self.record_id ,
            analysis_type=analysis_type ,
            model=self.model_open_ai ,
            temp=temp ,
            analysis_file=text ,
            token=tokens_used

        )


    def speaker_analysis(self):
        """

        :return:
        """

        response = open_ai_client.chat.completions.create(
            model=self.model_open_ai,
            messages=[
                {"role": "system" , "content": "You are an AI trained analyze dialogues."} ,
                {"role": "user" , "content": "Here is the transcript. Please identify how many speakers are talking. One Sentence answer: what are their roles/relationships. And format in the next line, when possible, can you identify names, when not , dont write anything?"} ,
                {"role": "user" , "content": self.content} ,
            ],
            temperature=0.7,
            max_tokens=200 # token as answer
        )

        # Display the generated text
        text = response.choices[0].message.content
        wrapped_text = textwrap.fill(text , width=80)
        print("result done with GPT40 mini")
        print(wrapped_text)


    def problem_analysis(self): #Your credit balance is too low
        # Specify the model to use
        model = "claude-3-5-sonnet-latest"

        # Prompt the user for input
        user_prompt = f"Here is a transcript of our last talking. {self.content}"

        # Define the system message to set the behavior of the assistant
        system_message = ("You act like an well know, experienced psychologist. Your highly skilled in identifying problems in couple relationships. And gives tips to solve them."
                          "best is, your able to nail you answers down. Problem and solution are not longer than one sentence!"
                          "Voice and tone is appealing to our target audience, they are between 28 and 38yo."
                          "when you can identify problems between the lines, feel free to give special advice")

        # Create the message payload
        messages = [
            {"role": "user" , "content": user_prompt}
        ]

        # Generate a response using the Claude API
        response = claude_client.messages.create(
            model=model ,
            system=system_message ,
            messages=messages ,
            max_tokens=150 ,
            temperature=0.7
        )

        # Display the generated text
        print("Generated text:\n" , response.content[0].text)




    def evaluate_analysis_with_groq(self , analysis_text: str , groq_model="llama3-70b-8192" , groq_heat=0.3):

        """
        Uses Groq's OpenAI-compatible API to evaluate a given relationship analysis based on psychological and emotional quality.

        Parameters:
            analysis_text (str): The relationship analysis to evaluate.
            groq_model (str): The Groq model to use, default is Mixtral.
            groq_heat (float): Temperature for generation, default is 0.3 for consistency.

        Returns:
            dict: Evaluation scores in JSON format.
        """
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("❌ GROQ_API_KEY is not set in environment variables.")

        groq_client = OpenAI(
            api_key=groq_api_key ,
            base_url="https://api.groq.com/openai/v1"
        )

        prompt = f"""
        Please evaluate the following relationship analysis based on the following criteria - but be hypercritical -
        as you are an expert in relationship psychology and conversational AI analysis.
        Your task is to evaluate the following analysis of a couple's conversation and rate it on four key dimensions. Use the definitions and scoring anchors below. Return a JSON object with scores from 1–10, and a calculated total_score and split_up_index (0–10). Be consistent and evidence-based.

        ### Dimensions & Scoring Guide

        1. **psychological_insight**  
        - 10: Expert-level psychological concepts (e.g., attachment theory, projection, defensiveness), correctly applied  
        - 7–9: Solid understanding of human behavior with some theoretical backing  
        - 4–6: General emotional insight, limited depth  
        - 1–3: Surface-level interpretation, no psychological grounding

        2. **emotional_nuance**  
        - 10: Captures subtle shifts in tone, emotion, defensiveness, and vulnerability  
        - 7–9: Good awareness of affect and mood changes  
        - 4–6: Emotionally flat or overly general  
        - 1–3: Misses key emotional tones or misreads intent

        3. **clarity_usefulness**  
        - 10: Clear, actionable advice or interpretation anyone could understand  
        - 7–9: Mostly clear and usable  
        - 4–6: Somewhat vague or abstract  
        - 1–3: Confusing, jargon-heavy, or impractical

        4. **empathy**  
        - 10: Deeply compassionate and fair to both parties  
        - 7–9: Generally empathetic and balanced  
        - 4–6: Slight bias or missed emotional context  
        - 1–3: Harsh, judgmental, or cold

        ### split_up_index
        - Rate from 0 (very healthy interaction) to 10 (very high risk of relationship breakdown)
        - Base this on the relationship analysis

        ---

        ### INPUT ANALYSIS:

        {analysis_text}

        ---

        ### JSON Output Format:
        {{
          "psychological_insight": int,
          "emotional_nuance": int,
          "clarity_usefulness": int,
          "empathy": int,
          "total_score": int,
          "split_up_index": int
        }}

        Respond ONLY with the JSON - no text no markdown.
    """.strip()

        response = groq_client.chat.completions.create(
            model=groq_model ,
            temperature=groq_heat ,
            messages=[
                {"role":    "system" ,
                 "content": "You are an expert relationship evaluator with a clinical psychology background."} ,
                {"role": "user" , "content": prompt}
            ] ,
            max_tokens=300
        )

        content = response.choices[0].message.content.strip()
        print("🧠 Groq Evaluation Result:\n" , content)

        try:
            import json
            return json.loads(content)
        except json.JSONDecodeError:
            print("⚠️ JSON decoding failed. Check the returned content.")
            return {"error": "Invalid JSON format returned from Groq" , "raw_output": content}


    def rate_analysis_by_id(self , analysis_id):
        # Load the analysis text from DB using your load method
        record = self.db.load_analysis_from_db(analysis_id)
        if record is None:
            raise ValueError(f"No analysis found for id {analysis_id}")

        recording_id , _id , analysis_text = record

        # Evaluate the analysis text
        rating = self.evaluate_analysis_with_groq(analysis_text)

        # Save the rating JSON string back to DB
        import json
        rating_json = json.dumps(rating)
        self.db.save_rating_to_ai_analysis(analysis_id , rating_json)

        return rating


    def process_and_rate_analysis(self , analysis_text , overall_summary , temp , tokens_used):
        # 1. Save the analysis to the database
        analysis_id = self.db.save_analysis(
            recording_id=self.record_id ,
            analysis_type="global_adaptive_analysis" ,
            model=self.model_open_ai ,
            temp=temp ,
            analysis_file=analysis_text ,
            overall_summary=overall_summary ,
            token=tokens_used
        )

        # 2. Evaluate the analysis (e.g., with Groq model or any scoring engine)
        rating = self.evaluate_analysis_with_groq(
            recording_id=self.record_id ,
            analysis_id=analysis_id ,
            content=analysis_text
        )

        # 3. Save the rating result back to the database
        self.db.save_rating_to_ai_analysis(
            analysis_id ,
            rating.get_rating_json()
        )

        # Optionally return the rating or analysis_id for downstream use
        return analysis_id , rating


    def basic_groq_analysing(self, groq_model = "llama-3.3-70b-versatile", groq_heat = 0.8):
        db = DatabaseManager() # Initialize the Groq client
        groq_api_key = os.getenv("GROQ_API_KEY")
        groq_client = Groq(api_key=groq_api_key)

        # Specify the model to use
        # "llama-3.3-70b-versatile"
        # Grok-2
        # "llama3-8b-8192" this works
        # "llama-7b-hf" this not


        # System's task
        system_prompt = ("You act like an well known, experienced psychologist. Your highly skilled in identifying problems in couple relationships. And gives tips to solve them."
                          "best is, your able to nail you answers down. Problem and solution are not longer than one sentence!"

                         )

        nothing  = ("You act like an well know, experienced psychologist. Your highly skilled in identifying problems in couple relationships. And gives tips to solve them."
                          "best is, your able to nail you answers down. Problem and solution are not longer than one sentence!"
                          "Voice and tone is appealing to our target audience, they are between 28 and 38yo."
                          "when you can identify problems between the lines, feel free to give special advice"
                         )

        # User's request
        user_prompt = f"Here is a transcript of our last talking. {self.content}"

        # Generate a response using the Groq API
        response = groq_client.chat.completions.create(
            model=groq_model ,
            messages=[
                {"role": "system" , "content": system_prompt} ,
                {"role": "user" , "content": user_prompt}
            ] ,
            temperature= groq_heat ,  # Controls creativity (0 = deterministic, 1 = creative)
            max_tokens=200  # Limits the length of the output
        )
        raw_text = response.choices[0].message.content
        tokens_used = response.usage.completion_tokens
        # save in sql
        analysis_type = inspect.currentframe().f_code.co_name
        db.save_analysis(
            recording_id=self.record_id,
            analysis_type=analysis_type ,
            model=groq_model ,
            temp=groq_heat ,
            analysis_file=raw_text ,
            token=tokens_used
        )

        # Display the generated text

        wrapped_text = textwrap.fill(raw_text , width=80)

        print("Generated text:\n" , wrapped_text)




    def analyze_speaker_profile_and_save_entries(self , temp=0.7):
        db = DatabaseManager()

        messages = [
            {
                "role":    "system" ,
                "content": (
                    "You are an AI trained to profile speakers based on their communication style in couple dialogues. "
                    "You return a structured JSON with separate speaker entries."
                )
            } ,
            {
                "role":    "user" ,
                "content": (
                    "Analyze each speaker's tone, style, emotional intensity, language level, audience fit, and recommendation style.\n\n"
                    "Also determine the speaker's **role** in the conversation group — such as 'boyfriend', 'girlfriend', 'partner', 'friend', 'observer', 'counselor', or just their function, like 'waiter' etc.\n\n"
                    "If the dialogue uses names (e.g., “Alex:”), extract and use them. Otherwise use 'Speaker A', 'Speaker B', etc. "
                    "If you think you understood a name but are unsure, format it like: 'Speaker A (possibly Jana)'.\n\n"
                    "✅ Return only the following JSON structure **exactly**, raw JSON only, without markdown or formatting or extra commentary.:\n\n"
                    "{\n"
                    "  \"speakers\": {\n"
                    "    \"Speaker A\": {\n"
                    "      \"tone\": \"...\",\n"
                    "      \"style\": \"...\",\n"
                    "      \"language_level\": \"...\",\n"
                    "      \"audience_fit\": \"...\",\n"
                    "      \"emotional_intensity\": \"...\",\n"
                    "      \"recommendation_style\": \"...\",\n"
                    "      \"group_role\": \"...\"\n"
                    "    },\n"
                    "    \"Speaker B\": { ... }\n"
                    "  }\n"
                    "}\n\n"
                    "Conversation transcript:\n"
                    )
            } ,
                {
                "role":    "user" ,
                "content": self.content
                }
                    ]

        response = open_ai_client.chat.completions.create(
            model=self.model_open_ai ,
            messages=messages ,
            temperature=temp ,
            max_tokens=600 ,
        )

        profile_text = response.choices[0].message.content



        try:
            profile_data = json.loads(profile_text)
            speakers = profile_data.get("speakers" , {})
            print(f"in analys Speakers var {speakers}")

        except json.JSONDecodeError as e:
            print("❌ Failed to parse JSON from response.")
            print("📛 Error:" , e)

        # Save to new table
        db.save_speaker_entries(self.record_id , speakers)

        print(f"✅ Saved {len(speakers)} speaker profiles for recording {self.record_id}.")




    def analysis_global_adaptive(self , temp=0.8):
        db = DatabaseManager()

        profile = db.get_speaker_profile(self.record_id)
        profile_summary = ""
        if profile:
            profile_summary = (
                f"Based on the speaker profile, the tone is '{profile['tone']}', "
                f"style is '{profile['style']}', "
                f"language level is '{profile['language_level']}', "
                f"audience fit is '{profile['audience_fit']}', "
                f"emotional intensity is '{profile['emotional_intensity']}', "
                f"and the recommended feedback style is '{profile['recommendation_style']}'.\n\n"
            )

        messages = [
            {"role":    "system" ,
             "content": "You are an AI trained to analyze couple dialogues from natural conversations."} ,
            {"role": "user" , "content": (
                "Here is a conversation transcript between two people.\n"
                "Please analyze and output in this exact format, replacing Speaker A and Speaker B with actual names if mentioned.\n"
                "If no names found, use Speaker A and Speaker B.\n\n"
                f"{profile_summary}"
                "Speaker A Problems (or [Name]):\n"
                "- List the main emotional or communication problems this person shows.\n\n"
                "Speaker B Problems (or [Name]):\n"
                "- List the main emotional or communication problems this person shows.\n\n"
                "Shared Problems:\n"
                "- List problems that affect both or their relationship.\n\n"
                "Conclusions & Explanation:\n"
                "- List key conclusions about the underlying dynamics and potential resolutions as bullet points.\n\n"
                "Overall Summary:"
                "- Provide a concise one-line psychological summary that encapsulates the overall emotional state and relationship dynamics."
                "Please keep your answer concise but detailed enough for understanding.\n\n"
                "Transcript:\n"
            )} ,
            {"role": "user" , "content": self.content} ,
        ]

        response = open_ai_client.chat.completions.create(
            model=self.model_open_ai ,
            messages=messages ,
            temperature=temp ,
            max_tokens=600
        )

        text = response.choices[0].message.content
        tokens_used = response.usage.total_tokens

        overall_summary = ""
        if "Overall Summary:" in text:
            parts = text.split("Overall Summary:")
            analysis_text = parts[0].strip()
            overall_summary = parts[1].strip().split("\n")[0]
        else:
            analysis_text = text

        # ✅ Save and capture analysis_id
        analysis_id = self.db.save_analysis(
            recording_id=self.record_id ,
            analysis_type="global_adaptive_analysis" ,
            model=self.model_open_ai ,
            temp=temp ,
            analysis_file=analysis_text ,
            overall_summary=overall_summary ,
            token=tokens_used
        )
        print(F"DEBUG in function: {analysis_id}")
        return analysis_id


    def analyze_relationship_dynamics(self , speaker_profiles: dict = None , temp: float = 0.65 ,
                                      max_tokens: int = 500):
        import json

        db = DatabaseManager()
        if speaker_profiles is None:
            speaker_profiles = db.load_speaker_entries(self.record_id)
            if not speaker_profiles:
                print("❌ No speaker profiles found to analyze.")
                return {}

        prompt_prefix = (
            "You are an expert in relationship psychology and conversational dynamics.\n\n"
            "Given the following speaker communication profiles, generate a relationship-focused analysis for EACH speaker.\n\n"
            "For each speaker, output:\n"
            "- relationship_mindset: a short phrase describing their likely mindset or emotional position\n"
            "- core_needs: 2–3 needs this person is likely expressing or lacking\n"
            "- communication_risks: what could go wrong in a conversation with them\n"
            "- recommendation: how to best approach or respond to this person\n\n"
            "Use clear, concise language. Output as valid JSON only — no markdown, no formatting, no extra text.\n\n"
            "Input:\n"
        )

        formatted_json = json.dumps({"speakers": speaker_profiles} , indent=2)
        full_prompt = prompt_prefix + formatted_json + "\n\nOutput format:\n" + json.dumps(
            {
                "Speaker A": {
                    "relationship_mindset": "..." ,
                    "core_needs":           "..." ,
                    "communication_risks":  "..." ,
                    "recommendation":       "..."
                } ,
                "Speaker B": {
                    "relationship_mindset": "..." ,
                    "core_needs":           "..." ,
                    "communication_risks":  "..." ,
                    "recommendation":       "..."
                }
            } ,
            indent=2
        )

        messages = [
            {"role":    "system" ,
             "content": "You are a helpful assistant that analyzes communication in relationships."} ,
            {"role": "user" , "content": full_prompt}
        ]

        response = open_ai_client.chat.completions.create(
            model=self.model_open_ai ,
            messages=messages ,
            temperature=temp ,
            max_tokens=max_tokens ,
        )
        output_text = response.choices[0].message.content
        print("🔍 Step 2 RAW OUTPUT:\n" , output_text)

        try:
            result = json.loads(output_text)
        except json.JSONDecodeError:
            print("❌ JSON parse failed.")
            return {}

        return result


    def analyze_relationship_dynamics_old(record_id: int , speaker_profiles: dict , temp: float = 0.65 ,
                                      max_tokens: int = 500):
        import json

        db = DatabaseManager()
        formatted_json = json.dumps({"speakers": speaker_profiles} , indent=2)

        prompt_prefix = (
            "You are an expert in relationship psychology and conversational dynamics.\n\n"
            "Given the following speaker communication profiles, generate a relationship-focused analysis for EACH speaker.\n\n"
            "For each speaker, output:\n"
            "- relationship_mindset: a short phrase describing their likely mindset or emotional position\n"
            "- core_needs: 2–3 needs this person is likely expressing or lacking\n"
            "- communication_risks: what could go wrong in a conversation with them\n"
            "- recommendation: how to best approach or respond to this person\n\n"
            "Use clear, concise language. Output as valid JSON only — no markdown, no formatting, no extra text.\n\n"
            "Input:\n"
        )

        full_prompt = prompt_prefix + formatted_json + "\n\nOutput format:\n" + json.dumps(
            {
                "Speaker A": {
                    "relationship_mindset": "..." ,
                    "core_needs":           "..." ,
                    "communication_risks":  "..." ,
                    "recommendation":       "..."
                } ,
                "Speaker B": {
                    "relationship_mindset": "..." ,
                    "core_needs":           "..." ,
                    "communication_risks":  "..." ,
                    "recommendation":       "..."
                }
            } , indent=2
        )

        messages = [
            {"role":    "system" ,
             "content": "You are a helpful assistant that analyzes communication in relationships."} ,
            {"role": "user" , "content": full_prompt}
        ]

        response = open_ai_client.chat.completions.create(
            model="gpt-4" ,
            messages=messages ,
            temperature=temp ,
            max_tokens=max_tokens
        )

        text = response.choices[0].message.content
        tokens_used = response.usage.total_tokens

        db.save_analysis(
            recording_id=record_id ,
            analysis_type="relationship_dynamic_analysis" ,
            model="gpt-4" ,
            temp=temp ,
            analysis_file=text ,
            token=tokens_used
        )

        print("\n💬 Relationship Dynamic Analysis:\n")
        print(text)



    def analyze_speaker_profile(self , temp=0.7):
        db = DatabaseManager()

        messages = [
            {
                "role":    "system" ,
                "content": (
                    "You are an AI trained to profile speakers based on their communication style in couple dialogues."
                ) ,
            } ,
            {
                "role":    "user" ,
                "content": (
                    "Analyze the communication style of both speakers in the following couple dialogue.\n\n"
                    "For each speaker, return a short profile including:\n"
                    "- tone\n"
                    "- style\n"
                    "- language level\n"
                    "- audience fit\n"
                    "- emotional intensity\n"
                    "- recommendation style\n\n"
                    "Use this JSON format:\n"
                    "{\n"
                    "  \"speakers\": {\n"
                    "    \"SpeakerName1\": {\n"
                    "      \"tone\": \"...\",\n"
                    "      \"style\": \"...\",\n"
                    "      \"language_level\": \"...\",\n"
                    "      \"audience_fit\": \"...\",\n"
                    "      \"emotional_intensity\": \"...\",\n"
                    "      \"recommendation_style\": \"...\"\n"
                    "    },\n"
                    "    \"SpeakerName2\": { ... }\n"
                    "  }\n"
                    "}\n\n"
                    "If the dialogue includes names (e.g., 'Alex:'), use those names as keys. If not, use 'Partner A' and 'Partner B'. "
                    "If you're unsure but a name might be mentioned (e.g., 'Jana?'), return a name like: 'Partner A (possibly Jana?)'.\n\n"
                    "Only return the raw JSON. No explanations.\n\n"
                    "Dialogue transcript:\n"
                ) ,
            } ,
            {
                "role":    "user" ,
                "content": self.content
            } ,
        ]

        response = open_ai_client.chat.completions.create(
            model=self.model_open_ai ,
            messages=messages ,
            temperature=temp ,
            max_tokens=600 ,
        )

        profile_text = response.choices[0].message.content.strip()

        # Safe JSON parsing
        try:
            profile_data = json.loads(profile_text)
        except json.JSONDecodeError:
            print("⚠️ Failed to parse JSON. Raw response:")
            print(profile_text)
            profile_data = {}

