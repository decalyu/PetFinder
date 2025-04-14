from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
from werkzeug.utils import secure_filename
from model import find_most_similar
import numpy as np  # 导入numpy处理数值类型

# 添加自定义JSON编码器解决float32序列化问题
class NumpyJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyJSONEncoder, self).default(obj)

app = Flask(__name__)
# 配置自定义JSON编码器
app.json_encoder = NumpyJSONEncoder
CORS(app)  # Enable cross-origin requests

# Configure upload folders
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
DATABASE_FOLDER = os.path.join(os.path.dirname(__file__), 'database')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATABASE_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit upload size to 16MB

# Allowed image formats
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

# Path to the pet information database file
PET_DB_FILE = os.path.join(os.path.dirname(__file__), 'database', 'pets_info.json')

def allowed_file(filename):
    """Check if file has an allowed image extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_pet_database():
    """Load pet information database"""
    if os.path.exists(PET_DB_FILE):
        try:
            with open(PET_DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading pet database: {e}")
            return {}
    return {}

@app.route('/')
def index():
    """Root endpoint providing API information"""
    return jsonify({
        'api_name': 'PetFinder API',
        'version': '1.0.0',
        'endpoints': {
            '/api/upload': 'POST - Upload pet photo and find similar pets',
            '/api/pets': 'GET - Get all pet information',
            '/api/initialize_db': 'GET - Initialize sample pet database',
            '/uploads/<filename>': 'GET - Get uploaded images',
            '/database/<filename>': 'GET - Get database images'
        }
    })

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve files from the uploads folder"""
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/database/<path:filename>')
def database_file(filename):
    """Serve files from the database folder"""
    return send_from_directory(DATABASE_FOLDER, filename)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Process uploaded pet image and find similar pets"""
    # Check if file is in the request
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    
    # Check if filename is empty
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Check if file type is allowed
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Use model to find top-3 most similar pets
        similar_paths, similarity_scores = find_most_similar(file_path, DATABASE_FOLDER, top_k=3)
        
        if similar_paths and len(similar_paths) > 0:
            # Load pet information database
            pet_database = load_pet_database()
            
            # Process each similar pet
            similar_pets = []
            for i, (path, score) in enumerate(zip(similar_paths, similarity_scores)):
                # Get filename of similar pet
                similar_filename = os.path.basename(path)
                
                # Get similar pet information
                pet_info = pet_database.get(similar_filename, {
                    'name': 'Unknown',
                    'owner_name': 'Unknown',
                    'contact': 'Unknown',
                    'description': 'No information available'
                })
                
                # Add to results list
                similar_pets.append({
                    'filename': similar_filename,
                    'similarity_score': score,
                    'pet_info': pet_info
                })
            
            # Return results
            return jsonify({
                'status': 'success',
                'message': 'File uploaded successfully',
                'uploaded_filename': filename,
                'similar_pets': similar_pets
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'No similar pets found'
            }), 404
    
    return jsonify({'error': 'Unsupported file format'}), 400

@app.route('/api/pets', methods=['GET'])
def get_all_pets():
    """Get all pet information"""
    pet_database = load_pet_database()
    return jsonify(pet_database)

@app.route('/api/initialize_db', methods=['GET'])
def initialize_db():
    """Initialize sample pet database - for demo purposes only"""
    try:
        # Check for images in the database folder
        image_files = [f for f in os.listdir(DATABASE_FOLDER) 
                      if f.lower().endswith(tuple(ALLOWED_EXTENSIONS))]
        
        if not image_files:
            return jsonify({
                'status': 'error',
                'message': 'No pet images found in database folder. Please add some images.'
            }), 400
            
        # Create sample pet breeds
        breeds = ["Golden Retriever", "Labrador", "Husky", "German Shepherd", 
                  "Poodle", "Bulldog", "Beagle", "Siamese Cat", "Persian Cat", 
                  "Maine Coon", "Ragdoll", "Bengal Cat", "Tabby Cat"]
        
        # Create sample information for each image
        pet_database = {}
        for idx, img_file in enumerate(image_files):
            breed = breeds[idx % len(breeds)]
            shelter_names = ["Happy Paws Rescue", "Second Chance Animal Shelter", "Golden Hearts Pet Sanctuary", "Safe Haven Animal Rescue", "Loving Friends Pet Center"]
            genders = ["Male", "Female"]
            
            pet_database[img_file] = {
                'name': f'Buddy {idx+1}',
                'gender': genders[idx % 2],
                'owner_name': f'Owner {idx+1}',
                'shelter_name': shelter_names[idx % 5],
                'contact': f'Shelter Hotline: (555) 123-{4000+idx}',
                'description': f'A lovely {breed}. Friendly and loves to play!',
                'breed': breed,
                'age': f'{(idx % 10) + 1} years',
                'location': f'{["123 Main St", "456 Oak Ave", "789 Pine Blvd", "101 Cedar Lane", "202 Maple Dr"][idx % 5]}, {["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"][idx % 5]}, USA'
            }
        
        # Ensure database directory exists
        os.makedirs(os.path.dirname(PET_DB_FILE), exist_ok=True)
        
        # Save to JSON file
        with open(PET_DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(pet_database, f, ensure_ascii=False, indent=4)
        
        return jsonify({
            'status': 'success',
            'message': f'Successfully initialized {len(pet_database)} pet records',
            'pets': pet_database
        })
    except Exception as e:
        app.logger.error(f"Error initializing database: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to initialize database: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5003)
