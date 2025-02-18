import React from "react";
import MainLayout from "../../../components/layout/MainLayout";
import TeamTemperatureTracking from "./components/TeamTemperatureTracking/TeamTemperatures";
import ProbablePitcherMetrics from "./components/ProbablePitcherMetrics/ProbablePitcherMetrics";
import HitterTempTracking from "./components/HitterTempTracking/HitterTempTracking";
import "./DailyDataMLB.css";

const DailyDataMLB = () => {
  const today = new Date();
  const formattedDate = today.toISOString().split('T')[0];
  const shortDate = formattedDate.substring(2);

  return (
    <MainLayout>
      <div className="daily-data-content">
        <h1>Daily MLB Data</h1>
        <div className="grid-container">
          <div className="grid-item">
            <TeamTemperatureTracking
              title="Team Temperatures"
              subtitle="Based on Bill James team temperature tracking"
              date={formattedDate}
            />
          </div>
          <div className="grid-item">
            <ProbablePitcherMetrics
              title="Probable Starting Pitcher Hot/Cold Metrics"
              subtitle="Metrics for probable starting pitchers"
              date={shortDate}
            />
          </div>
          <div className="grid-item">
            <HitterTempTracking
              title="Hitter Temperatures"
              subtitle="Hitter Temperatures Over last 7 games"
              date={formattedDate}
            />
          </div>
          <div className="grid-item">
            <HitterTempTracking
              title="Team Profitability"
              subtitle="Running totals of teams Vegas Profitability"
              date={formattedDate}
            />
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default DailyDataMLB;