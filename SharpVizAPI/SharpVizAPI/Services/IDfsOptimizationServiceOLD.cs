﻿//using Microsoft.EntityFrameworkCore;
//using SharpVizApi.Models;
//using SharpVizAPI.Data;
//using System.Text.RegularExpressions;

//namespace SharpVizApi.Services
//{
//    public interface IDfsOptimizationServiceOLD
//    {
//        Task<DfsOptimizationResponse> OptimizeLineup(DfsOptimizationRequest request);
//    }


//    public class DfsOptimizationService : IDfsOptimizationServiceOLD
//    {
//        private readonly NrfidbContext _context;
//        private readonly ILogger<DfsOptimizationService> _logger;
//        private readonly IMLBStrategyService _strategyService;

//        public DfsOptimizationService(
//            NrfidbContext context,
//            ILogger<DfsOptimizationService> logger,
//            IMLBStrategyService strategyService)
//        {
//            _context = context;
//            _logger = logger;
//            _strategyService = strategyService;
//        }
//        private async Task<(int PrimaryStackSize, int SecondaryStackSize)?> GetStackRequirements(int draftGroupId)
//        {
//            // Get total games from DKPoolsMap
//            var poolInfo = await _context.DKPoolsMaps
//                .FirstOrDefaultAsync(p => p.DraftGroupId == draftGroupId);

//            if (poolInfo?.TotalGames == null)
//            {
//                _logger.LogWarning($"No game count found for draft group {draftGroupId}");
//                return null;
//            }

//            _logger.LogInformation($"Found {poolInfo.TotalGames} games for draft group {draftGroupId}");

//            var strategy = _strategyService.GetOptimalStrategy(poolInfo.TotalGames.Value);
//            _logger.LogInformation($"Optimal strategy for {poolInfo.TotalGames} games: {strategy.RecommendedStrategy}");
//            _logger.LogInformation($"Strategy reasoning: {strategy.Reasoning}");

//            var requirements = _strategyService.GetStackRequirements(strategy.RecommendedStrategy);
//            _logger.LogInformation($"Stack requirements: {requirements[0].StackSize}-{requirements[1].StackSize}");

//            return (requirements[0].StackSize, requirements[1].StackSize);
//        }


//        private async Task<DfsOptimizationResponse> OptimizeWithStrategy(
//            List<DKPlayerPool> players,
//            DfsOptimizationRequest request,
//            Dictionary<string, HashSet<string>> positionMappings)
//        {
//            if (request.Strategy == null || request.Strategy.Count == 0)
//            {
//                _logger.LogWarning("No strategy teams provided");
//                return new DfsOptimizationResponse
//                {
//                    IsSuccessful = false,
//                    Message = "Strategy requires at least one team"
//                };
//            }

//            // Get all players from the selected strategy teams, regardless of watchlist
//            var strategyTeams = request.Strategy.ToList();

//            // Get all players from the draft group for these teams
//            var strategyTeamPlayers = await _context.DKPlayerPools
//                .Where(p => p.DraftGroupId == request.DraftGroupId &&
//                       strategyTeams.Contains(p.Team) &&
//                       p.Status != "OUT")
//                .ToListAsync();

//            // Add these players to our consideration set if they're not already there
//            int addedPlayers = 0;
//            foreach (var player in strategyTeamPlayers)
//            {
//                if (!players.Any(p => p.PlayerDkId == player.PlayerDkId))
//                {
//                    players.Add(player);
//                    addedPlayers++;
//                }
//            }

//            _logger.LogInformation($"Added {addedPlayers} additional players from strategy teams");

//            // After adding strategy team players, make sure must-start players are included
//            if (request.MustStartPlayers?.Any() == true)
//            {
//                var mustStartIdsInPlayers = players.Select(p => p.PlayerDkId).ToHashSet();

//                // Check if all must-start players are in the player list
//                var missingMustStartIds = request.MustStartPlayers
//                    .Where(id => !mustStartIdsInPlayers.Contains(id))
//                    .ToList();

//                if (missingMustStartIds.Any())
//                {
//                    _logger.LogWarning($"Some must-start players aren't in the player pool after adding strategy teams: {string.Join(", ", missingMustStartIds)}");

//                    // Get these players directly from the database to ensure they're available
//                    var missingPlayers = await _context.DKPlayerPools
//                        .Where(p => missingMustStartIds.Contains(p.PlayerDkId) &&
//                              p.DraftGroupId == request.DraftGroupId)
//                        .ToListAsync();

//                    if (missingPlayers.Any())
//                    {
//                        _logger.LogInformation($"Found {missingPlayers.Count} must-start players directly from database, adding them to player pool");
//                        players.AddRange(missingPlayers);
//                    }
//                }
//            }

//            // Determine the stack configuration to use
//            int primaryStackSize;
//            int secondaryStackSize;

//            if (request.Stack != null && request.Stack.Count > 0)
//            {
//                string stackStrategy = request.Stack[0];
//                _logger.LogInformation($"Using stack strategy from request: {stackStrategy}");

//                if (stackStrategy == "Use suggested stack for this slate")
//                {
//                    // Get number of games for this slate
//                    var poolInfo = await _context.DKPoolsMaps
//                        .FirstOrDefaultAsync(p => p.DraftGroupId == request.DraftGroupId);

//                    if (poolInfo?.TotalGames == null)
//                    {
//                        _logger.LogWarning($"No game count found for draft group {request.DraftGroupId}");
//                        return new DfsOptimizationResponse
//                        {
//                            IsSuccessful = false,
//                            Message = "Could not determine optimal stacking strategy - game count not found"
//                        };
//                    }

//                    var strategy = _strategyService.GetOptimalStrategy(poolInfo.TotalGames.Value);
//                    _logger.LogInformation($"Optimal strategy for {poolInfo.TotalGames} games: {strategy.RecommendedStrategy}");
//                    _logger.LogInformation($"Strategy reasoning: {strategy.Reasoning}");

//                    var requirements = _strategyService.GetStackRequirements(strategy.RecommendedStrategy);
//                    primaryStackSize = requirements[0].StackSize;
//                    secondaryStackSize = requirements[1].StackSize;

//                    _logger.LogInformation($"Using suggested stack strategy: {primaryStackSize}-{secondaryStackSize}");
//                }
//                else if (stackStrategy.Contains("-"))
//                {
//                    // Parse the stack strategy, e.g., "3-3", "4-2", etc.
//                    var parts = stackStrategy.Split('-');
//                    if (parts.Length != 2 || !int.TryParse(parts[0], out primaryStackSize) || !int.TryParse(parts[1], out secondaryStackSize))
//                    {
//                        _logger.LogWarning($"Invalid stack strategy format: {stackStrategy}");
//                        return new DfsOptimizationResponse
//                        {
//                            IsSuccessful = false,
//                            Message = "Invalid stack strategy format. Expected format: X-Y (e.g., 3-3, 4-2)"
//                        };
//                    }

//                    _logger.LogInformation($"Using specified stack strategy: {primaryStackSize}-{secondaryStackSize}");
//                }
//                else
//                {
//                    _logger.LogWarning($"Unrecognized stack strategy: {stackStrategy}");
//                    return new DfsOptimizationResponse
//                    {
//                        IsSuccessful = false,
//                        Message = "Unrecognized stack strategy"
//                    };
//                }
//            }
//            else
//            {
//                // Fallback to the default stacking configuration
//                var stackRequirements = await GetStackRequirements(request.DraftGroupId);
//                if (!stackRequirements.HasValue)
//                {
//                    return new DfsOptimizationResponse
//                    {
//                        IsSuccessful = false,
//                        Message = "Could not determine optimal stacking strategy"
//                    };
//                }

//                primaryStackSize = stackRequirements.Value.PrimaryStackSize;
//                secondaryStackSize = stackRequirements.Value.SecondaryStackSize;

//                _logger.LogInformation($"Using default stack strategy: {primaryStackSize}-{secondaryStackSize}");
//            }

//            if (request.Strategy.Count < 2 && secondaryStackSize > 0)
//            {
//                _logger.LogWarning("Secondary stack requested but only one team provided");
//                return new DfsOptimizationResponse
//                {
//                    IsSuccessful = false,
//                    Message = $"Strategy requires two teams for a {primaryStackSize}-{secondaryStackSize} stack"
//                };
//            }

//            // Get the primary team and secondary team (if applicable)
//            string primaryTeam = request.Strategy[0];
//            string secondaryTeam = request.Strategy.Count > 1 ? request.Strategy[1] : null;

//            _logger.LogInformation($"Using teams: Primary={primaryTeam}, Secondary={secondaryTeam ?? "None"}");
//            _logger.LogInformation($"Using stack sizes: Primary={primaryStackSize}, Secondary={secondaryStackSize}");

//            // Create a backup of the original must-start players, to make sure they don't get lost
//            var originalMustStartPlayers = request.MustStartPlayers != null
//                ? new List<int>(request.MustStartPlayers)
//                : new List<int>();

//            // Try using the specified teams
//            if (secondaryTeam != null)
//            {
//                // Try both team combinations
//                var request1 = CloneRequestWithOriginalMustStarts(request, originalMustStartPlayers);
//                var attempt1 = await TryStackCombination(
//                    players, request1, positionMappings,
//                    primaryTeam, secondaryTeam,
//                    primaryStackSize, secondaryStackSize);

//                var request2 = CloneRequestWithOriginalMustStarts(request, originalMustStartPlayers);
//                var attempt2 = await TryStackCombination(
//                    players, request2, positionMappings,
//                    secondaryTeam, primaryTeam,
//                    primaryStackSize, secondaryStackSize);

