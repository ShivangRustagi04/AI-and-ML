import sqlite3
from faker import Faker
import random
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os

# Initialize Faker
fake = Faker()

# Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('interview_scheduling.db')
cursor = conn.cursor()

# Drop the existing tables if they exist
cursor.execute('DROP TABLE IF EXISTS interviewers;')
cursor.execute('DROP TABLE IF EXISTS candidates;')

# Recreate the tables with the updated schema
cursor.execute('''
CREATE TABLE interviewers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    available_date TEXT NOT NULL,  -- New column for date
    available_time_slot TEXT NOT NULL,
    domain_experience TEXT NOT NULL,
    experience INTEGER NOT NULL,
    job_description TEXT NOT NULL,
    tech_stack TEXT NOT NULL,
    company TEXT NOT NULL
);
''')

cursor.execute('''
CREATE TABLE candidates (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    selected_date TEXT NOT NULL,  -- New column for date
    selected_time_slot TEXT NOT NULL,
    domain_experience TEXT NOT NULL,
    experience INTEGER NOT NULL,
    job_description TEXT NOT NULL,
    tech_stack TEXT NOT NULL,
    company TEXT NOT NULL
);
''')

# Define possible domains, tech stacks, and job descriptions
domains = ['Software Engineering', 'Data Science', 'Product Management', 'DevOps', 'UI/UX Design']
tech_stacks = ['Python', 'Java', 'JavaScript', 'C#', 'Ruby']
job_descriptions = {
    'Software Engineering': ['Backend Development', 'Frontend Development', 'Full Stack Development'],
    'Data Science': ['Machine Learning', 'Data Analysis', 'AI Research'],
    'Product Management': ['Product Strategy', 'Agile Project Management', 'Product Marketing'],
    'DevOps': ['Cloud Infrastructure', 'CI/CD Pipeline', 'Site Reliability Engineering'],
    'UI/UX Design': ['User Research', 'Wireframing', 'Prototyping']
}

# Define possible time slots
time_slots = ['09:00-10:00', '10:00-11:00', '11:00-12:00', '13:00-14:00', '14:00-15:00', '15:00-16:00']

# Google Calendar API setup
SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

