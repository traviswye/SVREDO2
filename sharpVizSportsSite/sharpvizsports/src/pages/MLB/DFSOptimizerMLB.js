import React, { useState, useEffect } from 'react';
import Sidebar from '../../components/SideBar';
import SlateDropdown from '../../components/SlateDropdown';
import PlayerPoolTable from '../../components/PlayerPoolTable';
import LineupBuilder from '../../components/LineupBuilder';
import DfsStrategyDrawer from '../../components/DfsStrategyDrawer';
import axios from 'axios';
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
  // State to track the DK IDs corresponding to selected pitcher BBRef IDs
  const [selectedPitcherDkIds, setSelectedPitcherDkIds] = useState([]);
  const [allPlayers, setAllPlayers] = useState([]);

  const handleAddToWatchList = (player) => {
    const isDuplicate = watchList.some(p => p.playerDkId === player.playerDkId);
    if (!isDuplicate) {
      setWatchList(prevWatchList => [...prevWatchList, player]);
    }
  };
  const handlePlayersLoaded = (playerData) => {
    setAllPlayers(playerData);
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
      // Find full player data from original player pool if game info is missing
      const playersWithFullData = sortedPlayers.map(player => {
        // If game property is missing, try to find it from the player pool
        if (!player.game) {
          const fullPlayerData = allPlayers.find(p => p.playerDkId === player.playerDkId);
          if (fullPlayerData) {
            return { ...player, game: fullPlayerData.game };
          }
        }
        return player;
      });

      setDraftedPlayers(playersWithFullData);
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

  // Function to fetch player DK IDs from the backend when strategy is saved
  const fetchPlayerDkIds = async (bbrefIds) => {
    if (!bbrefIds || bbrefIds.length === 0) return [];

    try {
      const response = await axios.post(
        'https://localhost:44346/api/PlayerIDMapping/bbrefToDkIds',
        bbrefIds
      );

      // The response will contain a dictionary with BBRef IDs as keys and DK IDs as values
      // Return just the values (DK IDs)
      return Object.values(response.data);
    } catch (error) {
      console.error('Error fetching player DK IDs:', error);
      return [];
    }
  };

  const handleSaveStrategy = async (strategyData) => {
    setSavedStrategy(strategyData);
    console.log('Strategy saved:', strategyData);

    // If there are selected pitchers, fetch their DK IDs
    if (strategyData.selectedPitchers && strategyData.selectedPitchers.length > 0) {
      try {
        const dkIds = await fetchPlayerDkIds(strategyData.selectedPitchers);
        console.log('Fetched DK IDs for pitchers:', dkIds);
        setSelectedPitcherDkIds(dkIds);
      } catch (error) {
        console.error('Error fetching pitcher DK IDs:', error);
        setSelectedPitcherDkIds([]);
      }
    } else {
      setSelectedPitcherDkIds([]);
    }
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
                    onPlayersLoaded={handlePlayersLoaded}
                    draftedPlayers={draftedPlayers}
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

                      // Add must-start players using the already fetched DK IDs
                      if (selectedPitcherDkIds && selectedPitcherDkIds.length > 0) {
                        console.log('Using pitcher DK IDs in optimization payload:', selectedPitcherDkIds);
                        basePayload.mustStartPlayers = selectedPitcherDkIds;
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