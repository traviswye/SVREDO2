// import React, { useState, useEffect } from "react";
// import { Line } from "react-chartjs-2";
// import "../css/DataBox.css";
// import { Chart, LineElement, LinearScale, CategoryScale, PointElement, LineController, Title, Tooltip, Legend } from "chart.js";

// // Register components
// Chart.register(LineElement, LinearScale, CategoryScale, PointElement, LineController, Title, Tooltip, Legend);


// const DataBox = ({
//   title,
//   subtitle,
//   headers,
//   keyHeaders,
//   apiUrl,
//   toggleEnabled = true,
// }) => {
//   const [view, setView] = useState("table"); // 'table' or 'graph'
//   const [data, setData] = useState([]);
//   const [loading, setLoading] = useState(true);
//   const [sortConfig, setSortConfig] = useState({
//     key: "currentTemp",
//     direction: "desc",
//   });

//   // State for graph options
//   const [selectedTeam, setSelectedTeam] = useState("");
//   const [selectedYear, setSelectedYear] = useState("2024");
//   const [graphData, setGraphData] = useState(null);
//   const [metric, setMetric] = useState("currentTemp"); // Default metric for graph

//   const teams = [
//     "ARI", "ATL", "BAL", "BOS", "CHC", "CIN", "CLE", "COL", "CWS", "DET",
//     "HOU", "KC", "LAA", "LAD", "MIA", "MIL", "MIN", "NYM", "NYY", "OAK",
//     "PHI", "PIT", "SD", "SEA", "SF", "STL", "TB", "TEX", "TOR", "WSH",
//   ];

//   const years = ["2024", "2025"];

//   useEffect(() => {
//     const fetchData = async () => {
//       try {
//         const response = await fetch(apiUrl);
//         const json = await response.json();

//         // Default sorting by currentTemp in descending order
//         const sortedData = [...json].sort((a, b) => b.currentTemp - a.currentTemp);
//         setData(sortedData);
//       } catch (error) {
//         console.error("Error fetching data:", error);
//       } finally {
//         setLoading(false);
//       }
//     };

//     fetchData();
//   }, [apiUrl]);

//   // Add this useEffect to your component
// useEffect(() => {
//     if (selectedTeam && selectedYear && view === "graph") {
//       fetchGraphData(); // Automatically fetch and render graph data
//     }
//   }, [selectedTeam, selectedYear, view]);


//   const handleToggle = () => {
//     if (view === "graph") {
//       // Reset graph state when toggling back to the table view
//       setGraphData(null);
//       setSelectedTeam("");
//       setSelectedYear("2024"); // Reset year or set to your default
//       setMetric("currentTemp"); // Reset metric to default
//     }
//     setView(view === "table" ? "graph" : "table");
//   };
//     // Log received data to ensure it's being passed properly
//     console.log("Data received by DataBox:", data);

//   const handleSort = (key) => {
//     const direction =
//       sortConfig.key === key && sortConfig.direction === "asc" ? "desc" : "asc";
//     setSortConfig({ key, direction });

//     const sortedData = [...data].sort((a, b) => {
//       if (a[key] < b[key]) return direction === "asc" ? -1 : 1;
//       if (a[key] > b[key]) return direction === "asc" ? 1 : -1;
//       return 0;
//     });

//     setData(sortedData);
//   };

//   const formatValue = (key, value) => {
//     if (key === "winPerc" || key === "pythagPerc") {
//       // Format percentages to 3 decimal places
//       return value.toFixed(3);
//     }
//     if (key === "date") {
//       // Format date to yyyy-mm-dd
//       return value.split("T")[0];
//     }
//     return value;
//   };
//   const fetchGraphData = async () => {
//     if (!selectedTeam || !selectedYear) {
//       alert("Please select both a team and a year.");
//       return;
//     }

//     try {
//       const response = await fetch(
//         `https://localhost:44346/api/TeamTemperatureTracking/${selectedTeam}/${selectedYear}`
//       );
//       const json = await response.json();

//       // Process data for graphing
//       const dates = json.map((entry) => entry.date.split("T")[0]); // Extract dates

//       let graphValues = {};

//       if (metric === "both") {
//         graphValues = {
//           rs: json.map((entry) => entry.rs),
//           ra: json.map((entry) => entry.ra),
//         };
//       } else {
//         graphValues = { [metric]: json.map((entry) => entry[metric]) }; // Extract single metric
//       }

//       setGraphData({ dates, values: graphValues });
//     } catch (error) {
//       console.error("Error fetching graph data:", error);
//     }
//   };

