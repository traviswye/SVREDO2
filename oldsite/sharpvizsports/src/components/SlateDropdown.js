import React, { useState, useEffect } from 'react';
import axios from 'axios';

const SlateDropdown = ({ onSlateSelect }) => {
    const [slates, setSlates] = useState([]);
    const [selectedSlate, setSelectedSlate] = useState(null);

    useEffect(() => {
        const fetchSlates = async () => {
            try {
                // TODO: Replace with dynamic date
                const response = await axios.get('https://localhost:44346/api/DKPoolsMap/date/2025-02-13');
                const formattedSlates = response.data.map(slate => ({
                    ...slate,
                    displayText: `${slate.sport} - ${slate.startTime} - ${slate.totalGames} Games`
                }));
                setSlates(formattedSlates);
            } catch (error) {
                console.error('Error fetching slates:', error);
            }
        };

        fetchSlates();
    }, []);

    const handleSlateChange = (event) => {
        const selectedId = event.target.value;
        const slate = slates.find(s => s.id.toString() === selectedId);
        setSelectedSlate(slate);
        onSlateSelect(slate);
    };

    return (
        <div className="slate-dropdown">
            <select
                onChange={handleSlateChange}
                value={selectedSlate?.id || ''}
            >
                <option value="">Select a Slate</option>
                {slates.map(slate => (
                    <option key={slate.id} value={slate.id}>
                        {slate.displayText}
                    </option>
                ))}
            </select>
        </div>
    );
};

export default SlateDropdown;