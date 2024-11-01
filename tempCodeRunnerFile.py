import os
from flask import Flask, request, render_template
import pytesseract
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv
from PyPDF2 import PdfReader

# Load environment variables from .env file
load_dotenv()

# Set your Gemini API Key from the .env file
api_key = os.getenv("GEMINI_API_KEY")
if api_key is None:
    raise ValueError("API key not found. Please set GEMINI_API_KEY in the .env file.")

genai.configure(api_key=api_key)

app = Flask(__name__)

# Specify the Tesseract executable path if necessary
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Create uploads directory if it doesn't exist
if not os.path.exists("uploads"):
    os.makedirs("uploads")

# Model configuration
generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "max_output_tokens": 2048,
    "response_mime_type": "text/plain",
}

# Initialize the Gemini model
model = genai.GenerativeModel(
    model_name="gemini-1.0-pro",
    generation_config=generation_config,
)

@app.context_processor
def utility_processor():
    return dict(enumerate=enumerate)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate-quiz", methods=["POST"])
def generate_quiz():
    try:
        quiz_type = request.form.get("quiz_type", "topic")
        topic = request.form.get("topic", "general knowledge")
        
        # Check if the quiz is image-based or PDF-based and process accordingly
        if quiz_type == "image":
            if 'image' in request.files and request.files['image'].filename != '':
                file = request.files['image']
                # Save the uploaded image temporarily
                file_path = os.path.join("uploads", file.filename)
                file.save(file_path)
                
                # Use Tesseract to extract text from the image
                text = pytesseract.image_to_string(Image.open(file_path))
                if text.strip():  # Check if extracted text is not empty
                    topic = text.strip()  # Use extracted text as the topic for quiz generation
                else:
                    return render_template('error.html', error="No text found in the uploaded image.")
        
        elif quiz_type == "pdf":
            if 'pdf' in request.files and request.files['pdf'].filename != '':
                pdf_file = request.files['pdf']
                pdf_path = os.path.join("uploads", pdf_file.filename)
                pdf_file.save(pdf_path)

                # Extract text from each page of the PDF
                pdf_text = ""
                try:
                    reader = PdfReader(pdf_path)
                    for page in reader.pages:
                        pdf_text += page.extract_text() or ""
                except Exception:
                    return render_template('error.html', error="Failed to read the PDF. Make sure it contains text.")
                
                # Use the extracted PDF text as the topic
                if pdf_text.strip():
                    topic = pdf_text.strip()
                else:
                    return render_template('error.html', error="No text found in the PDF.")

        # Update the prompt to generate MCQs
        prompt = (
            f"Generate 5 multiple-choice quiz questions on the topic '{topic}'. "
            "Each question should have 4 answer options, one of which is correct. "
            "Format the output as follows:\n"
            "Q1: Question 1?\nA1: Correct Answer 1.\nA2: Incorrect Answer 1.\nA3: Incorrect Answer 2.\nA4: Incorrect Answer 3.\n"
            "Q2: Question 2?\nA1: Correct Answer 2.\nA2: Incorrect Answer 1.\nA3: Incorrect Answer 2.\nA4: Incorrect Answer 3.\n"
            "Q3: Question 3?\nA1: Correct Answer 3.\nA2: Incorrect Answer 1.\nA3: Incorrect Answer 2.\nA4: Incorrect Answer 3.\n"
            "Q4: Question 4?\nA1: Correct Answer 4.\nA2: Incorrect Answer 1.\nA3: Incorrect Answer 2.\nA4: Incorrect Answer 3.\n"
            "Q5: Question 5?\nA1: Correct Answer 5.\nA2: Incorrect Answer 1.\nA3: Incorrect Answer 2.\nA4: Incorrect Answer 3."
        )

        # Generate the quiz questions
        response = model.start_chat(history=[]).send_message(prompt)
        quiz_data = response.text.strip().split("\n")

        # Process quiz data into structured format
        questions = []
        current_question = None
        options = []
        correct_answers = []

        for line in quiz_data:
            if line.startswith("Q"):  # Identify the start of a new question
                if current_question:  # Append the previous question's data
                    questions.append({"question_text": current_question, "choices": options})
                    options = []  # Reset options list for the next question
                current_question = line  # Update the current question text
            elif line.startswith("A"):
                option_text = line.split(": ", 1)[1]  # Option text after "A1: "
                options.append(option_text)
                if line.startswith("A1:"):  # Assume A1 is the correct answer
                    correct_answers.append(option_text)

        # Append the last question if it exists
        if current_question:
            questions.append({"question_text": current_question, "choices": options})

        return render_template('quiz.html', questions=questions, correct_answers=correct_answers)
    
    except Exception as e:
        return render_template('error.html', error=f"Error: {str(e)}")

@app.route("/evaluate", methods=["POST"])
def evaluate():
    # Retrieve correct answers
    correct_answers = request.form.get('correct_answers').split(',')
    # Retrieve selected answers for each question
    selected_answers = [
        request.form.get(f'answer_{i}', '') for i in range(len(correct_answers))
    ]

    feedback = []
    score = 0

    for selected, correct in zip(selected_answers, correct_answers):
        if selected == correct:
            feedback.append(f"Your answer: {selected}<br>Correct answer: {correct}.")
            score += 1
        else:
            feedback.append(f"Your answer: {selected}<br>Correct answer: {correct}.")

    total_questions = len(correct_answers)
    
    return render_template('result.html', score=score, total_questions=total_questions, feedback=feedback)

if __name__ == "__main__":
    app.run(debug=True)
