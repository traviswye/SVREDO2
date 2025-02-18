import React, { useEffect, useState } from "react";
import "../css/DataBox.css";

const HitterTempTracking = ({ title, subtitle, date }) => {
  const [data, setData] = useState([]);
  const [filteredData, setFilteredData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortConfig, setSortConfig] = useState({ key: "currentTemp", direction: "desc" });
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [tempTrackingResponse, trailingGameLogResponse] = await Promise.all([
          fetch(`https://localhost:44346/api/HitterTempTracking/last7Days?targetDate=${date}`),
          fetch(`https://localhost:44346/api/TrailingGameLogSplits/last7G`),
        ]);

        const tempTrackingData = await tempTrackingResponse.json();
        const trailingGameLogData = await trailingGameLogResponse.json();

        const trailingGameLogLookup = trailingGameLogData.reduce((acc, log) => {
          acc[log.bbrefId] = log;
          return acc;
        }, {});

        const mergedData = tempTrackingData
          .filter((temp) => trailingGameLogLookup[temp.bbrefId])
          .map((temp) => {
            const log = trailingGameLogLookup[temp.bbrefId];
            return {
              date: temp.date.split("T")[0],
              bbrefId: temp.bbrefId,
              team: temp.team,
              currentTemp: parseFloat(temp.currentTemp).toFixed(2),
              trailingTemp1: parseFloat(temp.trailingTemp1).toFixed(2),
              trailingTemp2: parseFloat(temp.trailingTemp2).toFixed(2),
              trailingTemp3: parseFloat(temp.trailingTemp3).toFixed(2),
              trailingTemp4: parseFloat(temp.trailingTemp4).toFixed(2),
              trailingTemp5: parseFloat(temp.trailingTemp5).toFixed(2),
              trailingTemp6: parseFloat(temp.trailingTemp6).toFixed(2),
              splitParkFactor: parseFloat(log.splitParkFactor).toFixed(2),
              g: log.g,
              pa: log.pa,
              hr: log.hr,
              ba: parseFloat(log.ba).toFixed(3),
              ops: parseFloat(log.ops).toFixed(3),
              homeGames: log.homeGames,
              awayGames: log.awayGames,
            };
          });

        const sortedData = mergedData.sort((a, b) => b.currentTemp - a.currentTemp);

        setData(sortedData);
        setFilteredData(sortedData);
      } catch (error) {
        console.error("Error fetching hitter temperature data:", error);
        setError("Failed to fetch hitter temperature data.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [date]);

  const handleSort = (key) => {
    const direction = sortConfig.key === key && sortConfig.direction === "asc" ? "desc" : "asc";
    setSortConfig({ key, direction });

    const sortedData = [...filteredData].sort((a, b) => {
      if (typeof a[key] === "number" && typeof b[key] === "number") {
        return direction === "asc" ? a[key] - b[key] : b[key] - a[key];
      }
      return direction === "asc"
        ? a[key].localeCompare(b[key])
        : b[key].localeCompare(a[key]);
    });

    setFilteredData(sortedData);
  };

  const handleSearch = (e) => {
    const query = e.target.value.toLowerCase();
    setSearchQuery(query);

    const filtered = data.filter((row) =>
      row.bbrefId.toLowerCase().includes(query)
    );

    setFilteredData(filtered);
  };

  const handleClearSearch = () => {
    setSearchQuery("");
    setFilteredData(data);
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (data.length === 0) return <div>No data available</div>;

  return (
    <div className="data-box-container">
      <div className="data-box-header">
        <div>
          <div className="data-box-title">{title}</div>
          <div className="data-box-subtitle">{subtitle}</div>
        </div>
        {/* Search Bar */}
        <div className="search-bar-container">
          <div className="search-wrapper">
            <input
              type="text"
              placeholder="Search by Player ID"
              value={searchQuery}
              onChange={handleSearch}
              className="search-bar"
            />
            {searchQuery && (
              <button className="clear-button" onClick={handleClearSearch}>
                ✖
              </button>
            )}
          </div>
        </div>
      </div>
      <div className="data-box-scrollable">
        <table className="data-box-table">
          <thead>
            <tr>
              <th onClick={() => handleSort("date")}>Date</th>
              <th onClick={() => handleSort("bbrefId")}>Player ID</th>
              <th onClick={() => handleSort("team")}>Team</th>
              <th onClick={() => handleSort("currentTemp")}>Current Temp</th>
              <th onClick={() => handleSort("trailingTemp1")}>Trailing Temp 1</th>
              <th onClick={() => handleSort("trailingTemp2")}>Trailing Temp 2</th>
              <th onClick={() => handleSort("trailingTemp3")}>Trailing Temp 3</th>
              <th onClick={() => handleSort("trailingTemp4")}>Trailing Temp 4</th>
              <th onClick={() => handleSort("trailingTemp5")}>Trailing Temp 5</th>
              <th onClick={() => handleSort("trailingTemp6")}>Trailing Temp 6</th>
              <th onClick={() => handleSort("splitParkFactor")}>Park Factor</th>
              <th onClick={() => handleSort("g")}>G</th>
              <th onClick={() => handleSort("pa")}>PA</th>
              <th onClick={() => handleSort("hr")}>HR</th>
              <th onClick={() => handleSort("ba")}>BA</th>
              <th onClick={() => handleSort("ops")}>OPS</th>
              <th onClick={() => handleSort("homeGames")}>Home Games</th>
              <th onClick={() => handleSort("awayGames")}>Away Games</th>
            </tr>
          </thead>
          <tbody>
            {filteredData.map((row, index) => (
              <tr key={index}>
                <td>{row.date}</td>
                <td>
                  <a
                    href={`https://www.baseball-reference.com/players/${row.bbrefId[0]}/${row.bbrefId}.shtml`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {row.bbrefId}
                  </a>
                </td>
                <td>{row.team}</td>
                <td>{row.currentTemp}</td>
                <td>{row.trailingTemp1}</td>
                <td>{row.trailingTemp2}</td>
                <td>{row.trailingTemp3}</td>
                <td>{row.trailingTemp4}</td>
                <td>{row.trailingTemp5}</td>
                <td>{row.trailingTemp6}</td>
                <td>{row.splitParkFactor}</td>
                <td>{row.g}</td>
                <td>{row.pa}</td>
                <td>{row.hr}</td>
                <td>{row.ba}</td>
                <td>{row.ops}</td>
                <td>{row.homeGames}</td>
                <td>{row.awayGames}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default HitterTempTracking;
