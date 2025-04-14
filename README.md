# PetFinder

An AI-powered pet image similarity search system that helps match pets with similar appearances.

## Features

- 🔍 Fast and accurate pet image similarity search
- 🖼️ Support for multiple image formats (JPG, PNG, JPEG, WEBP)
- 🚀 Efficient caching system for quick responses
- 🎯 Advanced feature extraction using ResNet101
- 💻 User-friendly web interface

## Tech Stack

### Backend
- Python 3.11
- Flask
- PyTorch
- OpenCV
- NumPy

### Frontend
- React
- Axios
- Material-UI

## Installation

1. Clone the repository:
```bash
git clone https://github.com/decalyu/PetFinder.git
cd PetFinder
```

2. Set up the backend:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up the frontend:
```bash
cd frontend
npm install
```

## Usage

1. Start the backend server:
```bash
cd backend
python app.py
```

2. Start the frontend development server:
```bash
cd frontend
npm start
```

3. Open http://localhost:3000 in your browser

## API Endpoints

- `POST /api/upload` - Upload and find similar pets
- `GET /api/pets` - Get all pets in database
- `GET /api/initialize_db` - Initialize the database

## Model Details

- Base model: ResNet101 (pretrained)
- Feature extraction: 2048-dimensional vectors
- Similarity metric: Combined cosine similarity and color histogram
- Cache system: Pickle-based feature caching

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- PyTorch team for the pretrained models
- OpenCV community for image processing tools
- React community for frontend framework
