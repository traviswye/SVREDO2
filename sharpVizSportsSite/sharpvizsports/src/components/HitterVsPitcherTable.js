import React from "react";
import "../css/HitterVsPitcherTable.css";

const HitterVsPitcherTable = ({ data, teamName, opposingTeamName, opposingPitcherId }) => {
    // If no data or no hitters, show message
    if (!data || !Array.isArray(data) || data.length === 0) {
        return (
            <div className="hvp-no-data">
                <p>No matchup history available for {teamName} hitters vs. {opposingPitcherId}</p>
            </div>
        );
    }

    // Helper to generate Baseball Reference matchup URLs
    const getBbRefMatchupUrl = (hitterId, pitcherId) => {
        if (!hitterId || !pitcherId) return "#";
        const firstLetterHitter = hitterId.charAt(0);
        const firstLetterPitcher = pitcherId.charAt(0);
        return `https://www.baseball-reference.com/players/${firstLetterHitter}/${hitterId}.shtml`;
    };

    return (
        <div className="hvp-section">
            <h3 className="hvp-title">
                {teamName} Hitters vs. {opposingTeamName} Pitcher
            </h3>
            <div className="hvp-table-container">
                <table className="hvp-table">
                    <thead>
                        <tr>
                            <th className="hvp-header-cell">Hitter</th>
                            <th className="hvp-header-cell">PA</th>
                            <th className="hvp-header-cell">H</th>
                            <th className="hvp-header-cell">HR</th>
                            <th className="hvp-header-cell">RBI</th>
                            <th className="hvp-header-cell">BB</th>
                            <th className="hvp-header-cell">SO</th>
                            <th className="hvp-header-cell">BA</th>
                            <th className="hvp-header-cell">OBP</th>
                            <th className="hvp-header-cell">SLG</th>
                            <th className="hvp-header-cell">OPS</th>
                        </tr>
                    </thead>
                    <tbody>
                        {data.map((hvp, index) => (
                            <tr key={`${hvp.hitter}-${index}`} className="hvp-row">
                                <td className="hvp-hitter-cell">
                                    <a
                                        href={getBbRefMatchupUrl(hvp.hitter, opposingPitcherId)}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="hvp-player-link"
                                    >
                                        {hvp.hitter}
                                    </a>
                                </td>
                                <td className="hvp-stat-cell">{hvp.pa || 0}</td>
                                <td className="hvp-stat-cell">{hvp.hits || hvp.h || 0}</td>
                                <td className="hvp-stat-cell">{hvp.hr || 0}</td>
                                <td className="hvp-stat-cell">{hvp.rbi || 0}</td>
                                <td className="hvp-stat-cell">{hvp.bb || 0}</td>
                                <td className="hvp-stat-cell">{hvp.so || 0}</td>
                                <td className="hvp-stat-cell">{formatBattingAvg(hvp.ba)}</td>
                                <td className="hvp-stat-cell">{formatBattingAvg(hvp.obp)}</td>
                                <td className="hvp-stat-cell">{formatBattingAvg(hvp.slg)}</td>
                                <td className="hvp-stat-cell">{formatBattingAvg(hvp.ops)}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

// Helper function to format batting averages
function formatBattingAvg(value) {
    if (value === undefined || value === null) return ".000";
    return value.toFixed(3).toString().replace(/^0\./, ".");
}

export default HitterVsPitcherTable;