//                // Return the better result
//                if (attempt1.IsSuccessful && (!attempt2.IsSuccessful ||
//                    attempt1.Players.Sum(p => p.DKppg ?? 0) > attempt2.Players.Sum(p => p.DKppg ?? 0)))
//                {
//                    return attempt1;
//                }

//                if (attempt2.IsSuccessful)
//                {
//                    return attempt2;
//                }

//                return new DfsOptimizationResponse
//                {
//                    IsSuccessful = false,
//                    Message = "Could not create valid lineup with specified stack requirements"
//                };
//            }
//            else
//            {
//                // Only primary team is specified, no secondary stack
//                var clonedRequest = CloneRequestWithOriginalMustStarts(request, originalMustStartPlayers);
//                return await TryStackCombination(
//                    players, clonedRequest, positionMappings,
//                    primaryTeam, null,
//                    primaryStackSize, 0);
//            }
//        }

//        // Helper method to clone the request with the original must-start players
//        private DfsOptimizationRequest CloneRequestWithOriginalMustStarts(
//            DfsOptimizationRequest request,
//            List<int> originalMustStartPlayers)
//        {
//            return new DfsOptimizationRequest
//            {
//                DraftGroupId = request.DraftGroupId,
//                Positions = request.Positions != null ? new List<string>(request.Positions) : null,
//                SalaryCap = request.SalaryCap,
//                OptimizeForDkppg = request.OptimizeForDkppg,
//                UserWatchlist = request.UserWatchlist != null ? new List<int>(request.UserWatchlist) : null,
//                ExcludePlayers = request.ExcludePlayers != null ? new List<int>(request.ExcludePlayers) : null,
//                MustStartPlayers = new List<int>(originalMustStartPlayers),
//                OppRankLimit = request.OppRankLimit,
//                Strategy = request.Strategy != null ? new List<string>(request.Strategy) : null,
//                Stack = request.Stack != null ? new List<string>(request.Stack) : null
//            };
//        }




//        private async Task<DfsOptimizationResponse> TryStackCombination(
//            List<DKPlayerPool> players,
//            DfsOptimizationRequest request,
//            Dictionary<string, HashSet<string>> positionMappings,
//            string primaryTeam,
//            string secondaryTeam,
//            int primaryStackSize,
//            int secondaryStackSize)
//        {
//            // Log must-start players at entry point
//            if (request.MustStartPlayers?.Any() == true)
//            {
//                _logger.LogInformation($"TryStackCombination received {request.MustStartPlayers.Count} must-start players: {string.Join(", ", request.MustStartPlayers)}");

//                // Check if they exist in the player pool
//                foreach (var mustStartId in request.MustStartPlayers)
//                {
//                    bool exists = players.Any(p => p.PlayerDkId == mustStartId);
//                    _logger.LogInformation($"Must-start player {mustStartId} exists in player pool: {exists}");

//                    if (!exists)
//                    {
//                        // Try to get the player directly from database
//                        var playerDb = await _context.DKPlayerPools
//                            .FirstOrDefaultAsync(p => p.PlayerDkId == mustStartId &&
//                                                    p.DraftGroupId == request.DraftGroupId);

//                        if (playerDb != null)
//                        {
//                            _logger.LogInformation($"Adding must-start player {playerDb.FullName} directly from database");
//                            players.Add(playerDb);
//                        }
//                    }
//                }
//            }

//            // Separate position players from pitchers
//            var pitchers = players.Where(p => p.Position.Contains("SP") || p.Position.Contains("RP") || p.Position.Contains("P")).ToList();
//            var positionPlayers = players.Where(p => !p.Position.Contains("SP") && !p.Position.Contains("RP") && !p.Position.Contains("P")).ToList();

//            var primaryTeamPositionPlayers = positionPlayers.Where(p => p.Team == primaryTeam).ToList();
//            var secondaryTeamPositionPlayers = secondaryTeam != null ?
//                positionPlayers.Where(p => p.Team == secondaryTeam).ToList() :
//                new List<DKPlayerPool>();

//            _logger.LogInformation($"Found {primaryTeamPositionPlayers.Count} position players from {primaryTeam}");
//            if (secondaryTeam != null)
//            {
//                _logger.LogInformation($"Found {secondaryTeamPositionPlayers.Count} position players from {secondaryTeam}");
//            }

//            // Separate must-start players into pitchers and position players
//            var mustStartPitchers = new List<int>();
//            var mustStartPositionPlayers = new List<int>();
//            var mustStartPrimaryCount = 0;
//            var mustStartSecondaryCount = 0;

//            if (request.MustStartPlayers?.Any() == true)
//            {
//                foreach (var mustStartId in request.MustStartPlayers)
//                {
//                    // Find the must-start player
//                    var matchingPlayers = players.Where(p => p.PlayerDkId == mustStartId).ToList();

//                    if (!matchingPlayers.Any())
//                    {
//                        _logger.LogWarning($"Must-start player with ID {mustStartId} not found in player pool");
//                        continue;
//                    }

//                    var player = matchingPlayers.First();
//                    _logger.LogInformation($"Must-start player {player.FullName} from team {player.Team} position {player.Position}");

//                    if (player.Position.Contains("SP") || player.Position.Contains("RP") || player.Position.Contains("P"))
//                    {
//                        mustStartPitchers.Add(mustStartId);
//                        continue;
//                    }

//                    mustStartPositionPlayers.Add(mustStartId);
//                    if (player.Team == primaryTeam)
//                        mustStartPrimaryCount++;
//                    else if (secondaryTeam != null && player.Team == secondaryTeam)
//                        mustStartSecondaryCount++;
//                }

//                _logger.LogInformation($"Must-start breakdown - Pitchers: {mustStartPitchers.Count}, " +
//                                     $"Primary Position Players: {mustStartPrimaryCount}, " +
//                                     $"Secondary Position Players: {mustStartSecondaryCount}");
//            }

//            // Adjust required stack sizes based on must-start position players
//            var remainingPrimaryNeeded = Math.Max(0, primaryStackSize - mustStartPrimaryCount);
//            var remainingSecondaryNeeded = Math.Max(0, secondaryStackSize - mustStartSecondaryCount);

//            _logger.LogInformation($"After accounting for must-starts, need {remainingPrimaryNeeded} more from {primaryTeam}");
//            if (secondaryTeam != null)
//            {
//                _logger.LogInformation($"and {remainingSecondaryNeeded} more from {secondaryTeam}");
//            }

//            if (primaryTeamPositionPlayers.Count < remainingPrimaryNeeded)
//            {
//                _logger.LogWarning($"Not enough position players available from {primaryTeam} for stack of size {primaryStackSize}");
//                return new DfsOptimizationResponse
//                {
//                    IsSuccessful = false,
//                    Message = $"Not enough position players available from {primaryTeam} for stack of size {primaryStackSize}"
//                };
//            }

//            if (secondaryTeam != null && secondaryTeamPositionPlayers.Count < remainingSecondaryNeeded)
//            {
//                _logger.LogWarning($"Not enough position players available from {secondaryTeam} for stack of size {secondaryStackSize}");
//                return new DfsOptimizationResponse
//                {
//                    IsSuccessful = false,
//                    Message = $"Not enough position players available from {secondaryTeam} for stack of size {secondaryStackSize}"
//                };
//            }

//            // Create a structure to track how many players we need for each position
//            var neededPositions = new Dictionary<string, int>();
//            foreach (var position in request.Positions)
//            {
//                if (neededPositions.ContainsKey(position))
//                    neededPositions[position]++;
//                else
//                    neededPositions[position] = 1;
//            }

//            _logger.LogInformation($"Required positions: {string.Join(", ", request.Positions)}");
//            _logger.LogInformation($"Needed positions count: {neededPositions.Count}");
//            foreach (var pos in neededPositions)
//            {
//                _logger.LogInformation($"Position {pos.Key}: {pos.Value} needed");
//            }

//            // Make sure we're counting correctly
//            int totalPositionsNeeded = neededPositions.Values.Sum();
//            _logger.LogInformation($"Total positions needed: {totalPositionsNeeded}");

//            // Account for must-start pitchers
//            if (request.MustStartPlayers?.Any() == true)
//            {
//                foreach (var mustStartId in request.MustStartPlayers)
//                {
//                    var matchingPlayer = players.FirstOrDefault(p => p.PlayerDkId == mustStartId);
//                    if (matchingPlayer == null) continue;

//                    // If it's a pitcher, reduce needed P positions
//                    if (matchingPlayer.Position.Contains("SP") || matchingPlayer.Position.Contains("RP") || matchingPlayer.Position.Contains("P"))
//                    {
//                        if (neededPositions.ContainsKey("P") && neededPositions["P"] > 0)
//                        {
//                            neededPositions["P"] = neededPositions["P"] - 1;
//                            _logger.LogInformation($"Accounting for must-start pitcher {matchingPlayer.FullName}, reducing P positions needed");
//                        }
//                    }
//                }
//            }

//            // Track positions filled by each stack
//            var filledPositions = new Dictionary<string, int>();
//            var primaryTeamAdded = 0;
//            var secondaryTeamAdded = 0;

//            // Start with must-start players
//            var modifiedRequest = new DfsOptimizationRequest
//            {
//                DraftGroupId = request.DraftGroupId,
//                Positions = request.Positions,
//                SalaryCap = request.SalaryCap,
//                OptimizeForDkppg = request.OptimizeForDkppg,
//                UserWatchlist = new List<int>(),
//                ExcludePlayers = request.ExcludePlayers,
//                MustStartPlayers = new List<int>(request.MustStartPlayers ?? new List<int>()),
//                OppRankLimit = request.OppRankLimit
//            };

