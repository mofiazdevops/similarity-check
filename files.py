import os
import requests
import pdfplumber
import docx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from flask import Flask, request, jsonify

app = Flask(__name__)

# Directory to store downloaded files
download_dir = './downloaded_docs'
os.makedirs(download_dir, exist_ok=True)

# Step 1: Download files from the API
def download_files():
    url = "https://portalteam.org/api/files"
    response = requests.get(url)
    files = response.json().get('data', [])

    # Download each file
    for file_info in files:
        file_name = file_info['file_name']
        file_link = file_info['file_link']

        file_response = requests.get(file_link)
        file_path = os.path.join(download_dir, file_name)

        # Save the file locally
        with open(file_path, 'wb') as file:
            file.write(file_response.content)

        print(f"Downloaded {file_name}")

# Step 2: Extract text from PDF files
def extract_text_from_pdf(file_path):
    with pdfplumber.open(file_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text()
    return text

# Step 3: Extract text from DOCX files
def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    text = ""
    for para in doc.paragraphs:
        text += para.text
    return text

# Step 4: Extract text from a file (PDF or DOCX)
def extract_text(file_path):
    if file_path.lower().endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    elif file_path.lower().endswith(".docx"):
        return extract_text_from_docx(file_path)
    else:
        return ""

# Step 5: Compare the input document with local documents to check similarity
def compare_document_with_local(input_file_path, local_directory):
    input_text = extract_text(input_file_path)
    
    if not input_text:
        return "Error: Unable to extract text from input file."
    
    local_files_texts = []
    local_files = []

    for file_name in os.listdir(local_directory):
        file_path = os.path.join(local_directory, file_name)
        local_text = extract_text(file_path)
        
        if local_text:
            local_files_texts.append(local_text)
            local_files.append(file_path)
    
    # Calculate cosine similarity using TF-IDF Vectorizer
    vectorizer = TfidfVectorizer().fit_transform([input_text] + local_files_texts)
    similarity_matrix = cosine_similarity(vectorizer[0:1], vectorizer[1:])

    # Calculate overall similarity
    overall_similarity = similarity_matrix.mean()
    
    # Prepare results with breakdown for each document
    breakdown = []
    for i, sim_score in enumerate(similarity_matrix.flatten()):
        breakdown.append({
            'document': local_files[i],
            'similarity_percentage': round(sim_score * 100, 2),
        })
    
    return {
        'overall_similarity_percentage': round(overall_similarity * 100, 2),
        'breakdown': breakdown
    }

# Step 6: Create the Flask API
@app.route('/check_similarity', methods=['POST'])
def check_similarity():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Save the uploaded file temporarily
    input_file_path = './temp_uploaded_file'
    file.save(input_file_path)

    # Compare the document and get results
    result = compare_document_with_local(input_file_path, download_dir)
    
    return jsonify(result)

if __name__ == '__main__':
    # Step 7: Download files when the app starts
    download_files()

    # Run the Flask app
    app.run(debug=True)
