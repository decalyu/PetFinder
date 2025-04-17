import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [dbInitialized, setDbInitialized] = useState(false);
  const [checkingDb, setCheckingDb] = useState(true);
  const [result, setResult] = useState(null);
  const resultRef = useRef(null);

  // Check database status
  const checkDbStatus = async () => {
    try {
      setCheckingDb(true);
      const response = await axios.get('http://localhost:5003/api/pets', {
        timeout: 5000,
        retry: 3,
        retryDelay: 1000
      });
      setDbInitialized(response.data && response.data.length > 0);
      setCheckingDb(false);
    } catch (error) {
      console.error('Database check error:', error);
      setError('Cannot connect to server. Please ensure the backend service is running on port 5003.');
      setCheckingDb(false);
    }
  };

  // Initialize database
  const initializeDb = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await axios.get('http://localhost:5003/api/initialize_db', {
        timeout: 10000,
        retry: 3,
        retryDelay: 1000
      });

      if (response.data.status === 'success') {
        setDbInitialized(true);
        setLoading(false);
      } else {
        setError(response.data.message || 'Failed to initialize database. Please try again.');
        setLoading(false);
      }
    } catch (error) {
      console.error('Initialize DB error:', error);
      if (error.response && error.response.data && error.response.data.message) {
        setError(error.response.data.message);
      } else if (error.message && error.message.includes('Network Error')) {
        setError('Server connection error. Please ensure the backend service is running on port 5003.');
      } else {
        setError('Failed to initialize database. Please try again.');
      }
      setLoading(false);
    }
  };

  useEffect(() => {
    checkDbStatus();
  }, []);

  // File selection handler
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    setError('');

    if (selectedFile) {
      if (!selectedFile.type.match('image.*')) {
        setError('Please select an image file.');
        setFile(null);
        setPreview('');
        return;
      }

      setFile(selectedFile);
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result);
      };
      reader.readAsDataURL(selectedFile);
    } else {
      setFile(null);
      setPreview('');
    }
  };

  // Form submission handler
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select an image first');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('image', file);

      const response = await axios.post('http://localhost:5003/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      if (response.data.status === 'success') {
        const petInfo = response.data.pet_infos[0];
        const similarityScore = response.data.similar_pets[0][1];
        setResult({ ...petInfo, similarity: similarityScore });
      } else {
        setError(response.data.message || 'Failed to process image');
      }
    } catch (error) {
      console.error('Upload error:', error);
      setError('An error occurred while processing your request');
    } finally {
      setLoading(false);
    }
  };

  // Reset form
  const resetForm = () => {
    setFile(null);
    setPreview('');
    setResult(null);
    setError('');
  };

  return (
    <div className="App">
      <header className="app-header">
        <div className="logo-container">
          <div className="logo">🐾</div>
        </div>
        <div className="title-container">
          <h1>PetFinder</h1>
          <p className="subtitle">
            <span className="accent">Lost</span> a pet or <span className="accent">found</span> one?
          </p>
        </div>
        <div className="header-decoration"></div>
      </header>

      <main className="app-content">
        <div className="column left-column">
          <section className="hero-section">
            <div className="hero-content">
              <h2>Find Missing Pets</h2>
              <p>Upload a pet photo and we'll search our database for similar pets. It might be your lost pet or help find a pet's owner!</p>
            </div>
            <div className="hero-images">
              <div className="pet-illustration dog"></div>
              <div className="pet-illustration cat"></div>
            </div>
            <div className="hero-decoration"></div>
          </section>

          <div className="card upload-card">
            <h2>📸 Upload Pet Photo</h2>

            {!dbInitialized && !loading && (
              <div className="db-init-section">
                <p>Before we start, we need to initialize the pet database.</p>
                <button
                  className="init-button"
                  onClick={initializeDb}
                  disabled={loading || checkingDb}
                >
                  {loading ? (
                    <>
                      <span className="button-spinner"></span>
                      Initializing...
                    </>
                  ) : 'Initialize Database'}
                </button>
                {checkingDb && <p className="status-message">Checking database status...</p>}
              </div>
            )}

            {dbInitialized && (
              <form className="upload-form" onSubmit={handleSubmit}>
                <div className="upload-container">
                  {!preview ? (
                    <label className="upload-placeholder">
                      <input
                        type="file"
                        onChange={handleFileChange}
                        accept="image/*"
                        disabled={loading}
                      />
                      <div className="upload-icon">📤</div>
                      <p>Click here to upload a photo<br />or drag and drop an image file</p>
                    </label>
                  ) : (
                    <div className="image-preview">
                      <div className="image-box">
                        <img src={preview} alt="Pet preview" />
                      </div>
                      <p className="file-name">{file?.name}</p>
                    </div>
                  )}
                </div>

                <div className="button-group">
                  <button
                    type="submit"
                    className="submit-button"
                    disabled={!file || loading || !dbInitialized}
                  >
                    {loading ? (
                      <>
                        <span className="button-spinner"></span>
                        Searching...
                      </>
                    ) : 'Find Similar Pets'}
                  </button>

                  {preview && (
                    <button
                      type="button"
                      className="reset-button"
                      onClick={resetForm}
                      disabled={loading}
                    >
                      Upload New Photo
                    </button>
                  )}
                </div>
              </form>
            )}

            {error && <div className="error-message">{error}</div>}
          </div>
        </div>

        <div className="column right-column">
          <div ref={resultRef} className="card result-card">
            <h2>🔍 Search Results</h2>

            {loading ? (
              <div className="loading-state">
                <div className="loading-spinner"></div>
                <p>Analyzing your image and searching for similar pets...</p>
              </div>
            ) : result ? (
              <div className="result-content">
                <div className="similar-pet-item">
                  <div className="image-comparison">
                    <div className="result-image-container">
                      <div className="image-box">
                        <img src={preview} alt="Your pet" />
                      </div>
                      <p className="image-label">Your Pet</p>
                    </div>

                    <div className="arrow">→</div>

                    <div className="result-image-container">
                      <div className="image-box">
                        <img src={`http://localhost:5003/database/24petconnect/images/${result.local_image}`} alt={`Similar pet`} />
                      </div>
                      <p className="image-label">Most Similar Pet</p>
                    </div>
                  </div>

                  <div className="result-details">
                    <h3>Pet Information</h3>
                    <div className="similarity-score">
                      <span className="score-label">Similarity Score</span>
                      <span className="score-value">{result.similarity ? `${(result.similarity * 100).toFixed(1)}%` : 'N/A'}</span>
                    </div>
                    <div className="pet-info">
                      <div className="info-item">
                        <span className="info-label">Name</span>
                        <span className="info-value">{result.name}</span>
                      </div>
                      <div className="info-item">
                        <span className="info-label">Gender</span>
                        <span className="info-value">{result.gender}</span>
                      </div>
                      <div className="info-item">
                        <span className="info-label">Age</span>
                        <span className="info-value">{result.age}</span>
                      </div>
                      <div className="info-item">
                        <span className="info-label">Breed</span>
                        <span className="info-value">{result.breed}</span>
                      </div>
                      <div className="info-item">
                        <span className="info-label">Location</span>
                        <span className="info-value">{result.location}</span>
                      </div>
                      <div className="info-item">
                        <span className="info-label">Address</span>
                        <span className="info-value">{result.address}</span>
                      </div>
                      <div className="info-item">
                        <span className="info-label">Phone</span>
                        <span className="info-value">{result.phone}</span>
                      </div>
                      <div className="info-item">
                        <span className="info-label">Website</span>
                        <span className="info-value">{result.website}</span>
                      </div>
                      <div className="info-item">
                        <span className="info-label">Days in Care</span>
                        <span className="info-value">{result.days_in_care}</span>
                      </div>
                      <div className="info-item">
                        <span className="info-label">Arrival Date</span>
                        <span className="info-value">{result.arrival_date}</span>
                      </div>
                      <div className="info-item">
                        <span className="info-label">Found Near</span>
                        <span className="info-value">{result.found_near}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="empty-state-minimal">
                <div className="empty-illustration"></div>
              </div>
            )}
          </div>

          {!result && !loading && (
            <div className="search-tips-container">
              <p className="search-guidance">Upload a pet photo to see matching results here.</p>
              <div className="tips-container">
                <div className="tip-badge">
                  <span className="tip-icon">💡</span>
                  <span>Clear face photos work best</span>
                </div>
                <div className="tip-badge">
                  <span className="tip-icon">🔍</span>
                  <span>We analyze pet features to find matches</span>
                </div>
              </div>
              <div className="dots-decoration"></div>
            </div>
          )}
        </div>
      </main>

      <footer className="app-footer">
        <div className="footer-decoration left"></div>
        <p>PetFinder &copy; 2023 - Helping reunite lost pets with their owners</p>
        <div className="footer-decoration right"></div>
      </footer>
    </div>
  );
}

export default App;