//            // Position-aware selection for primary team stack
//            var primaryCandidates = primaryTeamPositionPlayers
//                .Where(p => !modifiedRequest.MustStartPlayers.Contains(p.PlayerDkId))
//                .OrderByDescending(p => p.DKppg)
//                .ToList();

//            // Keep selecting until we've fulfilled the primary stack requirement
//            while (primaryTeamAdded < remainingPrimaryNeeded && primaryCandidates.Any())
//            {
//                // Find the best player for any remaining position
//                var selectedPlayer = FindBestPlayerForPositions(primaryCandidates, neededPositions, positionMappings);

//                if (selectedPlayer == null) break; // No suitable player found

//                // Add this player to must-start and update tracking
//                modifiedRequest.MustStartPlayers.Add(selectedPlayer.PlayerDkId);
//                primaryCandidates.Remove(selectedPlayer);
//                primaryTeamAdded++;

//                // Update available positions
//                var bestPosition = FindBestPositionForPlayer(selectedPlayer, neededPositions.Keys.ToList(), positionMappings);
//                if (bestPosition != null && neededPositions.ContainsKey(bestPosition) && neededPositions[bestPosition] > 0)
//                {
//                    neededPositions[bestPosition] = neededPositions[bestPosition] - 1;

//                    // Track which position was filled
//                    if (!filledPositions.ContainsKey(bestPosition))
//                        filledPositions[bestPosition] = 0;
//                    filledPositions[bestPosition]++;

//                    _logger.LogInformation($"Adding primary stack player: {selectedPlayer.FullName} ({selectedPlayer.Position}) for position {bestPosition}");
//                }
//            }

//            _logger.LogInformation($"Added {primaryTeamAdded} players from primary team {primaryTeam} - Stack requirement: {primaryStackSize}");

//            // Position-aware selection for secondary team stack (if applicable)
//            if (secondaryTeam != null && remainingSecondaryNeeded > 0)
//            {
//                var secondaryCandidates = secondaryTeamPositionPlayers
//                    .Where(p => !modifiedRequest.MustStartPlayers.Contains(p.PlayerDkId))
//                    .OrderByDescending(p => p.DKppg)
//                    .ToList();

//                // Keep selecting until we've fulfilled the secondary stack requirement
//                while (secondaryTeamAdded < remainingSecondaryNeeded && secondaryCandidates.Any())
//                {
//                    // Find the best player for any remaining position
//                    var selectedPlayer = FindBestPlayerForPositions(secondaryCandidates, neededPositions, positionMappings);

//                    if (selectedPlayer == null)
//                    {
//                        _logger.LogWarning($"No suitable player found for secondary stack after adding {secondaryTeamAdded} players");
//                        break; // No suitable player found
//                    }

//                    // Add this player to must-start and update tracking
//                    modifiedRequest.MustStartPlayers.Add(selectedPlayer.PlayerDkId);
//                    secondaryCandidates.Remove(selectedPlayer);
//                    secondaryTeamAdded++;

//                    // Update available positions
//                    var bestPosition = FindBestPositionForPlayer(selectedPlayer, neededPositions.Keys.ToList(), positionMappings);
//                    if (bestPosition != null && neededPositions.ContainsKey(bestPosition) && neededPositions[bestPosition] > 0)
//                    {
//                        neededPositions[bestPosition] = neededPositions[bestPosition] - 1;

//                        // Track which position was filled
//                        if (!filledPositions.ContainsKey(bestPosition))
//                            filledPositions[bestPosition] = 0;
//                        filledPositions[bestPosition]++;

//                        _logger.LogInformation($"Adding secondary stack player: {selectedPlayer.FullName} ({selectedPlayer.Position}) for position {bestPosition}");
//                    }
//                }
//            }

//            _logger.LogInformation($"Added {secondaryTeamAdded} players from secondary team {secondaryTeam} - Stack requirement: {secondaryStackSize}");

//            // Fix: Explicitly check if the secondary stack requirement is met
//            if (secondaryTeam != null && secondaryTeamAdded < secondaryStackSize)
//            {
//                // We need to explicitly add one more player for the OF position
//                _logger.LogWarning($"Secondary stack needs {secondaryStackSize - secondaryTeamAdded} more players");

//                // Find an outfielder from the secondary team
//                var secondaryOF = secondaryTeamPositionPlayers
//                    .Where(p => !modifiedRequest.MustStartPlayers.Contains(p.PlayerDkId) &&
//                              IsPositionMatch(p.Position, "OF", positionMappings))
//                    .OrderByDescending(p => p.DKppg)
//                    .FirstOrDefault();

//                if (secondaryOF != null && neededPositions.ContainsKey("OF") && neededPositions["OF"] > 0)
//                {
//                    modifiedRequest.MustStartPlayers.Add(secondaryOF.PlayerDkId);
//                    secondaryTeamAdded++;
//                    neededPositions["OF"]--;

//                    // Track filled position
//                    if (!filledPositions.ContainsKey("OF"))
//                        filledPositions["OF"] = 0;
//                    filledPositions["OF"]++;

//                    _logger.LogInformation($"Adding missing secondary stack player: {secondaryOF.FullName} ({secondaryOF.Position}) for position OF");
//                }
//                else
//                {
//                    _logger.LogWarning($"Unable to find suitable OF player from {secondaryTeam} to complete {secondaryStackSize}-stack");

//                    // Try any position, not just OF
//                    foreach (var posKey in neededPositions.Keys.ToList())
//                    {
//                        if (neededPositions[posKey] <= 0) continue;

//                        var anyPos = secondaryTeamPositionPlayers
//                            .Where(p => !modifiedRequest.MustStartPlayers.Contains(p.PlayerDkId) &&
//                                        IsPositionMatch(p.Position, posKey, positionMappings))
//                            .OrderByDescending(p => p.DKppg)
//                            .FirstOrDefault();

//                        if (anyPos != null)
//                        {
//                            modifiedRequest.MustStartPlayers.Add(anyPos.PlayerDkId);
//                            secondaryTeamAdded++;
//                            neededPositions[posKey]--;

//                            // Track filled position
//                            if (!filledPositions.ContainsKey(posKey))
//                                filledPositions[posKey] = 0;
//                            filledPositions[posKey]++;

//                            _logger.LogInformation($"Adding missing secondary stack player: {anyPos.FullName} ({anyPos.Position}) for position {posKey}");
//                            break;
//                        }
//                    }
//                }

//                // Log final secondary stack count
//                _logger.LogInformation($"Final secondary stack count: {secondaryTeamAdded} of {secondaryStackSize} required");
//            }

//            // Log the positions we've filled so far and what's still needed
//            _logger.LogInformation("Stack position allocation summary:");
//            foreach (var pos in filledPositions.OrderBy(kv => kv.Key))
//            {
//                _logger.LogInformation($"- Position {pos.Key}: {pos.Value} filled");
//            }

//            // Double-check we've added the right number of stack players
//            int totalStackPlayersAdded = primaryTeamAdded + secondaryTeamAdded;
//            int expectedStackPlayers = primaryStackSize + secondaryStackSize;

//            if (totalStackPlayersAdded < expectedStackPlayers)
//            {
//                _logger.LogError($"Stack player count mismatch! Expected to add {expectedStackPlayers} stack players, but only added {totalStackPlayersAdded}");
//                _logger.LogError($"Primary team {primaryTeam}: added {primaryTeamAdded} of {primaryStackSize} needed");
//                _logger.LogError($"Secondary team {secondaryTeam}: added {secondaryTeamAdded} of {secondaryStackSize} needed");

//                // We should try to add more players to meet the stack requirements
//                int additionalPlayersNeeded = expectedStackPlayers - totalStackPlayersAdded;

//                _logger.LogInformation($"Trying to add {additionalPlayersNeeded} more players to meet stack requirements");

//                // Try to add more players from the primary team first, then the secondary
//                var additionalPrimaryPlayers = primaryCandidates
//                    .OrderByDescending(p => p.DKppg)
//                    .Take(additionalPlayersNeeded)
//                    .ToList();

//                foreach (var player in additionalPrimaryPlayers)
//                {
//                    modifiedRequest.MustStartPlayers.Add(player.PlayerDkId);
//                    additionalPlayersNeeded--;

//                    // No need to track positions here, we're just making sure the stack count is correct
//                    _logger.LogInformation($"Adding additional primary stack player: {player.FullName} ({player.Position})");

//                    if (additionalPlayersNeeded == 0) break;
//                }

//                // If we still need more players, try the secondary team
//                if (additionalPlayersNeeded > 0 && secondaryTeam != null)
//                {
//                    var secondaryCandidates = secondaryTeamPositionPlayers
//                        .Where(p => !modifiedRequest.MustStartPlayers.Contains(p.PlayerDkId))
//                        .OrderByDescending(p => p.DKppg)
//                        .Take(additionalPlayersNeeded)
//                        .ToList();

//                    foreach (var player in secondaryCandidates)
//                    {
//                        modifiedRequest.MustStartPlayers.Add(player.PlayerDkId);
//                        additionalPlayersNeeded--;

//                        _logger.LogInformation($"Adding additional secondary stack player: {player.FullName} ({player.Position})");

//                        if (additionalPlayersNeeded == 0) break;
//                    }
//                }
//            }

//            // Now fill any remaining positions with the best available players
//            // Correctly calculate how many positions still need to be filled
//            int remainingPlayerSlotsNeeded = neededPositions.Values.Sum();
//            _logger.LogInformation($"After stacking, need {remainingPlayerSlotsNeeded} more players to complete lineup");

