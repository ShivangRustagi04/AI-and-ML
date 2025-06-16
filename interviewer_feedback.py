import os
from dotenv import load_dotenv
import json
import sqlite3
import requests
import assemblyai as aai
from moviepy.video.io.VideoFileClip import VideoFileClip
import streamlit as st
from PIL import Image
import numpy as np

# Load environment variables
load_dotenv()

# Configure APIs
aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Initialize the database
def initialize_database():
    if os.path.exists("candidate_database.db"):
        os.remove("candidate_database.db")

    conn = sqlite3.connect("candidate_database.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS candidates (
        Name TEXT NOT NULL,
        Email TEXT PRIMARY KEY,
        InterviewDate TEXT,
        AppliedRole TEXT,
        VideoInterviewLink TEXT
    );
    """)
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM candidates")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO candidates (Name, Email, InterviewDate, AppliedRole, VideoInterviewLink)
        VALUES ('Shivang Rustagi', 'john.doe@example.com', '2023-10-15', 'Data Scientist', 'https://drive.google.com/file/d/1O8nLXUz_N8IMUIjgSfuDCkQ3su20CqUq/view?usp=sharing');
        """)
        cursor.execute("""
        INSERT INTO candidates (Name, Email, InterviewDate, AppliedRole, VideoInterviewLink)
        VALUES ('Jane Smith', 'jane.smith@example.com', '2023-10-16', 'Software Engineer', 'https://drive.google.com/file/d/1SJD0uZq-NTGBhTyF5veKfOD9E0hzN1Me/view?usp=sharing');
        """)
        conn.commit()

    conn.close()

def download_video(drive_url, video_path="downloaded_video.mp4"):
    file_id = drive_url.split('/d/')[1].split('/')[0]
    download_url = f'https://drive.google.com/uc?id={file_id}'
    
    try:
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        
        with open(video_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=108192):
                file.write(chunk)
        
        return video_path
    except requests.RequestException as e:
        st.error(f"Failed to download video: {e}")
        return None

def get_video_duration(video_path):
    """
    Get the duration of the video using moviepy.
    """
    try:
        video_clip = VideoFileClip(video_path)
        duration = video_clip.duration
        video_clip.close()
        return duration
    except Exception as e:
        st.error(f"Error getting video duration: {e}")
        return None

def transcribe_video(video_path):
    """
    Transcribe video directly using AssemblyAI's video-to-text API.
    """
    try:
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(video_path)
        return transcript
    except Exception as e:
        st.error(f"Error during transcription: {e}")
        return None

def get_first_frame(video_path, timestamp):
    """
    Get the first frame of a video segment as an image.
    """
    try:
        video_clip = VideoFileClip(video_path)
        frame = video_clip.get_frame(timestamp)
        video_clip.close()
        
        # Convert numpy array to PIL Image
        frame_image = Image.fromarray(frame)
        return frame_image
    except Exception as e:
        st.error(f"Error extracting first frame: {e}")
        return None

def analyze_transcription_and_generate_feedback(transcription, video_duration):
    """
    Analyze the transcription and generate feedback for all questions in a single API request.
    Group questions by category.
    """
    prompt = f"""
    Below is a transcription of an interview. Perform the following tasks:
    1. Extract the interviewer's questions and the candidate's answers.
    2. Categorize each question (e.g., EDA, AI, JavaScript, etc.).
    3. For each question-answer pair, generate feedback including:
       - A summary of the candidate's performance.
       - A score (0-100 scale) for the category.
       - A list of pros and cons for the candidate's answer.
    4. Include the start and end timestamps for each question-answer pair (relative to the start of the video).
    5. Group questions with the same category into a single block.

    Transcription:
    {transcription.text}

    Return the data in STRICT JSON format as follows:
    {{
        "categories": [
            {{
                "category": "Category/topic of the question",
                "questions_and_answers": [
                    {{
                        "question": "Interviewer's question",
                        "answer": "Candidate's answer",
                        "feedback": {{
                            "feedback_summary": "A short summary of the candidate's response",
                            "score": "Score based on knowledge demonstrated in the category",
                            "pros": ["List of strengths in the candidate's answer"],
                            "cons": ["List of weaknesses in the candidate's answer"]
                        }},
                        "start_time": "Start time of the question in seconds (relative to video start)",
                        "end_time": "End time of the answer in seconds (relative to video start)"
                    }},
                    ...
                ]
            }},
            ...
        ]
    }}

    IMPORTANT:
    - Return ONLY valid JSON. Do not include any additional text or explanations.
    - Ensure all timestamps are relative to the start of the video.
    - Ensure the JSON is properly formatted and can be parsed by a JSON parser.
    """
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "qwen/qwen2.5-vl-32b-instruct:free",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )
        
        response.raise_for_status()
        response_data = response.json()
        
        # Extract the content from the response
        response_text = response_data['choices'][0]['message']['content'].strip()
        
        # Clean the response text
        if response_text.startswith("```json"):
            response_text = response_text[7:-3].strip()

        # Parse the JSON response
        data = json.loads(response_text)
        return data["categories"]
    except json.JSONDecodeError:
        st.error("The API response is not valid JSON. Please check the prompt or API output.")
        st.write("Raw API Response:", response_text)
        return None
    except Exception as e:
        st.error(f"An error occurred while analyzing the transcription: {e}")
        return None

