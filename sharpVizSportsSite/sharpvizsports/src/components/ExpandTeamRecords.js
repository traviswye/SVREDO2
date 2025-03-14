import React from "react";
import "../css/ExpandTeamRecords.css";

const ExpandedTeamRecords = ({ homeTeam, awayTeam, homeTeamRecord, awayTeamRecord }) => {
    // Set up record fields to be shown in the table
    const recordFields = [
        { key: "wins", label: "Wins" },
        { key: "losses", label: "Losses" },
        { key: "winPercentage", label: "Win %", format: (val) => val && val.toFixed(3) },
        { key: "gb", label: "Games Behind" },
        { key: "wcgb", label: "Wild Card GB" },
        { key: "streak", label: "Streak" },
        { key: "l10", label: "Last 10" },
        { key: "runsScored", label: "Runs Scored" },
        { key: "runsAgainst", label: "Runs Against" },
        { key: "diff", label: "Run Differential" },
        { key: "expectedRecord", label: "Pythagorean W-L" },
        { key: "homeRec", label: "Home Record" },
        { key: "awayRec", label: "Away Record" },
        { key: "xtra", label: "Extra Innings" },
        { key: "oneRun", label: "One-Run Games" },
        { key: "day", label: "Day Games" },
        { key: "night", label: "Night Games" },
        { key: "grass", label: "On Grass" },
        { key: "turf", label: "On Turf" },
        { key: "east", label: "vs East" },
        { key: "central", label: "vs Central" },
        { key: "west", label: "vs West" },
        { key: "inter", label: "vs Interleague" },
        { key: "vs500Plus", label: "vs .500+ Teams" },
        { key: "vsRHP", label: "vs RH Pitchers" },
        { key: "vsLHP", label: "vs LH Pitchers" }
    ];

    if (!homeTeamRecord || !awayTeamRecord) {
        return (
            <div className="expanded-records-container">
                <p className="no-data-message">Team record data not available.</p>
            </div>
        );
    }

    return (
        <div className="expanded-records-container">
            <table className="expanded-records-table">
                <thead>
                    <tr>
                        <th className="record-field-header">Field</th>
                        <th className="team-header">{awayTeam}</th>
                        <th className="team-header">{homeTeam}</th>
                    </tr>
                </thead>
                <tbody>
                    {recordFields.map((field) => (
                        <tr key={field.key} className="record-row">
                            <td className="record-field">{field.label}</td>
                            <td className="team-value">
                                {field.format
                                    ? field.format(awayTeamRecord[field.key])
                                    : awayTeamRecord[field.key] || "N/A"}
                            </td>
                            <td className="team-value">
                                {field.format
                                    ? field.format(homeTeamRecord[field.key])
                                    : homeTeamRecord[field.key] || "N/A"}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default ExpandedTeamRecords;