//            // Make sure we don't exceed the total lineup size
//            int totalPlayersSelected = modifiedRequest.MustStartPlayers.Count;
//            int maxAdditionalPlayers = request.Positions.Count - totalPlayersSelected;

//            if (remainingPlayerSlotsNeeded > maxAdditionalPlayers)
//            {
//                _logger.LogWarning($"Position tracking shows {remainingPlayerSlotsNeeded} positions needed, but we can only add {maxAdditionalPlayers} more players. Adjusting...");
//                remainingPlayerSlotsNeeded = maxAdditionalPlayers;
//            }

//            if (remainingPlayerSlotsNeeded > 0)
//            {
//                // Get all available players not already in our lineup
//                var availablePlayers = positionPlayers
//                    .Where(p => !modifiedRequest.MustStartPlayers.Contains(p.PlayerDkId))
//                    .OrderByDescending(p => p.DKppg)
//                    .ToList();

//                int additionalPlayersAdded = 0;

//                // First, focus on OF positions if we need them
//                if (neededPositions.ContainsKey("OF") && neededPositions["OF"] > 0)
//                {
//                    var availableOutfielders = availablePlayers
//                        .Where(p => IsPositionMatch(p.Position, "OF", positionMappings))
//                        .OrderByDescending(p => p.DKppg)
//                        .ToList();

//                    _logger.LogInformation($"Found {availableOutfielders.Count} available outfielders for remaining slots");

//                    while (neededPositions["OF"] > 0 && availableOutfielders.Any() && additionalPlayersAdded < remainingPlayerSlotsNeeded)
//                    {
//                        var selectedPlayer = availableOutfielders.First();

//                        // Add this player to must-start and update tracking
//                        modifiedRequest.MustStartPlayers.Add(selectedPlayer.PlayerDkId);
//                        availablePlayers.Remove(selectedPlayer);
//                        availableOutfielders.Remove(selectedPlayer);
//                        additionalPlayersAdded++;

//                        neededPositions["OF"]--;

//                        _logger.LogInformation($"Adding remaining position player: {selectedPlayer.FullName} ({selectedPlayer.Position}) for position OF");
//                    }
//                }

//                // Then handle any other positions
//                while (additionalPlayersAdded < remainingPlayerSlotsNeeded && availablePlayers.Any())
//                {
//                    // Find the best player for any remaining position
//                    var selectedPlayer = FindBestPlayerForPositions(availablePlayers, neededPositions, positionMappings);

//                    if (selectedPlayer == null) break; // No suitable player found

//                    // Add this player to must-start and update tracking
//                    modifiedRequest.MustStartPlayers.Add(selectedPlayer.PlayerDkId);
//                    availablePlayers.Remove(selectedPlayer);
//                    additionalPlayersAdded++;

//                    // Update available positions
//                    var bestPosition = FindBestPositionForPlayer(selectedPlayer, neededPositions.Keys.ToList(), positionMappings);
//                    if (bestPosition != null && neededPositions.ContainsKey(bestPosition) && neededPositions[bestPosition] > 0)
//                    {
//                        neededPositions[bestPosition] = neededPositions[bestPosition] - 1;
//                        _logger.LogInformation($"Adding remaining position player: {selectedPlayer.FullName} ({selectedPlayer.Position}) for position {bestPosition}");
//                    }
//                }
//            }

//            // Double-check that we haven't exceeded the lineup size
//            if (modifiedRequest.MustStartPlayers.Count > request.Positions.Count)
//            {
//                _logger.LogError($"Too many players selected: {modifiedRequest.MustStartPlayers.Count}, but lineup size is {request.Positions.Count}");
//                return new DfsOptimizationResponse
//                {
//                    IsSuccessful = false,
//                    Message = $"Selection logic error: selected {modifiedRequest.MustStartPlayers.Count} players but lineup size is {request.Positions.Count}"
//                };
//            }

//            // Also check if we have the correct number of players
//            if (modifiedRequest.MustStartPlayers.Count < request.Positions.Count)
//            {
//                _logger.LogError($"Not enough players selected: {modifiedRequest.MustStartPlayers.Count}, but lineup size is {request.Positions.Count}");
//                return new DfsOptimizationResponse
//                {
//                    IsSuccessful = false,
//                    Message = $"Selection logic error: selected only {modifiedRequest.MustStartPlayers.Count} players but lineup size is {request.Positions.Count}"
//                };
//            }

//            _logger.LogInformation($"Final must-start count: {modifiedRequest.MustStartPlayers.Count} players");
//            _logger.LogInformation($"Required lineup size: {request.Positions.Count} players");

//            // Use existing optimization logic with the modified request
//            DfsOptimizationResponse optimizationResult;
//            if (request.OptimizeForDkppg)
//            {
//                optimizationResult = await OptimizeForDkppg(players, modifiedRequest, positionMappings);
//            }
//            else
//            {
//                optimizationResult = await OptimizeForSalary(players, modifiedRequest, positionMappings);
//            }

//            // Verify the lineup has the correct number of players
//            if (optimizationResult.IsSuccessful && optimizationResult.Players.Count != request.Positions.Count)
//            {
//                _logger.LogError($"Lineup size mismatch! Expected {request.Positions.Count} players but got {optimizationResult.Players.Count}");

//                // Log details about the players in the lineup
//                foreach (var player in optimizationResult.Players)
//                {
//                    _logger.LogInformation($"Player in lineup: {player.FullName} ({player.Position}) - {player.AssignedPosition}");
//                }

//                return new DfsOptimizationResponse
//                {
//                    IsSuccessful = false,
//                    Message = $"Failed to create a complete lineup. Expected {request.Positions.Count} players but got {optimizationResult.Players.Count}."
//                };
//            }

//            // Double check that all original must-start players are in the result
//            if (optimizationResult.IsSuccessful && request.MustStartPlayers?.Any() == true)
//            {
//                var missingMustStarts = request.MustStartPlayers
//                    .Where(id => !optimizationResult.Players.Any(p => p.PlayerDkId == id))
//                    .ToList();

//                if (missingMustStarts.Any())
//                {
//                    _logger.LogError($"Optimization result is missing original must-start players: {string.Join(", ", missingMustStarts)}");

//                    // Get details about the missing players
//                    var missingDetails = string.Join(", ", players
//                        .Where(p => missingMustStarts.Contains(p.PlayerDkId))
//                        .Select(p => $"{p.FullName} ({p.Position})"));

//                    return new DfsOptimizationResponse
//                    {
//                        IsSuccessful = false,
//                        Message = $"Optimization couldn't include all must-start players. Missing: {missingDetails}"
//                    };
//                }
//            }

//            return optimizationResult;
//        }

//        // Add this new method to create optimal lineups with position assignments
//        private async Task<DfsOptimizationResponse> OptimizeWithPositionAssignments(
//            List<DKPlayerPool> players,
//            DfsOptimizationRequest request,
//            Dictionary<int, string> playerPositionMap,
//            Dictionary<string, HashSet<string>> positionMappings)
//        {
//            var optimizedLineup = new List<OptimizedPlayer>();
//            var remainingPositions = new List<string>(request.Positions);

//            // Handle explicitly mapped players first
//            foreach (var kvp in playerPositionMap)
//            {
//                int playerId = kvp.Key;
//                string assignedPosition = kvp.Value;

//                // Find this player in the pool
//                var player = players.FirstOrDefault(p => p.PlayerDkId == playerId);
//                if (player == null || !remainingPositions.Contains(assignedPosition))
//                {
//                    continue;
//                }

//                // Add to the optimized lineup
//                optimizedLineup.Add(new OptimizedPlayer
//                {
//                    FullName = player.FullName,
//                    PlayerDkId = player.PlayerDkId,
//                    Position = player.Position,
//                    AssignedPosition = assignedPosition,
//                    Salary = player.Salary,
//                    Team = player.Team,
//                    DKppg = player.DKppg
//                });

//                // Remove this position from available positions
//                remainingPositions.Remove(assignedPosition);

//                _logger.LogInformation($"Assigned player {player.FullName} to position {assignedPosition} based on position map");
//            }

//            // Handle any must-start players not yet assigned
//            if (request.MustStartPlayers?.Any() == true)
//            {
//                var alreadyAdded = optimizedLineup.Select(p => p.PlayerDkId).ToHashSet();

//                foreach (var playerId in request.MustStartPlayers)
//                {
//                    // Skip if already added
//                    if (alreadyAdded.Contains(playerId))
//                        continue;

//                    var player = players.FirstOrDefault(p => p.PlayerDkId == playerId);
//                    if (player == null)
//                        continue;

//                    // Find a suitable position
//                    string bestPosition = FindBestPositionForPlayer(player, remainingPositions, positionMappings);
//                    if (bestPosition == null)
//                    {
//                        _logger.LogWarning($"Could not find position for must-start player {player.FullName}");
//                        continue;
//                    }

//                    // Add to lineup
//                    optimizedLineup.Add(new OptimizedPlayer
//                    {
//                        FullName = player.FullName,
//                        PlayerDkId = player.PlayerDkId,
//                        Position = player.Position,
//                        AssignedPosition = bestPosition,
//                        Salary = player.Salary,
//                        Team = player.Team,
//                        DKppg = player.DKppg
//                    });

//                    // Remove this position from available positions
//                    remainingPositions.Remove(bestPosition);
//                    alreadyAdded.Add(player.PlayerDkId);

//                    _logger.LogInformation($"Assigned must-start player {player.FullName} to position {bestPosition}");
//                }
//            }

