// src/features/mlb/components/PitcherMetrics/PitcherStatusIcon.js
const PitcherStatusIcon = ({ message }) => {
    if (!message || message.includes("No data available")) {
        return <span className="status-icon unknown" title="No data available">🚫</span>;
    }

    if (message.includes("COLD")) {
        return <span className="status-icon cold" title={message}>❄️</span>;
    }

    if (message.includes("HOT")) {
        return <span className="status-icon hot" title={message}>🔥</span>;
    }

    if (message.includes("CONSISTENT")) {
        if (message.includes("better")) {
            return <span className="status-icon consistent-positive" title={message}>🔴</span>;
        }
        if (message.includes("worse")) {
            return <span className="status-icon consistent-negative" title={message}>🔵</span>;
        }
        return <span className="status-icon consistent-neutral" title={message}>⚪</span>;
    }

    return <span className="status-icon unknown" title="Unknown status">🚫</span>;
};