//   return (
//     <div className="data-box-container">
//       {/* Title and Subtitle */}
//       <div className="data-box-header">
//         <div>
//         <div className="data-box-title">{title}</div>
//         <div className="data-box-subtitle">{subtitle}</div>
//         </div>
//       </div>

//       {/* Toggle Button */}
//       {toggleEnabled && (
//         <div className="data-box-options">
//           <button className="toggle-button" onClick={handleToggle}>
//             Toggle to {view === "table" ? "Graph Explorer" : "Table"}
//           </button>
//         </div>
//       )}

//       {view === "table" ? (
//         <div className="data-box-scrollable">
//           <table className="data-box-table">
//             <thead>
//               <tr>
//                 {headers.map((header, index) => (
//                   <th
//                     key={index}
//                     onClick={() => handleSort(keyHeaders[index])}
//                     style={{ cursor: "pointer" }}
//                   >
//                     {header}{" "}
//                     {sortConfig.key === keyHeaders[index]
//                       ? sortConfig.direction === "asc"
//                         ? "↑"
//                         : "↓"
//                       : ""}
//                   </th>
//                 ))}
//               </tr>
//             </thead>

// <tbody>
//   {data.map((row, rowIndex) => (
//     <tr
//       key={rowIndex}
//       onClick={() => {
//         setSelectedTeam(row.team); // Assuming 'team' is the key for the team abbreviation
//         setSelectedYear("2024"); // Set the year to 2024 (or make this dynamic)
//         setView("graph"); // Switch to graph view
//       }}
//       style={{ cursor: "pointer" }} // Make it visually clear the row is clickable
//     >
//       {keyHeaders.map((key, cellIndex) => (
//         <td key={cellIndex}>{formatValue(key, row[key])}</td>
//       ))}
//     </tr>
//   ))}
// </tbody>


//           </table>
//         </div>
//       ) : (
//         <div className="graph-view">
// <div className="graph-options">
//   <label>
//     Team:
//     <select
//       value={selectedTeam}
//       onChange={(e) => setSelectedTeam(e.target.value)}
//     >
//       <option value="">Select a Team</option>
//       {teams.map((team) => (
//         <option key={team} value={team}>
//           {team}
//         </option>
//       ))}
//     </select>
//   </label>
//   <label>
//     Year:
//     <select
//       value={selectedYear}
//       onChange={(e) => setSelectedYear(e.target.value)}
//     >
//       {years.map((year) => (
//         <option key={year} value={year}>
//           {year}
//         </option>
//       ))}
//     </select>
//   </label>
//   <label>
//     Metric:
//     <select
//       value={metric}
//       onChange={(e) => setMetric(e.target.value)}
//     >
//       <option value="currentTemp">Current Temperature</option>

//       <option value="both">Both RS and RA</option> {/* New option */}
//     </select>
//   </label>
//   <button className="generate-button" onClick={fetchGraphData}>
//     Generate Graph
//   </button>
// </div>
// <div className="graph-container">
//   {graphData && (
//     <Line
//       key={selectedTeam + selectedYear + metric} // Ensures remounting on input change
//       data={{
//         labels: graphData.dates, // Dates are shared across all datasets
//         datasets: [
//           ...(metric === "both"
//             ? [
//                 {
//                   label: "Runs Scored (RS)",
//                   data: graphData.values.rs,
//                   borderColor: "#28a745", // Green color for RS
//                   tension: 0.4,
//                   fill: false,
//                 },
//                 {
//                   label: "Runs Allowed (RA)",
//                   data: graphData.values.ra,
//                   borderColor: "#dc3545", // Red color for RA
//                   tension: 0.4,
//                   fill: false,
//                 },
//               ]
//             : [
//                 {
//                   label:
//                     metric === "currentTemp"
//                       ? "Current Temperature"
//                       : metric === "rs"
//                       ? "Runs Scored (RS)"
//                       : "Runs Allowed (RA)",
//                   data:
//                     metric === "currentTemp"
//                       ? graphData.values.currentTemp
//                       : metric === "rs"
//                       ? graphData.values.rs
//                       : graphData.values.ra,
//                   borderColor: metric === "rs" ? "#28a745" : "#dc3545",
//                   tension: 0.4,
//                   fill: false,
//                 },
//               ]),
//         ],
//       }}
//       options={{
//         responsive: true,
//         maintainAspectRatio: true,
//         scales: {
//             x: {
//                 title: {
//                   display: true,
//                   text: "Date",
//                   font: { size: 14, weight: "bold" },
//                 },
//                 ticks: {
//                   maxTicksLimit: 15, // Reduces the number of labels displayed
//                   autoSkip: true,    // Dynamically skip labels
//                   maxRotation: 45,   // Rotate the labels 45 degrees
//                   minRotation: 45,   // Minimum rotation angle
//                   font: { size: 12 },
//                   color: "#555",
//                 },
//                 grid: {
//                   color: "#e0e0e0",   // Light grid lines for modern design
//                   borderDash: [4, 4], // Dashed grid lines
//                 },
//               },