//            // Fill any remaining positions with optimal players
//            while (remainingPositions.Any())
//            {
//                string position = remainingPositions.First();
//                var usedPlayers = optimizedLineup.Select(p => p.PlayerDkId).ToHashSet();

//                // Find best player for this position
//                var eligiblePlayers = players
//                    .Where(p => !usedPlayers.Contains(p.PlayerDkId) &&
//                               IsPositionMatch(p.Position, position, positionMappings))
//                    .OrderByDescending(p => p.DKppg)
//                    .ToList();

//                if (!eligiblePlayers.Any())
//                {
//                    _logger.LogWarning($"Could not find eligible player for position {position}");
//                    return new DfsOptimizationResponse
//                    {
//                        IsSuccessful = false,
//                        Message = $"Could not find eligible player for position {position}"
//                    };
//                }

//                var bestPlayer = eligiblePlayers.First();

//                // Add to lineup
//                optimizedLineup.Add(new OptimizedPlayer
//                {
//                    FullName = bestPlayer.FullName,
//                    PlayerDkId = bestPlayer.PlayerDkId,
//                    Position = bestPlayer.Position,
//                    AssignedPosition = position,
//                    Salary = bestPlayer.Salary,
//                    Team = bestPlayer.Team,
//                    DKppg = bestPlayer.DKppg
//                });

//                // Remove this position from available positions
//                remainingPositions.Remove(position);

//                _logger.LogInformation($"Assigned optimal player {bestPlayer.FullName} to remaining position {position}");
//            }

//            // Calculate total salary to check constraints
//            int totalSalary = optimizedLineup.Sum(p => p.Salary);
//            if (totalSalary > request.SalaryCap)
//            {
//                _logger.LogWarning($"Lineup exceeds salary cap: {totalSalary} > {request.SalaryCap}");
//                return new DfsOptimizationResponse
//                {
//                    IsSuccessful = false,
//                    Message = $"Lineup exceeds salary cap: {totalSalary} > {request.SalaryCap}"
//                };
//            }

//            decimal totalDkppg = optimizedLineup.Sum(p => p.DKppg ?? 0);

//            // Return the optimized lineup
//            return new DfsOptimizationResponse
//            {
//                IsSuccessful = true,
//                Players = optimizedLineup,
//                TotalSalary = totalSalary,
//                Message = $"Successfully optimized lineup with position constraints (Total DKPPG: {totalDkppg:F1})"
//            };
//        }


//        public async Task<DfsOptimizationResponse> OptimizeLineup(DfsOptimizationRequest request)
//        {
//            try
//            {
//                //dklimit
//                // Get all players for the draft group
//                var playersQuery = _context.DKPlayerPools
//                    .Where(p => p.DraftGroupId == request.DraftGroupId &&
//                                p.Status != "OUT" &&
//                                p.DKppg >= 5);

//                _logger.LogInformation("Automatically excluding players with OUT status");

//                // Apply watchlist filter if provided
//                if (request.UserWatchlist != null && request.UserWatchlist.Any())
//                {
//                    _logger.LogInformation($"Filtering by watchlist with {request.UserWatchlist.Count} players");
//                    playersQuery = playersQuery.Where(p => request.UserWatchlist.Contains(p.PlayerDkId));
//                }

//                // Apply exclusion filter if provided
//                if (request.ExcludePlayers != null && request.ExcludePlayers.Any())
//                {
//                    _logger.LogInformation($"Excluding {request.ExcludePlayers.Count} players from consideration");
//                    playersQuery = playersQuery.Where(p => !request.ExcludePlayers.Contains(p.PlayerDkId));
//                }

//                if (request.MustStartPlayers != null && request.MustStartPlayers.Any())
//                {
//                    _logger.LogInformation($"Validating {request.MustStartPlayers.Count} must-start players");
//                    _logger.LogInformation($"Must start player IDs: {string.Join(", ", request.MustStartPlayers)}");

//                    var mustStartQuery = _context.DKPlayerPools
//                        .Where(p => request.MustStartPlayers.Contains(p.PlayerDkId) &&
//                                    p.DraftGroupId == request.DraftGroupId);

//                    // Log the generated SQL query
//                    _logger.LogInformation($"Must start query SQL: {mustStartQuery.ToQueryString()}");

//                    var mustStartPlayers = await mustStartQuery.ToListAsync();

//                    _logger.LogInformation($"Found {mustStartPlayers.Count} out of {request.MustStartPlayers.Count} must-start players");

//                    // Log details of found players
//                    foreach (var player in mustStartPlayers)
//                    {
//                        _logger.LogInformation($"Found must-start player: ID={player.PlayerDkId}, Name={player.FullName}, DraftGroupId={player.DraftGroupId}");
//                    }

//                    // Log details of missing players
//                    var foundPlayerIds = mustStartPlayers.Select(p => p.PlayerDkId).ToHashSet();
//                    var missingPlayerIds = request.MustStartPlayers.Where(id => !foundPlayerIds.Contains(id));
//                    foreach (var missingId in missingPlayerIds)
//                    {
//                        _logger.LogWarning($"Could not find must-start player with ID: {missingId}");

//                        // Additional debug query to check if player exists at all
//                        var playerCheck = await _context.DKPlayerPools
//                            .Where(p => p.PlayerDkId == missingId)
//                            .Select(p => new { p.PlayerDkId, p.DraftGroupId, p.FullName })
//                            .ToListAsync();

//                        if (playerCheck.Any())
//                        {
//                            _logger.LogWarning($"Player {missingId} exists in other draft groups:");
//                            foreach (var p in playerCheck)
//                            {
//                                _logger.LogWarning($"- DraftGroup: {p.DraftGroupId}, Name: {p.FullName}");
//                            }
//                        }
//                        else
//                        {
//                            _logger.LogWarning($"Player {missingId} not found in any draft group");
//                        }
//                    }

//                    if (mustStartPlayers.Count != request.MustStartPlayers.Count)
//                    {
//                        return new DfsOptimizationResponse
//                        {
//                            IsSuccessful = false,
//                            Message = $"One or more must-start players not found in player pool. Missing players: {string.Join(", ", missingPlayerIds)}"
//                        };
//                    }

//                    // Validate must-start players don't exceed salary cap
//                    int mustStartSalary = mustStartPlayers.Sum(p => p.Salary);
//                    if (mustStartSalary > request.SalaryCap)
//                    {
//                        return new DfsOptimizationResponse
//                        {
//                            IsSuccessful = false,
//                            Message = "Must-start players total salary exceeds salary cap"
//                        };
//                    }
//                }

//                var players = await playersQuery.ToListAsync();

//                _logger.LogInformation($"Found {players.Count} players for draft group {request.DraftGroupId}");

//                if (!players.Any())
//                {
//                    return new DfsOptimizationResponse
//                    {
//                        IsSuccessful = false,
//                        Message = GetNoPlayersFoundMessage(request)
//                    };
//                }

//                // Apply OppRank filtering if specified
//                if (request.OppRankLimit.HasValue)
//                {
//                    _logger.LogInformation($"Applying OppRank filter with limit: {request.OppRankLimit.Value}");
//                    players = FilterByOppRank(players, request.OppRankLimit.Value);
//                    _logger.LogInformation($"After OppRank filtering: {players.Count} players remaining");
//                }

//                var positionMappings = new Dictionary<string, HashSet<string>>
//        {
//            { "G", new HashSet<string> { "PG", "SG" } },
//            { "F", new HashSet<string> { "SF", "PF" } },
//            { "UTIL", new HashSet<string> { "PG", "SG", "SF", "PF", "C" } },
//            { "P", new HashSet<string> { "SP", "RP", "P" }  },
//            { "OF", new HashSet<string> { "LF", "CF", "RF" }  }
//        };

//                // Log strategy and stack information
//                if (request.Strategy?.Any() == true)
//                {
//                    _logger.LogInformation($"Strategy teams provided: {string.Join(", ", request.Strategy)}");
//                }

//                if (request.Stack?.Any() == true)
//                {
//                    _logger.LogInformation($"Stack strategy provided: {string.Join(", ", request.Stack)}");
//                }

//                // Determine which optimization strategy to use
//                bool useStrategyOptimization = request.Strategy?.Any() == true;
//                bool useStackOptimization = request.Stack?.Any() == true && request.Stack[0] != "Use suggested stack for this slate";

//                _logger.LogInformation($"Optimization approach - Strategy: {useStrategyOptimization}, Stack: {useStackOptimization}");

//                if (useStrategyOptimization)
//                {
//                    _logger.LogInformation("Starting strategy-based optimization");
//                    return await OptimizeWithStrategy(players, request, positionMappings);
//                }
//                else if (request.OptimizeForDkppg)
//                {
//                    _logger.LogInformation("Starting DKPPG optimization");
//                    return await OptimizeForDkppg(players, request, positionMappings);
//                }
//                else
//                {
//                    _logger.LogInformation("Starting salary optimization");
//                    return await OptimizeForSalary(players, request, positionMappings);
//                }
//            }
//            catch (Exception ex)
//            {
//                _logger.LogError(ex, "Error optimizing lineup");
//                return new DfsOptimizationResponse
//                {
//                    IsSuccessful = false,
//                    Message = "Error occurred while optimizing lineup"
//                };
//            }
//        }


//        private string GetNoPlayersFoundMessage(DfsOptimizationRequest request)
//        {
//            var messageComponents = new List<string>();

//            if (request.UserWatchlist?.Any() == true)
//            {
//                messageComponents.Add("watchlist");
//            }

//            if (request.ExcludePlayers?.Any() == true)
//            {
//                messageComponents.Add("exclusion list");
//            }

