// src/features/mlb/utils/pitcherMetricsUtils.js
export const formatDate = (date) => date.split("T")[0];

export const extractPercentage = (message) => {
    if (!message || message.includes("No data available")) return 0;
    const match = message.match(/([-+]?\d+(\.\d+)?)%/);
    return match ? parseFloat(match[1]) : 0;
};

export const extractStatus = (message) => {
    if (!message || message.includes("No data available")) return "Unknown";
    if (message.includes("COLD")) return "COLD";
    if (message.includes("HOT")) return "HOT";
    if (message.includes("CONSISTENT")) return "CONSISTENT";
    return "Unknown";
};