def get_calendar_service():
    """Authenticate and return Google Calendar service."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=8080)  # Explicitly set the port
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    return build('calendar', 'v3', credentials=creds)

def create_google_calendar_event(candidate_name, interviewer_name, event_date, time_slot):
    """Create a Google Calendar event for the interview."""
    try:
        service = get_calendar_service()
        
        # Parse time slot (assuming format 'HH:MM-HH:MM')
        start_time, end_time = time_slot.split('-')
        
        # Combine the event date and time
        start_datetime = datetime.combine(datetime.strptime(event_date, "%Y-%m-%d").date(), datetime.strptime(start_time, "%H:%M").time())
        end_datetime = datetime.combine(datetime.strptime(event_date, "%Y-%m-%d").date(), datetime.strptime(end_time, "%H:%M").time())
        
        event = {
            'summary': f'Interview: {candidate_name} with {interviewer_name}',
            'description': f'Interview scheduled between {candidate_name} and {interviewer_name}',
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': 'Asia/Kolkata',  # Change to your timezone
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'Asia/Kolkata',  # Change to your timezone
            },
            'reminders': {
                'useDefault': True,
            },
        }
        created_event = service.events().insert(
            calendarId='primary',
            body=event
        ).execute()
        
        print(f"Event created: {created_event.get('htmlLink')}")
        return created_event
        
    except Exception as e:
        print(f"Error creating Google Calendar event: {str(e)}")
        return None

def generate_random_date():
    """Generate a random date within the next 7 days."""
    start_date = datetime.now().date()
    end_date = start_date + timedelta(days=7)  # Reduced range to 7 days
    random_days = random.randint(0, (end_date - start_date).days)
    return (start_date + timedelta(days=random_days)).strftime('%Y-%m-%d')

# Generate common dates for candidates and interviewers
common_dates = [generate_random_date() for _ in range(3)]  # Generate 3 common dates

# Function to generate fake interviewers with experience and date
def generate_interviewers(num):
    interviewers = []
    for _ in range(num):
        name = fake.name()
        domain = random.choice(domains)
        job_desc = random.choice(job_descriptions[domain])
        time_slot = random.choice(time_slots)
        tech_stack = random.choice(tech_stacks)
        company = fake.company()
        experience = random.randint(5, 10)  # Interviewers have higher experience (5–10 years)
        available_date = random.choice(common_dates)  # Use common dates
        interviewers.append((name, available_date, time_slot, domain, experience, job_desc, tech_stack, company))
    return interviewers

# Function to generate fake candidates with experience and date
def generate_candidates(num):
    candidates = []
    for _ in range(num):
        name = fake.name()
        domain = random.choice(domains)
        job_desc = random.choice(job_descriptions[domain])
        time_slot = random.choice(time_slots)
        tech_stack = random.choice(tech_stacks)
        company = fake.company()
        experience = random.randint(1, 5)  # Candidates have lower experience (1–5 years)
        selected_date = random.choice(common_dates)  # Use common dates
        candidates.append((name, selected_date, time_slot, domain, experience, job_desc, tech_stack, company))
    return candidates

# Generate 10 interviewers and 5 candidates
interviewers_data = generate_interviewers(10)
candidates_data = generate_candidates(5)

# Insert fake data into the interviewers table
cursor.executemany('''
INSERT INTO interviewers (name, available_date, available_time_slot, domain_experience, experience, job_description, tech_stack, company)
VALUES (?, ?, ?, ?, ?, ?, ?, ?);
''', interviewers_data)

# Insert fake data into the candidates table
cursor.executemany('''
INSERT INTO candidates (name, selected_date, selected_time_slot, domain_experience, experience, job_description, tech_stack, company)
VALUES (?, ?, ?, ?, ?, ?, ?, ?);
''', candidates_data)

# Commit the changes
conn.commit()

# Query to find potential interviewers for candidates with experience condition
query = '''
SELECT 
    c.name AS candidate_name,
    c.selected_date,
    c.selected_time_slot,
    c.domain_experience,
    c.experience AS candidate_experience,
    c.job_description,
    c.tech_stack,
    c.company,
    i.name AS interviewer_name,
    i.available_date,
    i.available_time_slot,
    i.experience AS interviewer_experience,
    i.tech_stack,
    i.company
FROM 
    candidates c
JOIN 
    interviewers i
ON 
    c.domain_experience = i.domain_experience
    AND c.selected_date = i.available_date  -- Match on date
    AND c.selected_time_slot = i.available_time_slot  -- Match on time slot
    AND i.experience >= c.experience + 2  -- Interviewer must have at least 2 years more experience
    AND c.company != i.company;  -- Ensure interviewer is from a different company
'''

# Execute the query
cursor.execute(query)

# Fetch all results
results = cursor.fetchall()

# Close the database connection
conn.close()

# Process matched pairs and create Google Calendar events
if results:
    print("Potential Interviewers for Candidates:")
    for row in results:
        candidate_name, selected_date, selected_time_slot, domain, candidate_experience, job_desc, tech_stack, company, interviewer_name, available_date, available_time_slot, interviewer_experience, interviewer_tech_stack, interviewer_company = row
        print(f"Candidate: {candidate_name}, Selected Date: {selected_date}, Selected Time Slot: {selected_time_slot}, Domain: {domain}, Experience: {candidate_experience} years, Job Description: {job_desc}, Tech Stack: {tech_stack}, Company: {company}")
        print(f"Matched Interviewer: {interviewer_name}, Available Date: {available_date}, Available Time Slot: {available_time_slot}, Experience: {interviewer_experience} years, Tech Stack: {interviewer_tech_stack}, Company: {interviewer_company}")
        print("-" * 50)
        # Create a Google Calendar event
        create_google_calendar_event(candidate_name, interviewer_name, selected_date, selected_time_slot)
else:
    print("No matching interviewers found for any candidate.")