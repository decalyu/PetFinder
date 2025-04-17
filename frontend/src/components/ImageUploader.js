import React, { useState } from 'react';
import axios from 'axios';
import './ImageUploader.css';

const ImageUploader = ({ onUploadSuccess }) => {
    const [file, setFile] = useState(null);
    const [previewUrl, setPreviewUrl] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleFileChange = (e) => {
        const selectedFile = e.target.files[0];
        if (selectedFile) {
            if (selectedFile.type.startsWith('image/')) {
                setFile(selectedFile);
                setError('');
                const reader = new FileReader();
                reader.onloadend = () => {
                    setPreviewUrl(reader.result);
                };
                reader.readAsDataURL(selectedFile);
            } else {
                setError('Please select an image file (JPEG, PNG, etc.)');
                setFile(null);
                setPreviewUrl('');
            }
        }
    };

    const handleUpload = async () => {
        if (!file) {
            setError('Please select an image first');
            return;
        }

        setLoading(true);
        setError('');

        const formData = new FormData();
        formData.append('image', file);

        try {
            const response = await axios.post('http://localhost:5003/api/upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
                timeout: 30000,
                retry: 3,
                retryDelay: 1000
            });

            if (response.data.status === 'success') {
                onUploadSuccess(response.data);
            } else {
                setError(response.data.message || 'Upload failed. Please try again.');
            }
        } catch (error) {
            console.error('Upload error:', error);
            if (error.response && error.response.data && error.response.data.message) {
                setError(error.response.data.message);
            } else if (error.message && error.message.includes('Network Error')) {
                setError('Server connection error. Please ensure the backend service is running on port 5003.');
            } else {
                setError('Failed to upload image. Please try again.');
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="image-uploader">
            <div className="upload-area">
                <input
                    type="file"
                    accept="image/*"
                    onChange={handleFileChange}
                    disabled={loading}
                    className="file-input"
                />
                {previewUrl && (
                    <div className="preview-container">
                        <img src={previewUrl} alt="Preview" className="preview-image" />
                    </div>
                )}
            </div>

            {error && <div className="error-message">{error}</div>}

            <button
                onClick={handleUpload}
                disabled={!file || loading}
                className="upload-button"
            >
                {loading ? 'Uploading...' : 'Upload Image'}
            </button>
        </div>
    );
};

export default ImageUploader; 