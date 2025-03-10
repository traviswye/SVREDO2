import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../css/SlateDropdown.css';

const SlateDropdown = ({ onSlateSelect }) => {
    const [slates, setSlates] = useState([]);
    const [selectedSlate, setSelectedSlate] = useState(null);
    const [selectedDate, setSelectedDate] = useState(formatDate(new Date()));
    const [loading, setLoading] = useState(false);

    // Format date as YYYY-MM-DD
    function formatDate(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    useEffect(() => {
        const fetchSlates = async () => {
            setLoading(true);
            try {
                const response = await axios.get(`https://localhost:44346/api/DKPoolsMap/date/${selectedDate}`);
                const formattedSlates = response.data.map(slate => ({
                    ...slate,
                    displayText: `${slate.sport} - ${slate.startTime} - ${slate.totalGames} Games`
                }));
                setSlates(formattedSlates);

                // If there are slates and none is selected, select the first one
                if (formattedSlates.length > 0 && !selectedSlate) {
                    setSelectedSlate(formattedSlates[0]);
                    onSlateSelect(formattedSlates[0]);
                }
            } catch (error) {
                console.error('Error fetching slates:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchSlates();
    }, [selectedDate, onSlateSelect]);

    const handleSlateChange = (event) => {
        const selectedId = event.target.value;
        const slate = slates.find(s => s.id.toString() === selectedId);
        setSelectedSlate(slate);
        onSlateSelect(slate);
    };

    const handleDateChange = (event) => {
        setSelectedDate(event.target.value);
        setSelectedSlate(null); // Reset selected slate when date changes
        onSlateSelect(null);
    };

    // Adjust date by days (positive or negative)
    const adjustDate = (days) => {
        const currentDate = new Date(selectedDate);
        currentDate.setDate(currentDate.getDate() + days);
        setSelectedDate(formatDate(currentDate));
        setSelectedSlate(null);
        onSlateSelect(null);
    };

    return (
        <div className="slate-dropdown-container">
            <div className="date-selector">
                <button
                    className="date-nav-button"
                    onClick={() => adjustDate(-1)}
                    title="Previous Day"
                >
                    &larr;
                </button>
                <input
                    type="date"
                    value={selectedDate}
                    onChange={handleDateChange}
                    className="date-input"
                />
                <button
                    className="date-nav-button"
                    onClick={() => adjustDate(1)}
                    title="Next Day"
                >
                    &rarr;
                </button>
            </div>
            <div className="slate-selector">
                <select
                    onChange={handleSlateChange}
                    value={selectedSlate?.id || ''}
                    className="slate-select"
                    disabled={loading || slates.length === 0}
                >
                    <option value="">
                        {loading
                            ? 'Loading slates...'
                            : slates.length === 0
                                ? 'No slates available for selected date'
                                : 'Select a Slate'}
                    </option>
                    {slates.map(slate => (
                        <option key={slate.id} value={slate.id}>
                            {slate.displayText}
                        </option>
                    ))}
                </select>
            </div>
        </div>
    );
};

export default SlateDropdown;