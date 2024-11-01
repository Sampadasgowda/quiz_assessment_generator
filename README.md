# Quiz and Assessment Generator

A Flask web application that allows users to generate quizzes and assessments based on uploaded images or PDF documents. The app uses Optical Character Recognition (OCR) to extract text from images and PDFs, and then generates multiple-choice questions or open-ended questions on the detected topic using Google Gemini's generative AI capabilities.

## Features

- Upload images or PDFs to extract text.
- Generate multiple-choice quiz questions based on a specified topic or extracted text from uploaded files.
- Generate open-ended assessment questions based on the specified topic or extracted text.
- User-friendly web interface.

## Technologies Used

- Python
- Flask
- pytesseract (for OCR)
- PyPDF2 (for PDF text extraction)
- Google Gemini API (for question generation)
- HTML/CSS for frontend

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/your-repository-name.git