def fetch_candidate_details(candidate_identifier):
    conn = sqlite3.connect("candidate_database.db")
    cursor = conn.cursor()
    query = """
    SELECT Name, Email, InterviewDate, AppliedRole, VideoInterviewLink
    FROM candidates
    WHERE Email = ? OR Name = ?
    """
    cursor.execute(query, (candidate_identifier, candidate_identifier))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {
            "Name": result[0],
            "Email": result[1],
            "InterviewDate": result[2],
            "AppliedRole": result[3],
            "VideoInterviewLink": result[4],
        }
    else:
        return None

def generate_recommendation(qa_data):
    """
    Calculate the average score and generate a recommendation based on the score range.
    Also, aggregate overall pros and cons.
    """
    total_score = 0
    num_questions = len(qa_data)
    overall_pros = []
    overall_cons = []

    for qa in qa_data:
        total_score += int(qa["feedback"]["score"])
        overall_pros.extend(qa["feedback"]["pros"])
        overall_cons.extend(qa["feedback"]["cons"])

    average_score = int(total_score / num_questions) if num_questions > 0 else 0

    if average_score >= 80:
        recommendation = "Highly Recommended"
    elif 50 <= average_score < 80:
        recommendation = "Recommended"
    elif 30 <= average_score < 50:
        recommendation = "Not Recommended"
    else:
        recommendation = "Highly Not Recommended"

    return average_score, recommendation, overall_pros, overall_cons

def format_timestamp(seconds):
    """Convert seconds to MM:SS format relative to video start"""
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

