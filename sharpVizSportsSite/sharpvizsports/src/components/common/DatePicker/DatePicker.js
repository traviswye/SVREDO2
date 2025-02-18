const DatePicker = ({
    selectedDate,
    onChange,
    onPrevious,
    onNext,
    prevLabel = "< Prev",
    nextLabel = "Next >",
}) => {
    return (
        <div className="date-picker">
            <button onClick={onPrevious} className="date-nav-button">
                {prevLabel}
            </button>
            <input
                type="date"
                value={selectedDate}
                onChange={(e) => onChange(e.target.value)}
                className="date-input"
            />
            <button onClick={onNext} className="date-nav-button">
                {nextLabel}
            </button>
        </div>
    );
};

export default DatePicker;