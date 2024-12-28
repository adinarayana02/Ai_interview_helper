import io
import logging
import requests
from flask import Flask, render_template, request, jsonify, send_file
import pyttsx3
import speech_recognition as sr

app = Flask(__name__)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Groq API configuration
API_KEY = "your_api_key_here"
MODEL = "llama3-8b-8192"

# Conversational context storage
conversation_history = []
MAX_CONVERSATION_HISTORY = 10  # Increased for better context retention

def format_technical_response(text):
    """Format technical responses with proper structure and code examples."""
    import re
    
    # Add syntax highlighting markers for code snippets
    text = re.sub(r'```(\w+)\n(.*?)\n```', r'<code class="\1">\2</code>', text, flags=re.DOTALL)
    
    # Format technical terms in bold
    technical_terms = [
        "API", "REST", "HTTP", "CRUD", "SQL", "Docker", "Kubernetes", "AWS",
        "Python", "JavaScript", "React", "Node.js", "Git", "CI/CD", "DevOps"
    ]
    for term in technical_terms:
        text = re.sub(rf'\b{term}\b', f'**{term}**', text)
    
    return text

def structure_interview_response(response):
    """Structure the response in an interview-friendly format."""
    sections = {
        'direct_answer': '',
        'explanation': '',
        'example': '',
        'additional_points': '',
        'follow_up': ''
    }
    
    # Parse the response into structured sections
    current_section = 'direct_answer'
    for line in response.split('\n'):
        if 'Example:' in line or '```' in line:
            current_section = 'example'
        elif 'Additional:' in line or 'Furthermore:' in line:
            current_section = 'additional_points'
        elif 'Related concepts:' in line or 'You might also want to know:' in line:
            current_section = 'follow_up'
        else:
            sections[current_section] += line + '\n'
    
    return sections

@app.route('/generate', methods=['POST'])
def generate_response():
    try:
        user_text = request.json.get('text', '').strip()
        interview_mode = request.json.get('mode', 'technical')  # technical/behavioral

        if not user_text:
            return jsonify({'error': 'No input text provided'}), 400

        # Manage conversation history with interview context
        conversation_history.append({
            "role": "user",
            "content": f"[{interview_mode.upper()} INTERVIEW QUESTION]: {user_text}"
        })

        # System prompt for technical interview assistance
        system_prompt = """You are an experienced technical interviewer and mentor with extensive 
        industry experience. Provide detailed, well-structured responses to technical interview 
        questions with:
        1. A clear, concise direct answer
        2. Technical explanation with relevant concepts
        3. Practical examples or code snippets when applicable
        4. Best practices and common pitfalls
        5. Related topics the interviewer might ask next
        
        For coding questions, include:
        - Time and space complexity analysis
        - Multiple approaches to solve the problem
        - Edge cases and error handling
        - Clean code principles
        
        Maintain a professional tone while being detailed and technically accurate."""

        messages = [
            {"role": "system", "content": system_prompt}
        ] + conversation_history[-MAX_CONVERSATION_HISTORY:]

        # API call to Groq
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": MODEL,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 800,  # Increased for detailed responses
                }
            )
            response.raise_for_status()
            
            response_data = response.json()
            ai_response = response_data['choices'][0]['message']['content'].strip()
            
            # Process and structure the response
            formatted_response = format_technical_response(ai_response)
            structured_response = structure_interview_response(formatted_response)
            
            # Add to conversation history
            conversation_history.append({
                "role": "assistant",
                "content": ai_response
            })

            return jsonify({
                'text': formatted_response,
                'structured_response': structured_response
            })

        except requests.RequestException as e:
            logger.error(f"API request error: {e}")
            return jsonify({'error': 'Failed to connect to AI service'}), 500

    except Exception as e:
        logger.error(f"Unexpected error in generate_response: {e}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

def analyze_question_type(question):
    """Analyze the type of interview question for better response formatting."""
    question_lower = question.lower()
    
    question_types = {
        'coding': ['implement', 'write a function', 'code', 'program'],
        'system_design': ['design', 'architecture', 'scale', 'system'],
        'conceptual': ['explain', 'what is', 'how does', 'describe'],
        'behavioral': ['tell me about a time', 'how would you handle', 'describe a situation']
    }
    
    for q_type, keywords in question_types.items():
        if any(keyword in question_lower for keyword in keywords):
            return q_type
    
    return 'general'

@app.route('/analyze_response', methods=['POST'])
def analyze_response():
    """Analyze user's practice response and provide feedback."""
    try:
        user_response = request.json.get('response', '').strip()
        question_type = request.json.get('question_type', 'technical')
        
        feedback = {
            'technical_accuracy': analyze_technical_accuracy(user_response),
            'communication_clarity': analyze_communication(user_response),
            'completeness': analyze_completeness(user_response),
            'improvement_suggestions': generate_improvements(user_response)
        }
        
        return jsonify(feedback)
        
    except Exception as e:
        logger.error(f"Error analyzing response: {e}")
        return jsonify({'error': 'Failed to analyze response'}), 500

def analyze_technical_accuracy(response):
    """Analyze technical accuracy of the response."""
    # Implementation would include checking for technical terms, concepts, and correctness
    pass

def analyze_communication(response):
    """Analyze communication clarity and structure."""
    # Implementation would include checking explanation clarity, examples, and organization
    pass

def analyze_completeness(response):
    """Check if all aspects of the question are addressed."""
    # Implementation would include checking for complete coverage of the topic
    pass

def generate_improvements(response):
    """Generate specific improvement suggestions."""
    # Implementation would include generating targeted improvement recommendations
    pass

@app.route('/reset', methods=['POST'])
def reset_conversation():
    global conversation_history
    conversation_history.clear()
    return jsonify({'status': 'Interview session reset successfully'})

if __name__ == '__main__':
    app.run(debug=True)