//            if (!messageComponents.Any())
//            {
//                return $"No players found for draft group {request.DraftGroupId}";
//            }

//            return $"No players found matching {string.Join(" and ", messageComponents)} for draft group {request.DraftGroupId}";
//        }
//        private List<DKPlayerPool> FilterByOppRank(List<DKPlayerPool> players, int oppRankLimit)
//        {
//            _logger.LogInformation($"FilterByOppRank called with limit: {oppRankLimit}");

//            // If oppRankLimit is 0, return all players (no filtering)
//            if (oppRankLimit == 0)
//            {
//                _logger.LogInformation("OppRank limit is 0, returning all players without filtering");
//                return players;
//            }

//            // Log initial state
//            _logger.LogInformation($"Starting OppRank filtering with {players.Count} players");
//            _logger.LogInformation($"Will include players with ranks {31 - oppRankLimit} through 30");

//            var filteredPlayers = players.Where(p => {
//                if (string.IsNullOrEmpty(p.OppRank))
//                {
//                    _logger.LogDebug($"Player {p.FullName} has no OppRank");
//                    return false;
//                }

//                // Extract number from strings like "28th"
//                var match = Regex.Match(p.OppRank, @"\d+");
//                if (!match.Success)
//                {
//                    _logger.LogDebug($"Player {p.FullName} has invalid OppRank format: {p.OppRank}");
//                    return false;
//                }

//                int rank = int.Parse(match.Value);
//                bool isIncluded = rank >= (31 - oppRankLimit);

//                _logger.LogDebug($"Player {p.FullName}: Rank={rank}, isIncluded={isIncluded}");

//                return isIncluded;
//            }).ToList();

//            _logger.LogInformation($"After OppRank filtering: {filteredPlayers.Count} players remain");

//            // Log sample of filtered players
//            _logger.LogInformation("Sample of filtered players:");
//            foreach (var player in filteredPlayers.Take(5))
//            {
//                _logger.LogInformation($"Filtered Player: {player.FullName}, OppRank: {player.OppRank}");
//            }

//            return filteredPlayers;
//        }

//        private async Task<DfsOptimizationResponse> OptimizeForDkppg(
//            List<DKPlayerPool> players,
//            DfsOptimizationRequest request,
//            Dictionary<string, HashSet<string>> positionMappings)
//        {
//            var bestLineup = new List<OptimizedPlayer>();
//            decimal bestTotalDkppg = 0;

//            _logger.LogInformation($"Starting DKPPG optimization with {players.Count} players");

//            // Filter out players with 0 or null DKPPG unless they are must-start players
//            var mustStartIds = request.MustStartPlayers ?? new List<int>();
//            var eligiblePlayers = players
//                .Where(p => mustStartIds.Contains(p.PlayerDkId) || (p.DKppg.HasValue && p.DKppg > 0))
//                .ToList();

//            _logger.LogInformation($"Filtered out {players.Count - eligiblePlayers.Count} players with 0 or null DKPPG");

//            // Handle must-start players first
//            var mustStartPlayers = new List<OptimizedPlayer>();
//            var remainingPositions = new List<string>(request.Positions);
//            var usedPlayerIds = new HashSet<int>();
//            var currentSalary = 0;

//            if (request.MustStartPlayers?.Any() == true)
//            {
//                // Create a lookup of must-start players for easier access
//                var mustStartPlayersLookup = eligiblePlayers
//                    .Where(p => request.MustStartPlayers.Contains(p.PlayerDkId))
//                    .ToDictionary(p => p.PlayerDkId, p => p);

//                _logger.LogInformation($"Found {mustStartPlayersLookup.Count} out of {request.MustStartPlayers.Count} must-start players in eligible player pool");

//                // First, handle pitchers in must-start list to ensure they're assigned correctly
//                var mustStartPitchers = mustStartPlayersLookup.Values
//                    .Where(p => p.Position.Contains("SP") || p.Position.Contains("RP") || p.Position.Contains("P"))
//                    .ToList();

//                foreach (var pitcher in mustStartPitchers)
//                {
//                    _logger.LogInformation($"Processing must-start pitcher: {pitcher.FullName} ({pitcher.Position})");

//                    // Find all P positions in the lineup
//                    var pitcherPositions = remainingPositions.Where(p => p == "P").ToList();

//                    if (!pitcherPositions.Any())
//                    {
//                        _logger.LogWarning($"No remaining P positions for must-start pitcher {pitcher.FullName}");
//                        return new DfsOptimizationResponse
//                        {
//                            IsSuccessful = false,
//                            Message = $"Cannot fit must-start pitcher {pitcher.FullName} in lineup - no pitcher positions available"
//                        };
//                    }

//                    // Assign to first available P position
//                    var positionToAssign = pitcherPositions.First();

//                    var optimizedPlayer = new OptimizedPlayer
//                    {
//                        FullName = pitcher.FullName,
//                        PlayerDkId = pitcher.PlayerDkId,
//                        Position = pitcher.Position,
//                        AssignedPosition = positionToAssign,
//                        Salary = pitcher.Salary,
//                        Team = pitcher.Team,
//                        DKppg = pitcher.DKppg,
//                        OptimalPosition = "Pitcher"
//                    };

//                    _logger.LogInformation($"Assigned must-start pitcher {pitcher.FullName} to position {positionToAssign}");

//                    mustStartPlayers.Add(optimizedPlayer);
//                    usedPlayerIds.Add(pitcher.PlayerDkId);
//                    currentSalary += pitcher.Salary;
//                    remainingPositions.Remove(positionToAssign);
//                }

//                // Now handle non-pitcher must-start players
//                foreach (var mustStartId in request.MustStartPlayers)
//                {
//                    // Skip if we already handled this player as a pitcher
//                    if (usedPlayerIds.Contains(mustStartId)) continue;

//                    // Skip if player not found
//                    if (!mustStartPlayersLookup.TryGetValue(mustStartId, out var player))
//                    {
//                        _logger.LogWarning($"Must-start player ID {mustStartId} not found in player pool");
//                        continue;
//                    }

//                    // Find the best position for this must-start player
//                    string bestPosition = FindBestPositionForPlayer(player, remainingPositions, positionMappings);
//                    if (bestPosition == null)
//                    {
//                        return new DfsOptimizationResponse
//                        {
//                            IsSuccessful = false,
//                            Message = $"Cannot find valid position for must-start player {player.FullName}"
//                        };
//                    }

//                    var optimizedPlayer = new OptimizedPlayer
//                    {
//                        FullName = player.FullName,
//                        PlayerDkId = player.PlayerDkId,
//                        Position = player.Position,
//                        AssignedPosition = bestPosition,
//                        Salary = player.Salary,
//                        Team = player.Team,
//                        DKppg = player.DKppg,
//                        OptimalPosition = "Must-Start"
//                    };

//                    mustStartPlayers.Add(optimizedPlayer);
//                    usedPlayerIds.Add(player.PlayerDkId);
//                    currentSalary += player.Salary;
//                    remainingPositions.Remove(bestPosition);
//                }
//            }

//            // Group eligible players by their eligible positions
//            var playersByPosition = new Dictionary<string, List<DKPlayerPool>>();
//            foreach (var position in remainingPositions)
//            {
//                var positionEligiblePlayers = eligiblePlayers
//                    .Where(p => !usedPlayerIds.Contains(p.PlayerDkId) &&
//                               IsPositionMatch(p.Position, position, positionMappings))
//                    .OrderByDescending(p => p.DKppg)
//                    .ToList();

//                playersByPosition[position] = positionEligiblePlayers;
//                _logger.LogInformation($"Found {positionEligiblePlayers.Count} eligible players for position {position}");

//                // Log the top 3 players for each position by DKPPG
//                var topPlayers = positionEligiblePlayers.Take(3).ToList();
//                foreach (var player in topPlayers)
//                {
//                    _logger.LogInformation($"Top player for {position}: {player.FullName} ({player.Team}) - DKPPG: {player.DKppg}");
//                }
//            }

//            // Try each position as starting position for remaining slots
//            foreach (var startingPosition in remainingPositions)
//            {
//                _logger.LogInformation($"Trying combinations starting with position: {startingPosition}");

//                var startingPlayers = playersByPosition[startingPosition]
//                    .OrderByDescending(p => p.DKppg)
//                    .Take(20) // Consider top 20 players for this position
//                    .ToList();

//                foreach (var startingPlayer in startingPlayers)
//                {
//                    var lineup = new List<OptimizedPlayer>(mustStartPlayers);
//                    var currentUsedPlayerIds = new HashSet<int>(usedPlayerIds);
//                    var currentTotalSalary = currentSalary;

//                    // Skip players with 0 or null DKPPG
//                    if (!startingPlayer.DKppg.HasValue || startingPlayer.DKppg <= 0)
//                    {
//                        _logger.LogInformation($"Skipping player with 0/null DKPPG: {startingPlayer.FullName}");
//                        continue;
//                    }

//                    // Add starting player
//                    var startingOptimizedPlayer = new OptimizedPlayer
//                    {
//                        FullName = startingPlayer.FullName,
//                        PlayerDkId = startingPlayer.PlayerDkId,
//                        Position = startingPlayer.Position,
//                        AssignedPosition = startingPosition,
//                        Salary = startingPlayer.Salary,
//                        Team = startingPlayer.Team,
//                        DKppg = startingPlayer.DKppg,
//                        OptimalPosition = "Auto-Selected"
//                    };