def main():
    initialize_database()

    st.title("Automated Interview Feedback Form")
    st.write("This app generates feedback by analyzing video interviews.")

    st.subheader("Candidate Details")
    candidate_identifier = st.text_input("Enter Candidate Email or Name", placeholder="e.g., john.doe@example.com or John Doe")
    if candidate_identifier:
        candidate_info = fetch_candidate_details(candidate_identifier)
        if candidate_info:
            candidate_name = candidate_info["Name"]
            candidate_email = candidate_info["Email"]
            interview_date = candidate_info["InterviewDate"]
            applied_role = candidate_info["AppliedRole"]
            video_link = candidate_info["VideoInterviewLink"]

            st.write(f"**Candidate Name:** {candidate_name}")
            st.write(f"**Candidate Email:** {candidate_email}")
            st.write(f"**Interview Date:** {interview_date}")
            st.write(f"**Applied Role:** {applied_role}")

            st.subheader("Video Analysis")
            if st.button("Analyze Video"):
                with st.spinner("Downloading video..."):
                    video_path = download_video(video_link)
                    if video_path:
                        st.video(video_path)  # Display the video directly in the form

                        with st.spinner("Getting video duration..."):
                            video_duration = get_video_duration(video_path)
                            if video_duration:
                                st.write(f"**Video Duration:** {format_timestamp(video_duration)}")

                        with st.spinner("Transcribing video..."):
                            transcription = transcribe_video(video_path)

                            if transcription:
                                st.write("**Transcription:**")
                                st.write(transcription.text)

                                st.write("**Analyzing Transcription and Generating Feedback...**")
                                categories_data = analyze_transcription_and_generate_feedback(transcription, video_duration)

                                if categories_data:
                                    st.write("**Extracted Data with Feedback:**")
                                    st.json(categories_data)

                                    st.subheader("Feedback Results")
                                    for category in categories_data:
                                        st.write(f"### Category: {category['category']}")
                                        for result in category["questions_and_answers"]:
                                            st.write(f"#### Question: {result['question']}")
                                            st.write(f"**Answer:** {result['answer']}")
                                            st.write(f"**Feedback Summary:** {result['feedback']['feedback_summary']}")
                                            st.write(f"**Score:** {result['feedback']['score']}/100")
                                            st.write("**Pros:**")
                                            for pro in result["feedback"]["pros"]:
                                                st.write(f"- {pro}")
                                            st.write("**Cons:**")
                                            for con in result["feedback"]["cons"]:
                                                st.write(f"- {con}")

                                            # Show first frame of the video segment with absolute timestamp
                                            start_time = result.get("start_time")
                                            if start_time is not None:
                                                try:
                                                    start_time = float(start_time)
                                                    frame_image = get_first_frame(video_path, start_time)
                                                    if frame_image:
                                                        st.write(f"**Video Preview at {format_timestamp(start_time)} (from start):**")
                                                        st.image(frame_image, 
                                                                 caption=f"Timestamp: {format_timestamp(start_time)} from video start",
                                                                 use_container_width=True)
                                                        # Add a link to jump to this time in the video
                                                        st.markdown(f"[Jump to this point in video](#video-timestamp-{int(start_time)})")
                                                except (ValueError, TypeError) as e:
                                                    st.error(f"Error processing timestamps: {e}")
                                            else:
                                                st.warning("No timestamp available for this question.")
                                            st.write("---")

                                    # Calculate overall recommendation and aggregate pros/cons
                                    all_qa_data = [qa for category in categories_data for qa in category["questions_and_answers"]]
                                    average_score, recommendation, overall_pros, overall_cons = generate_recommendation(all_qa_data)
                                    st.subheader("Overall Recommendation")
                                    st.write(f"**Average Score:** {average_score}/100")
                                    st.write(f"**Recommendation:** {recommendation}")

                                    # Display overall pros and cons
                                    st.write("**Overall Pros:**")
                                    for pro in overall_pros:
                                        st.write(f"- {pro}")

                                    st.write("**Overall Cons:**")
                                    for con in overall_cons:
                                        st.write(f"- {con}")

                                    st.subheader("Edit Feedback and Scores")
                                    for i, category in enumerate(categories_data):
                                        st.write(f"### Category: {category['category']}")
                                        for j, result in enumerate(category["questions_and_answers"]):
                                            st.write(f"#### Question: {result['question']}")
                                            new_feedback_summary = st.text_area(f"Edit Feedback Summary for Question {j+1} in Category {i+1}", value=result['feedback']['feedback_summary'])
                                            new_score = st.slider(f"Edit Score for Question {j+1} in Category {i+1}", 0, 100, value=int(result['feedback']['score']))
                                            new_pros = st.text_area(f"Edit Pros for Question {j+1} in Category {i+1}", value="\n".join(result['feedback']['pros']))
                                            new_cons = st.text_area(f"Edit Cons for Question {j+1} in Category {i+1}", value="\n".join(result['feedback']['cons']))

                                            categories_data[i]["questions_and_answers"][j]['feedback']['feedback_summary'] = new_feedback_summary
                                            categories_data[i]["questions_and_answers"][j]['feedback']['score'] = new_score
                                            categories_data[i]["questions_and_answers"][j]['feedback']['pros'] = new_pros.split("\n")
                                            categories_data[i]["questions_and_answers"][j]['feedback']['cons'] = new_cons.split("\n")

                                    if st.button("Save Edited Feedback"):
                                        st.success("Feedback saved successfully!")
                                        st.json(categories_data)
        else:
            st.error("Candidate not found in the database. Please check the email or name.")
    else:
        st.error("Please enter a candidate email or name to retrieve details.")

if __name__ == "__main__":
    main()
