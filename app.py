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
                file_path = os.path.join("uploads", file.filename)
                file.save(file_path)
                text = pytesseract.image_to_string(Image.open(file_path))
                if text.strip():
                    topic = text.strip()
                else:
                    return render_template('error.html', error="No text found in the uploaded image.")

        elif quiz_type == "pdf":
            if 'pdf' in request.files and request.files['pdf'].filename != '':
                pdf_file = request.files['pdf']
                pdf_path = os.path.join("uploads", pdf_file.filename)
                pdf_file.save(pdf_path)

                pdf_text = ""
                try:
                    reader = PdfReader(pdf_path)
                    for page in reader.pages:
                        pdf_text += page.extract_text() or ""
                except Exception:
                    return render_template('error.html', error="Failed to read the PDF.")

                if pdf_text.strip():
                    topic = pdf_text.strip()
                else:
                    return render_template('error.html', error="No text found in the PDF.")

        # Prepare the prompt for quiz generation
        prompt = (
            f"Generate 10 multiple-choice quiz questions on the topic '{topic}'. "
            "Each question should have 4 answer options, one of which is correct. "
            "Format the output as follows:\n"
            "Q1: Question 1?\nA1: Correct Answer 1.\nA2: Incorrect Answer 1.\nA3: Incorrect Answer 2.\nA4: Incorrect Answer 3.\n"
            "Q2: Question 2?\nA1: Correct Answer 2.\nA2: Incorrect Answer 1.\nA3: Incorrect Answer 2.\nA4: Incorrect Answer 3.\n"
            "Q3: Question 3?\nA1: Correct Answer 3.\nA2: Incorrect Answer 1.\nA3: Incorrect Answer 2.\nA4: Incorrect Answer 3.\n"
            "Q4: Question 4?\nA1: Correct Answer 4.\nA2: Incorrect Answer 1.\nA3: Incorrect Answer 2.\nA4: Incorrect Answer 3.\n"
            "Q5: Question 4?\nA1: Correct Answer 4.\nA2: Incorrect Answer 1.\nA3: Incorrect Answer 2.\nA4: Incorrect Answer 3.\n"
            "Q6: Question 4?\nA1: Correct Answer 4.\nA2: Incorrect Answer 1.\nA3: Incorrect Answer 2.\nA4: Incorrect Answer 3.\n"
            "Q7: Question 4?\nA1: Correct Answer 4.\nA2: Incorrect Answer 1.\nA3: Incorrect Answer 2.\nA4: Incorrect Answer 3.\n"
            "Q8: Question 4?\nA1: Correct Answer 4.\nA2: Incorrect Answer 1.\nA3: Incorrect Answer 2.\nA4: Incorrect Answer 3.\n"
            "Q9: Question 4?\nA1: Correct Answer 4.\nA2: Incorrect Answer 1.\nA3: Incorrect Answer 2.\nA4: Incorrect Answer 3.\n"
            "Q10: Question 5?\nA1: Correct Answer 5.\nA2: Incorrect Answer 1.\nA3: Incorrect Answer 2.\nA4: Incorrect Answer 3."
        )

        response = model.start_chat(history=[]).send_message(prompt)
        quiz_data = response.text.strip().split("\n")

        # Check the model's response
        print("Raw Response from Model:", quiz_data)  # Debugging line

        questions = []
        current_question = None
        options = []
        correct_answers = []

        for line in quiz_data:
            line = line.strip()
            if line.startswith("Q"):  # Indicates a new question
                if current_question is not None:  # Save the previous question
                    questions.append({
                        "question_text": current_question,
                        "choices": options,
                        "correct_answer": correct_answers[-1]  # Get the last correct answer added
                    })
                    options = []
                current_question = line  # Update to the current question
            elif line.startswith("A"):  # Indicates an answer option
                option_text = line.split(": ", 1)[1]  # Get the answer option text
                options.append(option_text)
                if line.startswith("A1:"):  # Assuming A1 is always the correct answer
                    correct_answers.append(option_text)

        # Append the last question if exists
        if current_question:
            questions.append({
                "question_text": current_question,
                "choices": options,
                "correct_answer": correct_answers[-1] if correct_answers else None  # Handle last question's correct answer
            })

        print("Processed Questions:", questions)  # Debugging line

        return render_template('quiz.html', questions=questions)

    except Exception as e:
        return render_template('error.html', error=f"Error: {str(e)}")

@app.route("/generate-assessment", methods=["POST"])
def generate_assessment():
    try:
        topic = request.form.get("assessment_topic", "general knowledge")

        # Check if an image is uploaded
        if 'image' in request.files and request.files['image'].filename != '':
            file = request.files['image']
            file_path = os.path.join("uploads", file.filename)
            file.save(file_path)
            text = pytesseract.image_to_string(Image.open(file_path))
            if text.strip():
                topic = text.strip()
            else:
                return render_template('error.html', error="No text found in the uploaded image.")

        # Check if a PDF is uploaded
        elif 'pdf' in request.files and request.files['pdf'].filename != '':
            pdf_file = request.files['pdf']
            pdf_path = os.path.join("uploads", pdf_file.filename)
            pdf_file.save(pdf_path)

            pdf_text = ""
            try:
                reader = PdfReader(pdf_path)
                for page in reader.pages:
                    pdf_text += page.extract_text() or ""
            except Exception:
                return render_template('error.html', error="Failed to read the PDF.")

            if pdf_text.strip():
                topic = pdf_text.strip()
            else:
                return render_template('error.html', error="No text found in the PDF.")

        # Prepare the prompt for assessment generation without asterisks
        prompt = (
            f"Generate 10 open-ended assessment questions on the topic '{topic}'. "
            "Each question should be in plain text and not require any formatting."
        )

        response = model.start_chat(history=[]).send_message(prompt)
        assessment_data = response.text.strip().split("\n")

        # Directly store each question as plain text
        questions = [line.strip() for line in assessment_data if line.strip()]

        return render_template('assessment.html', questions=questions)

    except Exception as e:
        return render_template('error.html', error=f"Error: {str(e)}")


if __name__ == "__main__":
    app.run(debug=True)