//                    lineup.Add(startingOptimizedPlayer);
//                    currentUsedPlayerIds.Add(startingPlayer.PlayerDkId);
//                    currentTotalSalary += startingPlayer.Salary;

//                    var nextPositions = remainingPositions
//                        .Where(p => p != startingPosition)
//                        .ToList();

//                    // Store max salary available per position to avoid exceeding salary cap
//                    int remainingPositionsCount = nextPositions.Count;
//                    int remainingSalary = request.SalaryCap - currentTotalSalary;
//                    int maxSalaryPerPosition = remainingSalary / Math.Max(1, remainingPositionsCount);

//                    _logger.LogInformation($"After adding {startingPlayer.FullName}, remaining salary: {remainingSalary}, max per position: {maxSalaryPerPosition}");

//                    var validLineup = await TryCompleteLineup(
//                        lineup,
//                        currentUsedPlayerIds,
//                        currentTotalSalary,
//                        nextPositions,
//                        playersByPosition,
//                        request.SalaryCap);

//                    if (validLineup != null)
//                    {
//                        decimal totalDkppg = validLineup.Sum(p => p.DKppg ?? 0);
//                        if (totalDkppg > bestTotalDkppg)
//                        {
//                            bestTotalDkppg = totalDkppg;
//                            bestLineup = validLineup;
//                            _logger.LogInformation($"New best lineup found! DKPPG: {totalDkppg:F1}");

//                            // Log the lineup details
//                            foreach (var player in bestLineup)
//                            {
//                                _logger.LogInformation($"Player in best lineup: {player.FullName} ({player.Team}) - {player.AssignedPosition} - DKPPG: {player.DKppg}");
//                            }
//                        }
//                    }
//                }
//            }

//            if (!bestLineup.Any())
//            {
//                return new DfsOptimizationResponse
//                {
//                    IsSuccessful = false,
//                    Message = "Could not find a valid lineup within constraints"
//                };
//            }

//            // Validate all must-start players are in the final lineup
//            if (request.MustStartPlayers?.Any() == true)
//            {
//                var missingMustStartPlayers = request.MustStartPlayers
//                    .Where(id => !bestLineup.Any(p => p.PlayerDkId == id))
//                    .ToList();

//                if (missingMustStartPlayers.Any())
//                {
//                    _logger.LogError($"Final lineup is missing {missingMustStartPlayers.Count} must-start players: {string.Join(", ", missingMustStartPlayers)}");

//                    // Get details about the missing players
//                    var missingPlayerDetails = players
//                        .Where(p => missingMustStartPlayers.Contains(p.PlayerDkId))
//                        .Select(p => $"{p.FullName} ({p.Position})")
//                        .ToList();

//                    return new DfsOptimizationResponse
//                    {
//                        IsSuccessful = false,
//                        Message = $"Could not create valid lineup including all must-start players. Missing: {string.Join(", ", missingPlayerDetails)}"
//                    };
//                }

//                _logger.LogInformation("Successfully included all must-start players in final lineup");

//                // Log which must-start players were used
//                foreach (var player in bestLineup)
//                {
//                    if (request.MustStartPlayers.Contains(player.PlayerDkId))
//                    {
//                        _logger.LogInformation($"Must-start player in final lineup: {player.FullName} ({player.AssignedPosition})");
//                    }
//                }
//            }

//            // Track team breakdown for lineup
//            var teamBreakdown = bestLineup
//                .GroupBy(p => p.Team)
//                .Select(g => new { Team = g.Key, Count = g.Count() })
//                .OrderByDescending(x => x.Count)
//                .ToList();

//            _logger.LogInformation("Final lineup team breakdown:");
//            foreach (var team in teamBreakdown)
//            {
//                _logger.LogInformation($"- Team {team.Team}: {team.Count} players");
//            }

//            // Calculate total DKPPG and average per position
//            decimal totalSalary = bestLineup.Sum(p => p.Salary);
//            decimal averageDkppg = bestLineup.Average(p => p.DKppg ?? 0);

//            return new DfsOptimizationResponse
//            {
//                IsSuccessful = true,
//                Players = bestLineup,
//                TotalSalary = (int)totalSalary, // Cast decimal to int
//                TeamBreakdown = teamBreakdown.ToDictionary(t => t.Team, t => t.Count),
//                Message = $"Successfully optimized lineup for DKPPG (Total DKPPG: {bestTotalDkppg:F1}, Avg: {averageDkppg:F1})"
//            };
//        }

//        private async Task<List<OptimizedPlayer>> TryCompleteLineup(
//            List<OptimizedPlayer> currentLineup,
//            HashSet<int> usedPlayerIds,
//            int currentSalary,
//            List<string> remainingPositions,
//            Dictionary<string, List<DKPlayerPool>> playersByPosition,
//            int salaryCap)
//        {
//            if (!remainingPositions.Any())
//            {
//                return currentLineup;
//            }

//            var position = remainingPositions[0];
//            var nextRemainingPositions = remainingPositions.Skip(1).ToList();

//            // Calculate maximum salary we can spend on this position
//            int remainingSalary = salaryCap - currentSalary;
//            int remainingPositionsCount = remainingPositions.Count;
//            int avgSalaryPerPosition = remainingSalary / remainingPositionsCount;

//            // Allow a buffer of 20% over average for flexibility
//            int maxSalaryForPosition = (int)(avgSalaryPerPosition * 1.2);

//            // Ensure we don't exceed total remaining salary
//            maxSalaryForPosition = Math.Min(maxSalaryForPosition, remainingSalary);

//            var eligiblePlayers = playersByPosition[position]
//                .Where(p => !usedPlayerIds.Contains(p.PlayerDkId) &&
//                            p.Salary <= maxSalaryForPosition &&
//                            currentSalary + p.Salary <= salaryCap &&
//                            (p.DKppg.HasValue && p.DKppg > 0)) // Ensure positive DKPPG
//                .OrderByDescending(p => p.DKppg)
//                .Take(15)  // Consider more players for each position
//                .ToList();

//            foreach (var player in eligiblePlayers)
//            {
//                var newLineup = new List<OptimizedPlayer>(currentLineup)
//        {
//            new OptimizedPlayer
//            {
//                FullName = player.FullName,
//                PlayerDkId = player.PlayerDkId,
//                Position = player.Position,
//                AssignedPosition = position,
//                Salary = player.Salary,
//                Team = player.Team,
//                DKppg = player.DKppg,
//                OptimalPosition = "Auto-Selected"
//            }
//        };

//                var newUsedPlayerIds = new HashSet<int>(usedPlayerIds) { player.PlayerDkId };
//                var newSalary = currentSalary + player.Salary;

//                var completedLineup = await TryCompleteLineup(
//                    newLineup,
//                    newUsedPlayerIds,
//                    newSalary,
//                    nextRemainingPositions,
//                    playersByPosition,
//                    salaryCap);

//                if (completedLineup != null)
//                {
//                    return completedLineup;
//                }
//            }

//            // If we couldn't find a player within our target salary, try again with higher max
//            if (!eligiblePlayers.Any())
//            {
//                eligiblePlayers = playersByPosition[position]
//                    .Where(p => !usedPlayerIds.Contains(p.PlayerDkId) &&
//                                p.Salary <= remainingSalary &&
//                                currentSalary + p.Salary <= salaryCap &&
//                                (p.DKppg.HasValue && p.DKppg > 0)) // Ensure positive DKPPG
//                    .OrderByDescending(p => p.DKppg)
//                    .Take(10)
//                    .ToList();

//                foreach (var player in eligiblePlayers)
//                {
//                    var newLineup = new List<OptimizedPlayer>(currentLineup)
//            {
//                new OptimizedPlayer
//                {
//                    FullName = player.FullName,
//                    PlayerDkId = player.PlayerDkId,
//                    Position = player.Position,
//                    AssignedPosition = position,
//                    Salary = player.Salary,
//                    Team = player.Team,
//                    DKppg = player.DKppg,
//                    OptimalPosition = "Auto-Selected (High Salary)"
//                }
//            };

//                    var newUsedPlayerIds = new HashSet<int>(usedPlayerIds) { player.PlayerDkId };
//                    var newSalary = currentSalary + player.Salary;

//                    var completedLineup = await TryCompleteLineup(
//                        newLineup,
//                        newUsedPlayerIds,
//                        newSalary,
//                        nextRemainingPositions,
//                        playersByPosition,
//                        salaryCap);

//                    if (completedLineup != null)
//                    {
//                        return completedLineup;
//                    }
//                }
//            }

//            return null;
//        }

//        private string FindBestPositionForPlayer(
//    DKPlayerPool player,
//    List<string> availablePositions,
//    Dictionary<string, HashSet<string>> positionMappings)
//        {
//            foreach (var position in availablePositions)
//            {
//                if (IsPositionMatch(player.Position, position, positionMappings))
//                {
//                    return position;
//                }
//            }
//            return null;
//        }

//        private async Task<DfsOptimizationResponse> OptimizeForSalary(
//            List<DKPlayerPool> players,
//            DfsOptimizationRequest request,
//            Dictionary<string, HashSet<string>> positionMappings)
//        {
//            var optimizedLineup = new List<OptimizedPlayer>();
//            var usedPlayerIds = new HashSet<int>();
//            var remainingSalary = request.SalaryCap;
//            var remainingPositions = new List<string>(request.Positions);

//            // Handle must-start players first
//            if (request.MustStartPlayers?.Any() == true)
//            {
//                // Create a lookup of must-start players for easier access
//                var mustStartPlayersLookup = players
//                    .Where(p => request.MustStartPlayers.Contains(p.PlayerDkId))
//                    .ToDictionary(p => p.PlayerDkId, p => p);

