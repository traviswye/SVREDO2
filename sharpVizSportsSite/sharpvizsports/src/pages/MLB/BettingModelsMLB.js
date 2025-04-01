import React, { useState } from "react";
import Sidebar from "../../components/SideBar";
import TodaysEV from "../../components/TodaysEV";
import PropsEV from "../../components/PropsEV";
import NRFIEV from "../../components/NRFIEV";
import ModelPicks from "../../components/ModelPicks";
import PickHistory from "../../components/PickHistory";
import "../../css/BettingModelsMLB.css";

const BettingModelsMLB = () => {
  const [activeTab, setActiveTab] = useState("today");

  const renderContent = () => {
    switch (activeTab) {
      case "picks":
        return <ModelPicks />;
      case "history":
        return <PickHistory />;
      case "props":
        return <PropsEV />;
      case "nrfi":
        return <NRFIEV />;
      case "today":
      default:
        return <TodaysEV />;
    }
  };

  return (
    <div className="betting-models-mlb">
      <Sidebar />
      <div className="content">
        <h1>MLB Betting Models</h1>

        <div className="betting-tabs">
          <button
            className={activeTab === "today" ? "active" : ""}
            onClick={() => setActiveTab("today")}
          >
            Today's Expected Values
          </button>
          <button
            className={activeTab === "picks" ? "active" : ""}
            onClick={() => setActiveTab("picks")}
          >
            Model Picks
          </button>
          <button
            className={activeTab === "history" ? "active" : ""}
            onClick={() => setActiveTab("history")}
          >
            Pick History
          </button>
          <button
            className={activeTab === "props" ? "active" : ""}
            onClick={() => setActiveTab("props")}
          >
            Props Analysis
          </button>
          <button
            className={activeTab === "nrfi" ? "active" : ""}
            onClick={() => setActiveTab("nrfi")}
          >
            NRFI Analysis
          </button>
        </div>

        <div className="betting-content">
          {renderContent()}
        </div>

        <div className="betting-disclaimer">
          <p>
            <strong>Disclaimer:</strong> The betting models provided are for informational purposes only.
            Past performance is not indicative of future results. Always gamble responsibly and be aware of the risks involved.
          </p>
        </div>
      </div>
    </div>
  );
};

export default BettingModelsMLB;