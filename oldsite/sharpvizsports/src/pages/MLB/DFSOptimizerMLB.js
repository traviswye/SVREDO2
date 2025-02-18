import React, { useState } from 'react';
import Sidebar from '../../components/SideBar';
import SlateDropdown from '../../components/SlateDropdown';
import PlayerPoolTable from '../../components/PlayerPoolTable';
import LineupBuilder from '../../components/LineupBuilder';

const DFSOptimizer = () => {
  const [selectedSlate, setSelectedSlate] = useState(null);
  const [watchList, setWatchList] = useState([]);
  const [draftedPlayers, setDraftedPlayers] = useState([]);

  const handleAddToWatchList = (player) => {
    const isDuplicate = watchList.some(p => p.playerDkId === player.playerDkId);
    if (!isDuplicate) {
      setWatchList(prevWatchList => [...prevWatchList, player]);
    }
  };

  const handleAddToDraft = (player) => {
    setDraftedPlayers(prevDraftedPlayers => [...prevDraftedPlayers, player]);
  };

  // New handler for optimization results
  const handleOptimizationResults = (results) => {
    // Clear existing drafted players
    setDraftedPlayers([]);

    // Add optimized players one by one to trigger proper position assignment
    if (results && results.players) {
      // Sort players by their optimal position to ensure proper placement
      const sortedPlayers = [...results.players].sort((a, b) => {
        const positionOrder = {
          P: 1, C: 2, '1B': 3, '2B': 4, '3B': 5, 'SS': 6, 'OF': 7,
          PG: 1, SG: 2, SF: 3, PF: 4, C: 5, G: 6, F: 7, UTIL: 8
        };
        return (positionOrder[a.optimalPosition] || 99) - (positionOrder[b.optimalPosition] || 99);
      });

      setDraftedPlayers(sortedPlayers);
    }
  };

  return (
    <div className="dfs-optimizer">
      <Sidebar />
      <div className="content">
        <h1>{selectedSlate?.sport || 'DFS'} Optimizer</h1>
        <SlateDropdown onSlateSelect={setSelectedSlate} />
        {selectedSlate && (
          <div className="optimizer-grid">
            <PlayerPoolTable
              draftGroupId={selectedSlate.draftGroupId}
              sport={selectedSlate.sport}
              onAddToWatchList={handleAddToWatchList}
              onAddToDraft={handleAddToDraft}
              onOptimizationResults={handleOptimizationResults}
            />
            <LineupBuilder
              sport={selectedSlate.sport}
              draftedPlayers={draftedPlayers}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default DFSOptimizer;