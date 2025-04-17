import React from 'react';
import './PetInfo.css';

const PetInfo = ({ pet }) => {
    if (!pet) return null;

    return (
        <div className="pet-info">
            <h2>Pet Information</h2>
            <div className="info-grid">
                <div className="info-item">
                    <span className="label">NAME</span>
                    <span className="value">{pet.name || 'Unknown'}</span>
                </div>
                <div className="info-item">
                    <span className="label">GENDER</span>
                    <span className="value">{pet.gender || 'Unknown'}</span>
                </div>
                <div className="info-item">
                    <span className="label">AGE</span>
                    <span className="value">{pet.age || 'Unknown'}</span>
                </div>
                <div className="info-item">
                    <span className="label">SHELTER</span>
                    <span className="value">{pet.location || 'Unknown'}</span>
                </div>
                <div className="info-item">
                    <span className="label">LOCATION</span>
                    <span className="value">{pet.address || 'Unknown'}</span>
                </div>
                <div className="info-item">
                    <span className="label">CONTACT</span>
                    <span className="value">Shelter Hotline: {pet.phone || 'Unknown'}</span>
                </div>
                <div className="info-item">
                    <span className="label">BREED</span>
                    <span className="value">{pet.breed || 'Unknown'}</span>
                </div>
                <div className="info-item">
                    <span className="label">DAYS IN CARE</span>
                    <span className="value">{pet.days_in_care || 'Unknown'}</span>
                </div>
                <div className="info-item">
                    <span className="label">ARRIVAL DATE</span>
                    <span className="value">{pet.arrival_date || 'Unknown'}</span>
                </div>
                <div className="info-item">
                    <span className="label">FOUND NEAR</span>
                    <span className="value">{pet.found_near || 'Unknown'}</span>
                </div>
            </div>
        </div>
    );
};

export default PetInfo; 