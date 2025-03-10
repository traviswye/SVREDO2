import React, { useState } from 'react';
import Sidebar from '../../components/SideBar';
import SlateDropdown from '../../components/SlateDropdown';
import PlayerPoolTable from '../../components/PlayerPoolTable';
import LineupBuilder from '../../components/LineupBuilder';
import DfsStrategyDrawer from '../../components/DfsStrategyDrawer';
import '../../css/DFSOptimizerMLB.css';
import '../../css/PlayerPoolTable.css';
import '../../css/LineupBuilder.css';
import '../../css/SlateDropdown.css';
import '../../css/DfsStrategyDrawer.css';

const DFSOptimizer = () => {
  const [selectedSlate, setSelectedSlate] = useState(null);
  const [watchList, setWatchList] = useState([]);
  const [draftedPlayers, setDraftedPlayers] = useState([]);
  const [isStrategyDrawerOpen, setIsStrategyDrawerOpen] = useState(false);
  const [savedStrategy, setSavedStrategy] = useState(null);

  const handleAddToWatchList = (player) => {
    const isDuplicate = watchList.some(p => p.playerDkId === player.playerDkId);
    if (!isDuplicate) {
      setWatchList(prevWatchList => [...prevWatchList, player]);
    }
  };

  const handleAddToDraft = (player) => {
    setDraftedPlayers(prevDraftedPlayers => [...prevDraftedPlayers, player]);
  };

  // Handler for optimization results
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

  const handleResetLineup = (updatedPlayers = []) => {
    // If updatedPlayers is provided, use it (for individual player removal)
    // Otherwise clear everything (for full reset)
    setDraftedPlayers(updatedPlayers);
  };

  const toggleStrategyDrawer = () => {
    setIsStrategyDrawerOpen(!isStrategyDrawerOpen);
  };

  const handleSaveStrategy = (strategyData) => {
    setSavedStrategy(strategyData);
    console.log('Strategy saved:', strategyData);
  };

  // Function to convert pitcherId to DraftKings player ID
  // This function would need to be implemented based on your data structure
  // For now, we'll assume we can do a direct lookup or use the ID as is
  const getPitcherDraftKingsId = (pitcherId) => {
    // In a real implementation, this might look up the DK ID from a mapping
    // For now, we'll just ensure it's a number (assuming pitcherId has ID at the end)
    const numericId = parseInt(pitcherId.replace(/\D/g, ''));
    return numericId || 0; // Return 0 if no numeric part found
  };

  return (
    <div className="dfs-optimizer">
      <Sidebar />
      <div className="content">
        <h1>{selectedSlate?.sport || 'MLB'} Optimizer</h1>
        <SlateDropdown onSlateSelect={setSelectedSlate} />

        {selectedSlate && (
          <>
            {/* Strategy Toggle Button */}
            <div className="strategy-toggle">
              <button
                className="strategy-toggle-button"
                onClick={toggleStrategyDrawer}
              >
                <span className="icon">⚙️</span>
                {savedStrategy ? 'Edit Strategy' : 'Set Strategy'}
              </button>
              {savedStrategy && (
                <span className="strategy-status">
                  {savedStrategy.contestType} Game
                  {savedStrategy.contestType === 'Tournament' &&
                    ` - ${savedStrategy.stackStrategy}`}
                </span>
              )}
            </div>

            <div className="optimizer-grid">
              <div className="player-pool-container">
                <div className="scrollable-player-pool">
                  <PlayerPoolTable
                    draftGroupId={selectedSlate.draftGroupId}
                    sport={selectedSlate.sport}
                    onAddToWatchList={handleAddToWatchList}
                    onAddToDraft={handleAddToDraft}
                    onOptimizationResults={handleOptimizationResults}
                    prepareOptimizationPayload={(watchlistIds, draftGroupId) => {
                      // Default payload structure
                      const basePayload = {
                        draftGroupId: draftGroupId,
                        positions: (selectedSlate?.sport === 'MLB') ?
                          ["P", "P", "C", "1B", "2B", "3B", "SS", "OF", "OF", "OF"] :
                          ["C", "PF", "SF", "SG", "PG", "G", "F", "UTIL"],
                        salaryCap: 50000,
                        optimizeForDkppg: true,
                        oppRankLimit: 0,
                        userWatchlist: watchlistIds,
                        excludePlayers: []
                      };

                      // Add must-start players if we have selected pitchers
                      if (savedStrategy?.selectedPitchers && savedStrategy.selectedPitchers.length > 0) {
                        // Get the DraftKings player IDs for the selected pitchers
                        const mustStartPitcherIds = savedStrategy.selectedPitchers.map(pitcherId => {
                          // Find the draft kings ID for this pitcher
                          return getPitcherDraftKingsId(pitcherId);
                        }).filter(id => id > 0); // Filter out any that couldn't be mapped

                        basePayload.mustStartPlayers = mustStartPitcherIds;
                      } else {
                        basePayload.mustStartPlayers = [];
                      }

                      // If we have tournament strategy settings, enhance the payload
                      if (savedStrategy && savedStrategy.contestType === 'Tournament') {
                        return {
                          ...basePayload,
                          strategy: savedStrategy.selectedTeams,
                          stack: [savedStrategy.stackStrategy]
                        };
                      }

                      // Otherwise return the default payload for Cash games
                      return basePayload;
                    }}
                  />
                </div>
              </div>

              <div className="lineup-container">
                <LineupBuilder
                  sport={selectedSlate.sport}
                  draftedPlayers={draftedPlayers}
                  onResetLineup={handleResetLineup}
                />
              </div>
            </div>

            {/* Strategy Drawer Component */}
            <DfsStrategyDrawer
              isOpen={isStrategyDrawerOpen}
              onClose={() => setIsStrategyDrawerOpen(false)}
              draftGroupId={selectedSlate.draftGroupId}
              sport={selectedSlate.sport}
              onSaveStrategy={handleSaveStrategy}
            />
          </>
        )}
      </div>
    </div>
  );
};

export default DFSOptimizer;