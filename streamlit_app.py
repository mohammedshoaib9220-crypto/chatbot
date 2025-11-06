# # === Set your credentials here === #
# USERNAME = "s4151984@student.rmit.edu.au"  # CHANGE THIS
# PASSWORD = "MD$Hoaib9220" 


# RMIT Cyber Security Course Advisor - Ultimate Edition
# DCNC Assignment 3 - Option 2
# Author: [Your Name]

import streamlit as st
import json
import boto3
import time
from PyPDF2 import PdfReader
import pandas as pd
from io import StringIO
import base64
from datetime import datetime

# === AWS Configuration === #
COGNITO_REGION = "ap-southeast-2"
BEDROCK_REGION = "ap-southeast-2"
MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"
IDENTITY_POOL_ID = "ap-southeast-2:eaa059af-fd47-4692-941d-e314f2bd5a0e"
USER_POOL_ID = "ap-southeast-2_NfoZbDvjD"
APP_CLIENT_ID = "3p3lrenj17et3qfrnvu332dvka"

# === Set your credentials here === #
USERNAME = "s4151984@student.rmit.edu.au"  # CHANGE THIS
PASSWORD = "MD$Hoaib9220"                   # CHANGE THIS

# === Helper Functions === #
def get_aws_credentials():
    """Connect to AWS with fixed credentials"""
    try:
        idp_client = boto3.client("cognito-idp", region_name=COGNITO_REGION)
        response = idp_client.initiate_auth(
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={"USERNAME": USERNAME, "PASSWORD": PASSWORD},
            ClientId=APP_CLIENT_ID,
        )
        id_token = response["AuthenticationResult"]["IdToken"]

        identity_client = boto3.client("cognito-identity", region_name=COGNITO_REGION)
        identity_response = identity_client.get_id(
            IdentityPoolId=IDENTITY_POOL_ID,
            Logins={f"cognito-idp.{COGNITO_REGION}.amazonaws.com/{USER_POOL_ID}": id_token},
        )

        creds_response = identity_client.get_credentials_for_identity(
            IdentityId=identity_response["IdentityId"],
            Logins={f"cognito-idp.{COGNITO_REGION}.amazonaws.com/{USER_POOL_ID}": id_token},
        )

        return creds_response["Credentials"]
    except Exception as e:
        st.error(f"❌ Login failed. Please check username/password in code.")
        return None

def extract_pdf_text(pdf_files):
    """Extract text from PDF files"""
    all_text = []
    for pdf_file in pdf_files:
        try:
            reader = PdfReader(pdf_file)
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text and text.strip():
                    text_parts.append(text.strip())
            
            if text_parts:
                pdf_content = f"📄 {pdf_file.name}\n" + "\n".join(text_parts)
                all_text.append(pdf_content)
        except Exception as e:
            st.error(f"❌ Error reading {pdf_file.name}: {str(e)}")
    
    return "\n\n".join(all_text)

def ask_claude(question, context=""):
    """Ask Claude AI"""
    credentials = get_aws_credentials()
    if not credentials:
        return "Error: Cannot connect to AI service."

    try:
        prompt = f"""You are a helpful RMIT University course advisor. Provide detailed, accurate information about courses, enrollment, and program structure.

{context}

STUDENT'S QUESTION: {question}

Please provide comprehensive, helpful advice. Include specific course codes, requirements, and practical guidance.

Answer in a clear, structured format with headings and bullet points where appropriate:"""

        bedrock_runtime = boto3.client(
            "bedrock-runtime",
            region_name=BEDROCK_REGION,
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretKey"],
            aws_session_token=credentials["SessionToken"],
        )

        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1500,
            "temperature": 0.3,
            "messages": [{"role": "user", "content": prompt}]
        }

        response = bedrock_runtime.invoke_model(
            body=json.dumps(payload),
            modelId=MODEL_ID,
            contentType="application/json",
            accept="application/json"
        )

        result = json.loads(response["body"].read())
        return result["content"][0]["text"]
        
    except Exception as e:
        return f"Error: {str(e)}"

