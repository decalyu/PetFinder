from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
from werkzeug.utils import secure_filename
import numpy as np
import cv2
from PIL import Image
import logging
from pathlib import Path
from model import find_most_similar

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
app.config['DATABASE_FOLDER'] = DATABASE_FOLDER
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
    pet_info_file = os.path.join(os.path.dirname(__file__), 'database', '24petconnect', 'pets_info.json')
    if os.path.exists(pet_info_file):
        try:
            with open(pet_info_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        except Exception as e:
            logger.error(f"Error loading pet database: {e}")
            return []
    return []

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
    try:
        return send_from_directory(app.config['DATABASE_FOLDER'], filename)
    except Exception as e:
        logger.error(f"Error serving database file {filename}: {str(e)}")
        return jsonify({'status': 'error', 'message': 'File not found'}), 404

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload and find similar pets"""
    try:
        logger.info("Received upload request")
        logger.info(f"Request files: {request.files}")
        
        if 'image' not in request.files:
            logger.error("No 'image' field in request.files")
            return jsonify({'status': 'error', 'message': 'No file uploaded'}), 400
            
        file = request.files['image']
        logger.info(f"File received: {file.filename}")
        
        if file.filename == '':
            logger.error("Empty filename")
            return jsonify({'status': 'error', 'message': 'No file selected'}), 400
            
        if not allowed_file(file.filename):
            logger.error(f"Invalid file type: {file.filename}")
            return jsonify({'status': 'error', 'message': 'File type not allowed'}), 400
            
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        logger.info(f"Saving file to: {filepath}")
        
        file.save(filepath)
        logger.info("File saved successfully")
        
        # 查找相似宠物
        try:
            # 使用模型查找最相似的宠物图片
            images_dir = os.path.join(app.config['DATABASE_FOLDER'], '24petconnect', 'images')
            similar_paths, similarity_scores = find_most_similar(filepath, images_dir)
            
            if similar_paths:
                logger.info(f"Found similar pets: {similar_paths}")
                
                # 加载宠物数据库
                pets_info = load_pet_database()
                
                # 查找匹配的宠物信息
                pet_infos = []
                for path in similar_paths:
                    image_name = os.path.basename(path)
                    pet_info = next((pet for pet in pets_info if pet.get('local_image') == image_name), None)
                    if pet_info:
                        pet_infos.append(pet_info)
                
                if pet_infos:
                    logger.info(f"Found pet infos: {pet_infos}")
                    return jsonify({
                        'status': 'success',
                        'pet_infos': pet_infos,
                        'similar_pets': list(zip([os.path.basename(p) for p in similar_paths], [float(score) for score in similarity_scores]))
                    })
                else:
                    logger.error(f"No pet info found for images: {[os.path.basename(p) for p in similar_paths]}")
                    return jsonify({'status': 'error', 'message': 'No matching pet information found'}), 404
            else:
                logger.error("No similar pets found")
                return jsonify({'status': 'error', 'message': 'No similar pets found'}), 404
                
        except Exception as e:
            logger.error(f"Error finding similar pets: {str(e)}")
            return jsonify({'status': 'error', 'message': 'Failed to find similar pets'}), 500
            
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

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
        pet_database = []
        for idx, img_file in enumerate(image_files):
            breed = breeds[idx % len(breeds)]
            shelter_names = ["Happy Paws Rescue", "Second Chance Animal Shelter", "Golden Hearts Pet Sanctuary", "Safe Haven Animal Rescue", "Loving Friends Pet Center"]
            genders = ["Male", "Female"]
            
            pet_info = {
                'name': f'Buddy {idx+1}',
                'gender': genders[idx % 2],
                'owner_name': f'Owner {idx+1}',
                'shelter_name': shelter_names[idx % 5],
                'contact': f'Shelter Hotline: (555) 123-{4000+idx}',
                'description': f'A lovely {breed}. Friendly and loves to play!',
                'breed': breed,
                'age': f'{(idx % 10) + 1} years',
                'location': f'{["123 Main St", "456 Oak Ave", "789 Pine Blvd", "101 Cedar Lane", "202 Maple Dr"][idx % 5]}, {["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"][idx % 5]}, USA',
                'local_image': img_file
            }
            pet_database.append(pet_info)
        
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
        logger.error(f"Error initializing database: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to initialize database: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5003)
