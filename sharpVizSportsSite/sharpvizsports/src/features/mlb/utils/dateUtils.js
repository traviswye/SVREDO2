// src/utils/dateUtils.js
export const formatDate = (date) => {
    if (typeof date === 'string') {
        // If it's already a string, ensure it's in the right format
        const parsedDate = new Date(date);
        return parsedDate.toISOString().split('T')[0];
    }

    // If it's a Date object
    return date.toISOString().split('T')[0];
};

export const getShortDate = (date) => {
    // Converts YYYY-MM-DD to YY-MM-DD
    const formattedDate = formatDate(date);
    return formattedDate.substring(2);
};

export const addDays = (date, days) => {
    const result = new Date(date);
    result.setDate(result.getDate() + days);
    return formatDate(result);
};