from flask import Flask, request, jsonify, g, abort
from werkzeug.utils import secure_filename
import os
import sqlite3
import logging
from langchain.llms import OpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.document_loaders import PyPDFLoader
from langchain.vectorstores import Chroma
from langchain.agents.agent_toolkits import (
    create_vectorstore_agent,
    VectorStoreToolkit,
    VectorStoreInfo
)

# Initialize the Flask app
app = Flask(__name__)
os.environ['OPENAI_API_KEY'] = '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'

# Create an instance of OpenAI LLM
llm = OpenAI(temperature=0.1, verbose=True)
embeddings = OpenAIEmbeddings()

# Define the directory where uploaded files will be stored
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

# Dictionary to store user-specific file paths
user_files = {}

# Database initialization
DATABASE = 'app.db'

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'db'):
        g.db.close()

# Logging configuration
logging.basicConfig(filename='app.log', level=logging.INFO)

# Check if a filename has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Error handling
@app.errorhandler(400)
@app.errorhandler(401)
@app.errorhandler(404)
@app.errorhandler(500)
def error_handler(error):
    # Log the error
    app.logger.error(error)
    
    # Return an error response to the client
    response = jsonify({'error': 'An error occurred'})
    response.status_code = error.code
    return response

# Endpoint to upload a file
@app.route('/upload', methods=['POST'])
def upload_file():
    user_id = request.form.get('user_id')
    
    # Input validation for user_id
    if not user_id:
        abort(400, 'User ID not provided')

    # Check if the POST request contains a file part
    if 'file' not in request.files:
        abort(400, 'No file part')

    file = request.files['file']

    # Check if the user did not select a file
    if file.filename == '':
        abort(400, 'No selected file')

    # Check if the file has an allowed extension
    if not allowed_file(file.filename):
        abort(400, 'Invalid file extension')

    user_dir = os.path.join(UPLOAD_FOLDER, user_id)
    os.makedirs(user_dir, exist_ok=True)

    # Delete the previous file if it exists
    previous_file_path = user_files.get(user_id)
    if previous_file_path:
        os.remove(previous_file_path)

    # Generate a secure filename and save the file to the user's directory
    filename = secure_filename(file.filename)
    file_path = os.path.join(user_dir, filename)
    file.save(file_path)

    # Store file metadata in the database
    db = get_db()
    db.execute('INSERT INTO files (user_id, filename) VALUES (?, ?)', (user_id, filename))
    db.commit()

    # Update the user's file path
    user_files[user_id] = file_path

    return jsonify({'message': 'File uploaded successfully', 'file_path': file_path})

# Endpoint to ask a question
@app.route('/ask', methods=['POST'])
def ask_question():
    user_id = request.form.get('user_id')
    
    # Input validation for user_id
    if not user_id:
        abort(400, 'User ID not provided')

    # Check if the user has uploaded a file
    user_file_path = user_files.get(user_id)
    if not user_file_path:
        abort(400, 'No file uploaded by the user')

    # ... (Code to process the uploaded file with Langchain and generate a response)

    # Process the uploaded file with Langchain
    loader = PyPDFLoader(user_file_path)
    pages = loader.load_and_split()
    store = Chroma.from_documents(pages, embeddings, collection_name=f'uploaded_report_{user_id}')

    vectorstore_info = VectorStoreInfo(
        name=f'uploaded_report_{user_id}',
        description=f'User-uploaded report for user {user_id}',
        vectorstore=store
    )

    toolkit = VectorStoreToolkit(vectorstore_info=vectorstore_info)
    agent_executor = create_vectorstore_agent(
        llm=llm,
        toolkit=toolkit,
        verbose=True
    )

    # Process the prompt (you can add error handling if needed)
    prompt = request.form.get('prompt')
    response = agent_executor.run(prompt)

    return jsonify({'response': response})

if __name__ == '__main__':
    init_db()  # Initialize the database
    app.run(debug=True)