//           y: {
//             title: {
//               display: true,
//               text: metric === "currentTemp"
//                 ? "Temperature"
//                 : "Runs Scored / Allowed",
//               font: { size: 14, weight: "bold" },
//             },
//             ticks: {
//               font: { size: 12 },
//               color: "#555",
//             },
//             grid: {
//               color: "#e0e0e0",
//               borderDash: [4, 4],
//             },
//           },
//         },
//         plugins: {
//           legend: {
//             position: "top",
//             labels: {
//               font: { size: 14 },
//               color: "#333",
//               boxWidth: 20,
//               padding: 10,
//             },
//           },
//           tooltip: {
//             backgroundColor: "#444",
//             titleFont: { size: 14, weight: "bold" },
//             bodyFont: { size: 12 },
//             bodySpacing: 6,
//             padding: 8,
//             cornerRadius: 6,
//           },
//         },
//       }}
//     />
//   )}
// </div>


//         </div>
//       )}
//     </div>
//   );
// };

// export default DataBox;

// src/components/common/DataBox/DataBox.js
import React, { useState } from "react";
import { Line } from "react-chartjs-2";
import "./DataBox.css";
import { Chart, LineElement, LinearScale, CategoryScale, PointElement, LineController, Title, Tooltip, Legend } from "chart.js";

// Register Chart.js components
Chart.register(LineElement, LinearScale, CategoryScale, PointElement, LineController, Title, Tooltip, Legend);

const DataBox = ({
  title,
  subtitle,
  headers,
  keyHeaders,
  data,
  toggleEnabled = true,
  graphOptions = null,
  onRowClick = null,
  formatValue = (key, value) => value,
  defaultSort = { key: null, direction: "desc" }
}) => {
  const [view, setView] = useState("table");
  const [sortConfig, setSortConfig] = useState(defaultSort);

  const handleSort = (key) => {
    const direction =
      sortConfig.key === key && sortConfig.direction === "asc" ? "desc" : "asc";
    setSortConfig({ key, direction });

    return [...data].sort((a, b) => {
      if (a[key] < b[key]) return direction === "asc" ? -1 : 1;
      if (a[key] > b[key]) return direction === "asc" ? 1 : -1;
      return 0;
    });
  };

  const handleToggle = () => {
    setView(view === "table" ? "graph" : "table");
  };

  return (
    <div className="data-box-container">
      <div className="data-box-header">
        <div>
          <div className="data-box-title">{title}</div>
          <div className="data-box-subtitle">{subtitle}</div>
        </div>
      </div>

      {toggleEnabled && graphOptions && (
        <div className="data-box-options">
          <button className="toggle-button" onClick={handleToggle}>
            Toggle to {view === "table" ? "Graph Explorer" : "Table"}
          </button>
        </div>
      )}

      {view === "table" ? (
        <div className="data-box-scrollable">
          <table className="data-box-table">
            <thead>
              <tr>
                {headers.map((header, index) => (
                  <th
                    key={index}
                    onClick={() => handleSort(keyHeaders[index])}
                    style={{ cursor: "pointer" }}
                  >
                    {header}{" "}
                    {sortConfig.key === keyHeaders[index]
                      ? sortConfig.direction === "asc"
                        ? "↑"
                        : "↓"
                      : ""}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((row, rowIndex) => (
                <tr
                  key={rowIndex}
                  onClick={() => onRowClick && onRowClick(row)}
                  style={{ cursor: onRowClick ? "pointer" : "default" }}
                >
                  {keyHeaders.map((key, cellIndex) => (
                    <td key={cellIndex}>{formatValue(key, row[key])}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="graph-view">
          {graphOptions && (
            <>
              <div className="graph-options">
                {graphOptions.controls}
              </div>
              <div className="graph-container">
                {graphOptions.data && (
                  <Line
                    data={graphOptions.data}
                    options={graphOptions.chartOptions}
                  />
                )}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default DataBox;