//                _logger.LogInformation($"Found {mustStartPlayersLookup.Count} out of {request.MustStartPlayers.Count} must-start players in player pool");

//                // First, handle pitchers in must-start list to ensure they're assigned correctly
//                var mustStartPitchers = mustStartPlayersLookup.Values
//                    .Where(p => p.Position.Contains("SP") || p.Position.Contains("RP") || p.Position.Contains("P"))
//                    .ToList();

//                foreach (var pitcher in mustStartPitchers)
//                {
//                    _logger.LogInformation($"Processing must-start pitcher: {pitcher.FullName} ({pitcher.Position})");

//                    // Find all P positions in the lineup
//                    var pitcherPositions = remainingPositions.Where(p => p == "P").ToList();

//                    if (!pitcherPositions.Any())
//                    {
//                        _logger.LogWarning($"No remaining P positions for must-start pitcher {pitcher.FullName}");
//                        return new DfsOptimizationResponse
//                        {
//                            IsSuccessful = false,
//                            Message = $"Cannot fit must-start pitcher {pitcher.FullName} in lineup - no pitcher positions available"
//                        };
//                    }

//                    // Assign to first available P position
//                    var positionToAssign = pitcherPositions.First();

//                    var optimizedPlayer = new OptimizedPlayer
//                    {
//                        FullName = pitcher.FullName,
//                        PlayerDkId = pitcher.PlayerDkId,
//                        Position = pitcher.Position,
//                        AssignedPosition = positionToAssign,
//                        Salary = pitcher.Salary,
//                        Team = pitcher.Team,
//                        DKppg = pitcher.DKppg
//                    };

//                    _logger.LogInformation($"Assigned must-start pitcher {pitcher.FullName} to position {positionToAssign}");

//                    optimizedLineup.Add(optimizedPlayer);
//                    usedPlayerIds.Add(pitcher.PlayerDkId);
//                    remainingSalary -= pitcher.Salary;
//                    remainingPositions.Remove(positionToAssign);
//                }

//                // Now handle non-pitcher must-start players
//                foreach (var mustStartId in request.MustStartPlayers)
//                {
//                    // Skip if we already handled this player as a pitcher
//                    if (usedPlayerIds.Contains(mustStartId)) continue;

//                    // Skip if player not found
//                    if (!mustStartPlayersLookup.TryGetValue(mustStartId, out var player))
//                    {
//                        _logger.LogWarning($"Must-start player ID {mustStartId} not found in player pool");
//                        continue;
//                    }

//                    // Find the best position for this must-start player
//                    string bestPosition = FindBestPositionForPlayer(player, remainingPositions, positionMappings);
//                    if (bestPosition == null)
//                    {
//                        return new DfsOptimizationResponse
//                        {
//                            IsSuccessful = false,
//                            Message = $"Cannot find valid position for must-start player {player.FullName}"
//                        };
//                    }

//                    var optimizedPlayer = new OptimizedPlayer
//                    {
//                        FullName = player.FullName,
//                        PlayerDkId = player.PlayerDkId,
//                        Position = player.Position,
//                        AssignedPosition = bestPosition,
//                        Salary = player.Salary,
//                        Team = player.Team,
//                        DKppg = player.DKppg
//                    };

//                    optimizedLineup.Add(optimizedPlayer);
//                    usedPlayerIds.Add(player.PlayerDkId);
//                    remainingSalary -= player.Salary;
//                    remainingPositions.Remove(bestPosition);
//                }
//            }

//            // Fill remaining positions
//            foreach (var position in remainingPositions)
//            {
//                var eligiblePlayers = players
//                    .Where(p => !usedPlayerIds.Contains(p.PlayerDkId) &&
//                               IsPositionMatch(p.Position, position, positionMappings))
//                    .OrderByDescending(p => p.DKppg)
//                    .ToList();

//                if (!eligiblePlayers.Any())
//                {
//                    return new DfsOptimizationResponse
//                    {
//                        IsSuccessful = false,
//                        Message = $"Could not find eligible player for position {position}"
//                    };
//                }

//                var selectedPlayer = FindBestPlayerForSalary(eligiblePlayers, remainingSalary,
//                    remainingPositions.Count - optimizedLineup.Count + 1);

//                if (selectedPlayer == null)
//                {
//                    return new DfsOptimizationResponse
//                    {
//                        IsSuccessful = false,
//                        Message = $"Could not find suitable player for position {position} within salary constraints"
//                    };
//                }

//                optimizedLineup.Add(new OptimizedPlayer
//                {
//                    FullName = selectedPlayer.FullName,
//                    PlayerDkId = selectedPlayer.PlayerDkId,
//                    Position = selectedPlayer.Position,
//                    AssignedPosition = position,
//                    Salary = selectedPlayer.Salary,
//                    Team = selectedPlayer.Team,
//                    DKppg = selectedPlayer.DKppg
//                });

//                usedPlayerIds.Add(selectedPlayer.PlayerDkId);
//                remainingSalary -= selectedPlayer.Salary;
//            }

//            // Validate all must-start players are in the final lineup
//            if (request.MustStartPlayers?.Any() == true)
//            {
//                var missingMustStartPlayers = request.MustStartPlayers
//                    .Where(id => !optimizedLineup.Any(p => p.PlayerDkId == id))
//                    .ToList();

//                if (missingMustStartPlayers.Any())
//                {
//                    _logger.LogError($"Final lineup is missing {missingMustStartPlayers.Count} must-start players: {string.Join(", ", missingMustStartPlayers)}");

//                    // Get details about the missing players
//                    var missingPlayerDetails = players
//                        .Where(p => missingMustStartPlayers.Contains(p.PlayerDkId))
//                        .Select(p => $"{p.FullName} ({p.Position})")
//                        .ToList();

//                    return new DfsOptimizationResponse
//                    {
//                        IsSuccessful = false,
//                        Message = $"Could not create valid lineup including all must-start players. Missing: {string.Join(", ", missingPlayerDetails)}"
//                    };
//                }

//                _logger.LogInformation("Successfully included all must-start players in final lineup");

//                // Log which must-start players were used
//                foreach (var player in optimizedLineup)
//                {
//                    if (request.MustStartPlayers.Contains(player.PlayerDkId))
//                    {
//                        _logger.LogInformation($"Must-start player in final lineup: {player.FullName} ({player.AssignedPosition})");
//                    }
//                }
//            }

//            decimal totalDkppg = optimizedLineup.Sum(p => p.DKppg ?? 0);
//            return new DfsOptimizationResponse
//            {
//                IsSuccessful = true,
//                Players = optimizedLineup,
//                TotalSalary = request.SalaryCap - remainingSalary,
//                Message = $"Successfully optimized lineup (Total DKPPG: {totalDkppg:F1})"
//            };
//        }

//        private bool IsPositionMatch(string playerPosition, string requiredPosition,
//                    Dictionary<string, HashSet<string>> positionMappings)
//        {
//            // Split player position on '/' to handle multi-position players
//            var playerPositions = playerPosition.Split('/', StringSplitOptions.RemoveEmptyEntries)
//                                              .Select(p => p.Trim())
//                                              .ToHashSet();

//            // Direct match - check if any of the player's positions match the required position
//            if (playerPositions.Contains(requiredPosition))
//                return true;

//            // Check flexible positions (G, F, UTIL)
//            if (positionMappings.ContainsKey(requiredPosition))
//            {
//                // Check if any of the player's positions match any of the mapped positions
//                return playerPositions.Any(pos => positionMappings[requiredPosition].Contains(pos));
//            }

//            return false;
//        }

//        private DKPlayerPool FindBestPlayerForSalary(List<DKPlayerPool> players, int remainingSalary, int remainingPlayers)
//        {
//            var targetSalary = remainingSalary / remainingPlayers;

//            return players
//                .Where(p => p.Salary <= remainingSalary)
//                .OrderBy(p => Math.Abs(p.Salary - targetSalary))
//                .ThenByDescending(p => p.DKppg)
//                .FirstOrDefault();
//        }

//        // Helper method to find the best player for the remaining positions
//        // Helper method to find the best player for the remaining positions
//        private DKPlayerPool FindBestPlayerForPositions(
//            List<DKPlayerPool> candidates,
//            Dictionary<string, int> neededPositions,
//            Dictionary<string, HashSet<string>> positionMappings)
//        {
//            // First try to find players who can fill positions with exactly 1 slot left
//            var criticalPositions = neededPositions
//                .Where(kvp => kvp.Value == 1)
//                .Select(kvp => kvp.Key)
//                .ToList();

//            if (criticalPositions.Any())
//            {
//                foreach (var position in criticalPositions)
//                {
//                    var eligiblePlayers = candidates
//                        .Where(p => IsPositionMatch(p.Position, position, positionMappings))
//                        .OrderByDescending(p => p.DKppg)
//                        .ToList();

//                    if (eligiblePlayers.Any())
//                        return eligiblePlayers.First();
//                }
//            }

//            // If no critical positions, just find any player who can fill a needed position
//            foreach (var position in neededPositions.Where(kvp => kvp.Value > 0).Select(kvp => kvp.Key))
//            {
//                var eligiblePlayers = candidates
//                    .Where(p => IsPositionMatch(p.Position, position, positionMappings))
//                    .OrderByDescending(p => p.DKppg)
//                    .ToList();

//                if (eligiblePlayers.Any())
//                    return eligiblePlayers.First();
//            }

//            // If no eligible players found for specific positions, return the highest DKPPG player
//            return candidates.OrderByDescending(p => p.DKppg).FirstOrDefault();
//        }
//    }
//}