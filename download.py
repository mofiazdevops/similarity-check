from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from docx import Document
from fpdf import FPDF
from sklearn.feature_extraction.text import CountVectorizer
import os
import requests
import base64

download_dir = './downloaded_docs'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}

# Flask app initialization
app = Flask(__name__)

def download_files(download_dir):
    # Ensure the download directory exists
    os.makedirs(download_dir, exist_ok=True)

    url = "https://portalteam.org/api/download_files"
    response = requests.get(url)
    if response.status_code != 200:
        print("Failed to retrieve the file list")
        return

    files = response.json().get('data', [])
    
    # Download only new files
    for file_info in files:
        file_name = file_info['file_name']
        file_link = file_info['file_link']
        file_path = os.path.join(download_dir, file_name)

        # Check if the file already exists
        if os.path.exists(file_path):
            print(f"Skipping {file_name} (already exists)")
            continue

        # Download and save the new file
        file_response = requests.get(file_link)
        if file_response.status_code == 200:
            with open(file_path, 'wb') as file:
                file.write(file_response.content)
            print(f"Downloaded {file_name}")
        else:
            print(f"Failed to download {file_name}")

if __name__ == '__main__':
    download_files(download_dir)
    app.run(debug=True, host='0.0.0.0', port=8010)