def create_download_link(content, filename, text):
    """Create a download link for text content"""
    b64 = base64.b64encode(content.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">{text}</a>'
    return href

def display_course_beautifully(course):
    """Display course information in a beautiful format"""
    with st.container():
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 25px;
            border-radius: 15px;
            color: white;
            margin: 15px 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        '>
            <h2 style='margin:0; color:white;'>🎓 {course.get('title', 'Unknown Course')}</h2>
            <h3 style='margin:5px 0; color:#f0f0f0;'>{course.get('course_code', 'N/A')}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Course details in cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div style='
                background: #f8f9fa;
                padding: 15px;
                border-radius: 10px;
                border-left: 4px solid #28a745;
                margin: 10px 0;
            '>
                <h4 style='margin:0; color:#333;'>📚 Course Type</h4>
                <p style='margin:5px 0; color:#666;'>{course.get('course_type', 'N/A').title()}</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div style='
                background: #f8f9fa;
                padding: 15px;
                border-radius: 10px;
                border-left: 4px solid #007bff;
                margin: 10px 0;
            '>
                <h4 style='margin:0; color:#333;'>📅 Semester</h4>
                <p style='margin:5px 0; color:#666;'>{course.get('semester', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
            <div style='
                background: #f8f9fa;
                padding: 15px;
                border-radius: 10px;
                border-left: 4px solid #ffc107;
                margin: 10px 0;
            '>
                <h4 style='margin:0; color:#333;'>🏛️ Campus</h4>
                <p style='margin:5px 0; color:#666;'>{course.get('campus', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Description
        st.markdown(f"""
        <div style='
            background: #e3f2fd;
            padding: 20px;
            border-radius: 10px;
            margin: 15px 0;
            border-left: 4px solid #2196f3;
        '>
            <h4 style='margin:0 0 10px 0; color:#1565c0;'>📖 Course Description</h4>
            <p style='margin:0; color:#333; line-height: 1.6;'>{course.get('description', 'No description available.')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Topics
        if course.get('topics'):
            topics_html = "".join([f"<li>{topic}</li>" for topic in course['topics']])
            st.markdown(f"""
            <div style='
                background: #fff3e0;
                padding: 20px;
                border-radius: 10px;
                margin: 15px 0;
                border-left: 4px solid #ff9800;
            '>
                <h4 style='margin:0 0 10px 0; color:#e65100;'>📋 Topics Covered</h4>
                <ul style='margin:0; color:#333;'>{topics_html}</ul>
            </div>
            """, unsafe_allow_html=True)
        
        # Prerequisites
        if course.get('prerequisites'):
            prereq_html = "".join([f"<li>{prereq}</li>" for prereq in course['prerequisites']])
            st.markdown(f"""
            <div style='
                background: #fce4ec;
                padding: 20px;
                border-radius: 10px;
                margin: 15px 0;
                border-left: 4px solid #e91e63;
            '>
                <h4 style='margin:0 0 10px 0; color:#ad1457;'>🎯 Prerequisites</h4>
                <ul style='margin:0; color:#333;'>{prereq_html}</ul>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style='
                background: #e8f5e8;
                padding: 20px;
                border-radius: 10px;
                margin: 15px 0;
                border-left: 4px solid #4caf50;
            '>
                <h4 style='margin:0 0 10px 0; color:#2e7d32;'>✅ Prerequisites</h4>
                <p style='margin:0; color:#333;'>No prerequisites required for this course.</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")

def main():
    # Page setup
    st.set_page_config(
        page_title="RMIT Ultimate Course Advisor",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    .feature-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin: 10px 0;
        border-left: 5px solid #667eea;
    }
    .chat-message {
        padding: 15px;
        border-radius: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .user-message {
        background: #e3f2fd;
        border-left: 5px solid #2196f3;
    }
    .ai-message {
        background: #f3e5f5;
        border-left: 5px solid #9c27b0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="main-header">🎓 RMIT Ultimate Course Advisor</h1>', unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align: center; margin-bottom: 2rem;'>
        <h3 style='color: #666;'>Your All-in-One Solution for Course Planning & Enrollment</h3>
        <p>Browse courses, get AI advice, and download your study plan - all in one place!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://www.rmit.edu.au/content/dam/rmit/au/en/study-with-us/logo/rmit-logo-red-black.png", width=200)
        st.markdown("### 🎯 Quick Actions")
        
        if st.button("📚 Browse All Courses", use_container_width=True):
            st.session_state.current_tab = "Course Browser"
        if st.button("🤖 Ask AI Advisor", use_container_width=True):
            st.session_state.current_tab = "AI Chat Advisor"
        if st.button("📊 Program Structure", use_container_width=True):
            st.session_state.current_tab = "Program Structure"
        
        st.markdown("---")
        st.markdown("### 📁 Upload Data")
        data_format = st.radio("Choose format:", ["JSON Files", "PDF Documents"])
        
        if data_format == "JSON Files":
            uploaded_courses = st.file_uploader("Upload courses_data.json", type=["json"])
            uploaded_structure = st.file_uploader("Upload program_structure.json", type=["json"])
        else:
            uploaded_pdfs = st.file_uploader("Upload PDF documents", type=["pdf"], accept_multiple_files=True)
    
    # Initialize session state
    if 'current_tab' not in st.session_state:
        st.session_state.current_tab = "AI Chat Advisor"
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Main content area
    if st.session_state.current_tab == "AI Chat Advisor":
        display_chat_advisor(uploaded_courses if 'uploaded_courses' in locals() else None)
    
    elif st.session_state.current_tab == "Course Browser":
        display_course_browser(uploaded_courses if 'uploaded_courses' in locals() else None)
    
    elif st.session_state.current_tab == "Program Structure":
        display_program_structure(uploaded_structure if 'uploaded_structure' in locals() else None)

def display_chat_advisor(uploaded_courses):
    st.header("💬 AI Chat Advisor")
    
    # Quick questions
    st.markdown("### 🚀 Quick Questions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("First Year Help", use_container_width=True):
            st.session_state.current_question = "What courses should I take in first year for Cyber Security?"
    with col2:
        if st.button("Enrollment Steps", use_container_width=True):
            st.session_state.current_question = "What are the steps to enroll in courses?"
    with col3:
        if st.button("Career Paths", use_container_width=True):
            st.session_state.current_question = "What career paths are available after Cyber Security degree?"
    with col4:
        if st.button("Course Fees", use_container_width=True):
            st.session_state.current_question = "What are the course fees and payment options?"
    
    # Chat interface
    st.markdown("### 💭 Ask Anything")
    question = st.text_area(
        "Your question:",
        height=100,
        value=st.session_state.get('current_question', ''),
        placeholder="Ask about courses, enrollment, prerequisites, careers, fees, deadlines, or anything else..."
    )
    
    if st.button("🎯 Get Detailed Answer", type="primary", use_container_width=True):
        if question:
            with st.spinner("🤔 Thinking deeply about your question..."):
                start_time = time.time()
                
                # Prepare context
                context = ""
                if uploaded_courses:
                    try:
                        courses_data = json.load(uploaded_courses)
                        context = f"Available courses: {json.dumps(courses_data[:5])}"  # First 5 courses as context
                    except:
                        pass
                
                answer = ask_claude(question, context)
                response_time = round(time.time() - start_time, 2)
                
                # Add to chat history
                st.session_state.chat_history.append({
                    "question": question,
                    "answer": answer,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })
                
                # Display answer
                st.success(f"✅ Answer ready! (Generated in {response_time} seconds)")
                
                st.markdown(f"""
                <div class="chat-message ai-message">
                    <h4>🤖 AI Advisor Response:</h4>
                    {answer}
                </div>
                """, unsafe_allow_html=True)
                
                # Download option
                download_content = f"Question: {question}\n\nAnswer: {answer}\n\nGenerated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                st.markdown(create_download_link(download_content, "ai_response.txt", "📥 Download This Response"), unsafe_allow_html=True)
    
    # Chat history
    if st.session_state.chat_history:
        st.markdown("### 📜 Chat History")
        for i, chat in enumerate(reversed(st.session_state.chat_history[-5:])):  # Show last 5
            with st.expander(f"💬 {chat['question'][:50]}... ({chat['timestamp']})"):
                st.markdown(f"**Q:** {chat['question']}")
                st.markdown(f"**A:** {chat['answer']}")

def display_course_browser(uploaded_courses):
    st.header("📚 Course Browser")
    
    if uploaded_courses:
        try:
            courses_data = json.load(uploaded_courses)
            st.success(f"✅ Loaded {len(courses_data)} courses")
            
            # Search and filter
            col1, col2 = st.columns([2, 1])
            with col1:
                search_term = st.text_input("🔍 Search courses by name, code, or topic")
            with col2:
                course_type = st.selectbox("Filter by type", ["All", "Core", "Elective", "Capstone"])
            
            # Filter courses
            filtered_courses = courses_data
            if search_term:
                filtered_courses = [
                    c for c in courses_data
                    if search_term.lower() in c.get('title', '').lower()
                    or search_term.lower() in c.get('course_code', '').lower()
                    or any(search_term.lower() in topic.lower() for topic in c.get('topics', []))
                ]
            
            if course_type != "All":
                filtered_courses = [c for c in filtered_courses if c.get('course_type', '').lower() == course_type.lower()]
            
            st.write(f"**Showing {len(filtered_courses)} courses**")
            
            # Display courses
            for course in filtered_courses:
                display_course_beautifully(course)
                
                # Download button for individual course
                course_content = f"""
COURSE: {course.get('title', '')} ({course.get('course_code', '')})

DESCRIPTION:
{course.get('description', '')}

DETAILS:
• Type: {course.get('course_type', '')}
• Semester: {course.get('semester', '')}
• Campus: {course.get('campus', '')}
• Credits: {course.get('credits', '')}

TOPICS:
{chr(10).join(f"• {topic}" for topic in course.get('topics', []))}

PREREQUISITES:
{chr(10).join(f"• {prereq}" for prereq in course.get('prerequisites', [])) if course.get('prerequisites') else 'None'}
"""
                st.markdown(create_download_link(
                    course_content, 
                    f"{course.get('course_code', 'course')}_details.txt", 
                    "📥 Download Course Details"
                ), unsafe_allow_html=True)
            
            # Download all courses
            all_courses_content = "\n\n".join([
                f"{course.get('title', '')} ({course.get('course_code', '')}) - {course.get('course_type', '')}"
                for course in filtered_courses
            ])
            st.markdown(create_download_link(
                all_courses_content,
                "all_courses_list.txt",
                "💾 Download All Courses List"
            ), unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Error loading courses: {str(e)}")
    else:
        st.info("📁 Please upload courses_data.json in the sidebar to browse courses")

def display_program_structure(uploaded_structure):
    st.header("📊 Program Structure")
    
    if uploaded_structure:
        try:
            structure_data = json.load(uploaded_structure)
            
            # Program info
            st.markdown("### 🎓 Program Information")
            for program in structure_data.get('programs', []):
                st.markdown(f"""
                <div class="feature-card">
                    <h3>{program.get('title', '')} ({program.get('code', '')})</h3>
                    <p><strong>Duration:</strong> {program.get('duration', '')}</p>
                    <p><strong>Campus:</strong> {program.get('campus', '')}</p>
                    <p><strong>Career:</strong> {program.get('career', '')}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Recommended courses by year
            st.markdown("### 📅 Recommended Study Plan")
            recommended = structure_data.get('recommended_courses', {})
            for year, courses in recommended.items():
                with st.expander(f"🎯 {year.replace('_', ' ').title()}"):
                    for course in courses:
                        st.write(f"• {course}")
            
            # Minors
            st.markdown("### 🎨 Available Minors")
            minors = structure_data.get('minors', [])
            cols = st.columns(3)
            for i, minor in enumerate(minors):
                cols[i % 3].markdown(f"• {minor}")
            
            # Career paths
            st.markdown("### 💼 Career Paths")
            careers = structure_data.get('career_paths', [])
            for career in careers:
                st.write(f"• {career}")
                
            # Download program structure
            structure_content = json.dumps(structure_data, indent=2)
            st.markdown(create_download_link(
                structure_content,
                "program_structure.json",
                "📥 Download Program Structure"
            ), unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Error loading program structure: {str(e)}")
    else:
        st.info("📁 Please upload program_structure.json in the sidebar")

if __name__ == "__main__":
    main()
