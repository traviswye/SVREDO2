import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../css/SlateDropdown.css';

const SlateDropdown = ({ onSlateSelect }) => {
    const [slates, setSlates] = useState([]);
    const [selectedSlate, setSelectedSlate] = useState(null);
    const [selectedDate, setSelectedDate] = useState(formatDate(new Date()));
    const [loading, setLoading] = useState(false);
    const [displayDate, setDisplayDate] = useState(selectedDate); // Add separate state for the displayed date

    // Format date as YYYY-MM-DD
    function formatDate(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    // Parse a date string safely
    function parseDate(dateString) {
        // Create a date at noon to avoid timezone issues
        const parts = dateString.split('-');
        if (parts.length !== 3) return new Date(); // Default to today if format is wrong

        return new Date(
            parseInt(parts[0], 10),
            parseInt(parts[1], 10) - 1, // Month is 0-indexed in JS
            parseInt(parts[2], 10),
            12, 0, 0 // Noon to avoid DST issues
        );
    }

    useEffect(() => {
        fetchSlates();
    }, [selectedDate]);

    const fetchSlates = async () => {
        setLoading(true);
        try {
            console.log(`Fetching slates for date: ${selectedDate}`);
            const response = await axios.get(`https://localhost:44346/api/DKPoolsMap/date/${selectedDate}`);

            const formattedSlates = response.data.map(slate => ({
                ...slate,
                displayText: `${slate.sport} - ${slate.startTime} - ${slate.totalGames || 0} Games`
            }));

            setSlates(formattedSlates);

            // If there are slates and none is selected, select the first one
            if (formattedSlates.length > 0 && !selectedSlate) {
                setSelectedSlate(formattedSlates[0]);
                onSlateSelect(formattedSlates[0]);
            } else if (formattedSlates.length === 0) {
                // Clear selection if no slates available
                setSelectedSlate(null);
                onSlateSelect(null);
            }

            // Update the display date to match the selected date
            setDisplayDate(selectedDate);
        } catch (error) {
            console.error('Error fetching slates:', error);
            // Still update display date even if there's an error
            setDisplayDate(selectedDate);
        } finally {
            setLoading(false);
        }
    };

    const handleSlateChange = (event) => {
        const selectedId = event.target.value;
        const slate = slates.find(s => s.id.toString() === selectedId);
        setSelectedSlate(slate);
        onSlateSelect(slate);
    };

    const handleDateChange = (event) => {
        const newDate = event.target.value;
        console.log(`Date changed from input: ${selectedDate} -> ${newDate}`);
        setSelectedDate(newDate);
        setSelectedSlate(null);
        onSlateSelect(null);
    };

    // Adjust date by days (positive or negative)
    const adjustDate = (days) => {
        const currentDate = parseDate(selectedDate);
        currentDate.setDate(currentDate.getDate() + days);
        const newDate = formatDate(currentDate);

        console.log(`Date adjusted by ${days} days: ${selectedDate} -> ${newDate}`);

        setSelectedDate(newDate);
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
                    value={displayDate} // Use displayDate for the input
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