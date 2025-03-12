using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using SharpVizAPI.Data;
using SharpVizApi.Models;
using SharpVizApi.Services.Optimization;

namespace SharpVizApi.Services.Optimization
{
    // MLB-specific parameters
    public class MLBParameters
    {
        public List<string> StrategyTeams { get; set; } = new List<string>();
        public string StackStrategy { get; set; } = "Use suggested stack for this slate";
    }

    public class MLBLineupOptimizer : BaseLineupOptimizer
    {
        private readonly NrfidbContext _context;
        private readonly ILogger<MLBLineupOptimizer> _logger;
        private readonly IMLBStrategyService _strategyService;

        public MLBLineupOptimizer(
            NrfidbContext context,
            ILogger<MLBLineupOptimizer> logger,
            IMLBStrategyService strategyService)
        {
            _context = context;
            _logger = logger;
            _strategyService = strategyService;
        }

        protected override async Task<OptimizationResult> OptimizeLineupInternal(OptimizationParameters parameters)
        {
            try
            {
                // 1. Cast sport-specific parameters
                var mlbParams = parameters.SportSpecificParameters as MLBParameters;
                if (mlbParams == null && parameters.SportSpecificParameters != null)
                {
                    _logger.LogWarning("Sport-specific parameters provided but not of type MLBParameters");
                    mlbParams = new MLBParameters();
                }
                else if (mlbParams == null)
                {
                    mlbParams = new MLBParameters();
                }

                // 2. Get players from the draft group
                var players = await GetPlayerPool(parameters, mlbParams);

                if (!players.Any())
                {
                    return new OptimizationResult
                    {
                        IsSuccessful = false,
                        Message = $"No players found for draft group {parameters.DraftGroupId} with the specified filters"
                    };
                }

                _logger.LogInformation($"Found {players.Count} players for draft group {parameters.DraftGroupId}");

                // 3. Process must-start players
                var (mustStartPlayers, remainingPositions, remainingSalary) =
                    await ProcessMustStartPlayers(players, parameters);

                if (mustStartPlayers.Any(p => p.IsError))
                {
                    var invalidPlayers = string.Join(", ",
                        mustStartPlayers.Where(p => p.IsError).Select(p => p.ErrorMessage));

                    return new OptimizationResult
                    {
                        IsSuccessful = false,
                        Message = $"Issues with must-start players: {invalidPlayers}"
                    };
                }

                // 4. Apply stacking strategy if applicable
                var stackingResult = await ApplyStackingStrategy(
                    players, parameters, mlbParams, remainingPositions, mustStartPlayers);

                if (!stackingResult.IsSuccessful)
                {
                    // Convert the stacking result to an optimization result
                    return new OptimizationResult
                    {
                        IsSuccessful = false,
                        Message = stackingResult.Message,
                        Players = new List<OptimizedPlayer>()
                    };
                }

                // 5. Optimize the lineup using the knapsack approach
                var lineup = await OptimizeLineupUsingKnapsack(
                    players,
                    remainingPositions,
                    remainingSalary,
                    parameters.OptimizationCriterion,
                    mustStartPlayers.Select(p => p.Player).ToList(),
                    stackingResult.RequiredPlayers);

                // Calculate team breakdown
                var teamBreakdown = lineup
                    .Where(p => !p.Position.Contains("P")) // Exclude pitchers from the count
                    .GroupBy(p => p.Team)
                    .ToDictionary(g => g.Key, g => g.Count());

                // 6. Construct the final result with stack information
                var result = new OptimizationResult
                {
                    IsSuccessful = true,
                    Players = lineup,
                    TotalSalary = lineup.Sum(p => p.Salary),
                    TotalValue = lineup.Sum(p => GetPlayerValue(p, parameters.OptimizationCriterion)),
                    Message = "Lineup successfully optimized",
                    TeamBreakdown = teamBreakdown
                };

                // Add stack info if stacking was used
                if (!string.IsNullOrEmpty(stackingResult.UsedStackStrategy))
                {
                    result.StackInfo = new Dictionary<string, object>
            {
                { "Strategy", stackingResult.UsedStackStrategy },
                { "Reasoning", stackingResult.StackReasoning },
                { "Teams", new Dictionary<string, object>
                    {
                        { "Primary", new { Team = stackingResult.PrimaryTeam, StackSize = stackingResult.PrimaryStackSize } },
                        { "Secondary", new { Team = stackingResult.SecondaryTeam, StackSize = stackingResult.SecondaryStackSize } }
                    }
                }
            };
                }

                return result;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error optimizing MLB lineup");
                return new OptimizationResult
                {
                    IsSuccessful = false,
                    Message = $"Error optimizing lineup: {ex.Message}"
                };
            }
        }


        // Helper methods to implement
        private async Task<List<DKPlayerPool>> GetPlayerPool(OptimizationParameters parameters, MLBParameters mlbParams)
        {
            // Start with a query for all players in the draft group
            var query = _context.DKPlayerPools
                .Where(p => p.DraftGroupId == parameters.DraftGroupId && p.Status != "OUT");

            // Apply watchlist filter if provided
            if (parameters.UserWatchlist != null && parameters.UserWatchlist.Any())
            {
                query = query.Where(p => parameters.UserWatchlist.Contains(p.PlayerDkId));
            }

            // Apply exclusion filter
            if (parameters.ExcludePlayers != null && parameters.ExcludePlayers.Any())
            {
                query = query.Where(p => !parameters.ExcludePlayers.Contains(p.PlayerDkId));
            }

            // Get the initial player pool
            var players = await query.ToListAsync();

            // If strategy teams are specified, add all hitters from those teams
            if (mlbParams.StrategyTeams != null && mlbParams.StrategyTeams.Any())
            {
                _logger.LogInformation($"Adding players from strategy teams: {string.Join(", ", mlbParams.StrategyTeams)}");

                // Get all position players (non-pitchers) from the strategy teams
                var strategyTeamPlayers = await _context.DKPlayerPools
                    .Where(p => p.DraftGroupId == parameters.DraftGroupId &&
                          mlbParams.StrategyTeams.Contains(p.Team) &&
                          p.Status != "OUT" &&
                          !p.Position.Contains("P")) // Exclude pitchers
                    .ToListAsync();

                // Add them to the player pool if they're not already there
                foreach (var player in strategyTeamPlayers)
                {
                    if (!players.Any(p => p.PlayerDkId == player.PlayerDkId))
                    {
                        players.Add(player);
                    }
                }
            }

            _logger.LogInformation($"Total player pool size: {players.Count}");
            return players;
        }

        private async Task<(List<MustStartResult> MustStart, List<string> RemainingPositions, int RemainingSalary)>
            ProcessMustStartPlayers(List<DKPlayerPool> players, OptimizationParameters parameters)
        {
            var mustStartResults = new List<MustStartResult>();
            var remainingPositions = new List<string>(parameters.Positions);
            var remainingSalary = parameters.SalaryCap;

            if (parameters.MustStartPlayers == null || !parameters.MustStartPlayers.Any())
            {
                return (mustStartResults, remainingPositions, remainingSalary);
            }

            // Process each must-start player
            foreach (var mustStartId in parameters.MustStartPlayers)
            {
                // Find the player in the pool
                var player = players.FirstOrDefault(p => p.PlayerDkId == mustStartId);

                if (player == null)
                {
                    // Check if they exist in the database but weren't in the pool
                    var dbPlayer = await _context.DKPlayerPools
                        .FirstOrDefaultAsync(p => p.PlayerDkId == mustStartId && p.DraftGroupId == parameters.DraftGroupId);

                    if (dbPlayer != null)
                    {
                        player = dbPlayer;
                        players.Add(dbPlayer); // Add to pool for future processing
                    }
                    else
                    {
                        // Player not found at all
                        mustStartResults.Add(new MustStartResult
                        {
                            IsError = true,
                            ErrorMessage = $"Must-start player with ID {mustStartId} not found in the player pool"
                        });
                        continue;
                    }
                }

                // For baseball, pitchers go into P positions, everyone else needs position matching
                string positionToUse;

                if (player.Position.Contains("P"))
                {
                    // Find the first available P position
                    positionToUse = remainingPositions.FirstOrDefault(p => p == "P");

                    if (positionToUse == null)
                    {
                        mustStartResults.Add(new MustStartResult
                        {
                            IsError = true,
                            ErrorMessage = $"Cannot place pitcher {player.FullName} in lineup - no pitcher slots available"
                        });
                        continue;
                    }
                }
                else
                {
                    // For position players, find the first available matching position
                    positionToUse = FindMatchingPosition(player, remainingPositions);

                    if (positionToUse == null)
                    {
                        mustStartResults.Add(new MustStartResult
                        {
                            IsError = true,
                            ErrorMessage = $"Cannot place {player.FullName} ({player.Position}) in lineup - no compatible positions available"
                        });
                        continue;
                    }
                }

                // Create the optimized player entry
                var optimizedPlayer = new OptimizedPlayer
                {
                    FullName = player.FullName,
                    PlayerDkId = player.PlayerDkId,
                    Position = player.Position,
                    AssignedPosition = positionToUse,
                    Salary = player.Salary,
                    Team = player.Team,
                    DKppg = player.DKppg
                };

                // Add to results, update remaining positions and salary
                mustStartResults.Add(new MustStartResult
                {
                    Player = optimizedPlayer,
                    IsError = false
                });

                remainingPositions.Remove(positionToUse);
                remainingSalary -= player.Salary;
            }

            return (mustStartResults, remainingPositions, remainingSalary);
        }

        private string FindMatchingPosition(DKPlayerPool player, List<string> availablePositions)
        {
            // For baseball, handle special cases for outfielders
            if (player.Position.Contains("OF") && availablePositions.Contains("OF"))
            {
                return "OF";
            }

            // For other positions, try direct matches
            foreach (var position in availablePositions)
            {
                if (player.Position.Contains(position))
                {
                    return position;
                }
            }

            return null; // No matching position found
        }


        private async Task<StackingResult> ApplyStackingStrategy(
            List<DKPlayerPool> players,
            OptimizationParameters parameters,
            MLBParameters mlbParams,
            List<string> remainingPositions,
            List<MustStartResult> mustStartPlayers)
        {
            // If no strategy teams or no stacking requested, return empty result
            if (mlbParams.StrategyTeams == null || !mlbParams.StrategyTeams.Any() ||
                string.IsNullOrEmpty(mlbParams.StackStrategy))
            {
                return new StackingResult
                {
                    IsSuccessful = true,
                    RequiredPlayers = new List<RequiredPlayer>()
                };
            }

            // Parse the stack strategy
            int primaryStackSize = 0;
            int secondaryStackSize = 0;

            // Determine which stack was used (for user feedback)
            string usedStackStrategy = mlbParams.StackStrategy;
            string stackReasoning = "";

            if (mlbParams.StackStrategy == "Use suggested stack for this slate")
            {
                // Get the optimal strategy from the service
                var draftGroupInfo = await _context.DKPoolsMaps.FirstOrDefaultAsync(p => p.DraftGroupId == parameters.DraftGroupId);

                if (draftGroupInfo?.TotalGames == null)
                {
                    return new StackingResult
                    {
                        IsSuccessful = false,
                        Message = "Could not determine optimal stacking strategy - game count not found"
                    };
                }

                var strategy = _strategyService.GetOptimalStrategy(draftGroupInfo.TotalGames.Value);
                usedStackStrategy = strategy.RecommendedStrategy;
                stackReasoning = strategy.Reasoning;

                var stackRequirements = _strategyService.GetStackRequirements(strategy.RecommendedStrategy);

                primaryStackSize = stackRequirements[0].StackSize;
                secondaryStackSize = stackRequirements[1].StackSize;

                _logger.LogInformation($"Using suggested stack strategy: {primaryStackSize}-{secondaryStackSize}");
            }
            else if (mlbParams.StackStrategy.Contains("-"))
            {
                // Parse the user-specified strategy (e.g., "5-2")
                var parts = mlbParams.StackStrategy.Split('-');
                if (parts.Length != 2 || !int.TryParse(parts[0], out primaryStackSize) || !int.TryParse(parts[1], out secondaryStackSize))
                {
                    return new StackingResult
                    {
                        IsSuccessful = false,
                        Message = $"Invalid stack strategy format: {mlbParams.StackStrategy}"
                    };
                }

                _logger.LogInformation($"Using user-specified stack strategy: {primaryStackSize}-{secondaryStackSize}");
            }
            else
            {
                return new StackingResult
                {
                    IsSuccessful = false,
                    Message = $"Unrecognized stack strategy: {mlbParams.StackStrategy}"
                };
            }

            // Ensure we have enough teams for the strategy
            if (mlbParams.StrategyTeams.Count < (secondaryStackSize > 0 ? 2 : 1))
            {
                return new StackingResult
                {
                    IsSuccessful = false,
                    Message = $"Strategy requires {(secondaryStackSize > 0 ? 2 : 1)} teams for a {primaryStackSize}-{secondaryStackSize} stack"
                };
            }

            // Get the primary and secondary teams
            string primaryTeam = mlbParams.StrategyTeams[0];
            string secondaryTeam = mlbParams.StrategyTeams.Count > 1 ? mlbParams.StrategyTeams[1] : null;

            // Count how many players from each team are already must-starts
            int primaryMustStarts = mustStartPlayers.Count(m => !m.IsError && m.Player.Team == primaryTeam && !m.Player.Position.Contains("P"));
            int secondaryMustStarts = secondaryTeam != null ?
                mustStartPlayers.Count(m => !m.IsError && m.Player.Team == secondaryTeam && !m.Player.Position.Contains("P")) : 0;

            // Adjust required stack sizes based on must-starts
            int primaryNeeded = Math.Max(0, primaryStackSize - primaryMustStarts);
            int secondaryNeeded = Math.Max(0, secondaryStackSize - secondaryMustStarts);

            // Check if we have enough players for the strategy
            var primaryTeamPlayers = players
                .Where(p => p.Team == primaryTeam &&
                       !p.Position.Contains("P") && // Exclude pitchers
                       !mustStartPlayers.Any(m => !m.IsError && m.Player.PlayerDkId == p.PlayerDkId))
                .ToList();

            if (primaryTeamPlayers.Count < primaryNeeded)
            {
                return new StackingResult
                {
                    IsSuccessful = false,
                    Message = $"Not enough position players available from {primaryTeam} for stack of size {primaryStackSize}"
                };
            }

            var secondaryTeamPlayers = secondaryTeam != null ?
                players.Where(p => p.Team == secondaryTeam &&
                          !p.Position.Contains("P") && // Exclude pitchers
                          !mustStartPlayers.Any(m => !m.IsError && m.Player.PlayerDkId == p.PlayerDkId))
                      .ToList() :
                new List<DKPlayerPool>();

            if (secondaryTeam != null && secondaryTeamPlayers.Count < secondaryNeeded)
            {
                return new StackingResult
                {
                    IsSuccessful = false,
                    Message = $"Not enough position players available from {secondaryTeam} for stack of size {secondaryStackSize}"
                };
            }

            // Create required players list - THIS IS THE KEY CHANGE
            var requiredPlayers = new List<RequiredPlayer>();

            // Add requirements for primary team - THIS IS THE KEY CHANGE
            for (int i = 0; i < primaryNeeded; i++)
            {
                requiredPlayers.Add(new RequiredPlayer
                {
                    Team = primaryTeam,
                    Position = "STACK"
                });
            }

            // Add requirements for secondary team - THIS IS THE KEY CHANGE
            for (int i = 0; i < secondaryNeeded; i++)
            {
                requiredPlayers.Add(new RequiredPlayer
                {
                    Team = secondaryTeam,
                    Position = "STACK"
                });
            }

            _logger.LogInformation($"Created {requiredPlayers.Count} required player slots: " +
                $"{requiredPlayers.Count(rp => rp.Team == primaryTeam)} for {primaryTeam}, " +
                $"{requiredPlayers.Count(rp => rp.Team == secondaryTeam)} for {secondaryTeam}");

            return new StackingResult
            {
                IsSuccessful = true,
                RequiredPlayers = requiredPlayers,
                UsedStackStrategy = usedStackStrategy,
                StackReasoning = stackReasoning,
                PrimaryTeam = primaryTeam,
                PrimaryStackSize = primaryStackSize,
                SecondaryTeam = secondaryTeam,
                SecondaryStackSize = secondaryStackSize
            };
        }

        private async Task<List<OptimizedPlayer>> OptimizeLineupUsingKnapsack(
            List<DKPlayerPool> players,
            List<string> positions,
            int salaryCap,
            string optimizationCriterion,
            List<OptimizedPlayer> mustStartPlayers,
            List<RequiredPlayer> requiredPlayers)
        {
            _logger.LogInformation("Starting lineup optimization with strict stacking constraints");

            // Start with the must-start players
            var lineup = new List<OptimizedPlayer>(mustStartPlayers);

            // Extract stack requirements
            string primaryTeam = null;
            string secondaryTeam = null;
            int primaryStackSize = 0;
            int secondaryStackSize = 0;

            // Group the required players by team to get stack requirements
            var stacksByTeam = requiredPlayers
                .Where(p => p.Position == "STACK")
                .GroupBy(p => p.Team)
                .ToDictionary(g => g.Key, g => g.Count());

            if (stacksByTeam.Count >= 1)
            {
                var primary = stacksByTeam.OrderByDescending(kv => kv.Value).First();
                primaryTeam = primary.Key;
                primaryStackSize = primary.Value;
            }

            if (stacksByTeam.Count >= 2)
            {
                var secondary = stacksByTeam.OrderByDescending(kv => kv.Value).Skip(1).First();
                secondaryTeam = secondary.Key;
                secondaryStackSize = secondary.Value;
            }

            _logger.LogInformation($"Stack requirements - Primary: {primaryTeam} ({primaryStackSize}), Secondary: {secondaryTeam} ({secondaryStackSize})");

            // Create a list of players we've already used
            var usedPlayerIds = mustStartPlayers.Select(p => p.PlayerDkId).ToHashSet();

            // Track how many non-pitcher players we have from each team in the lineup
            var teamCounts = mustStartPlayers
                .Where(p => !p.Position.Contains("P")) // Exclude pitchers from stack counts
                .GroupBy(p => p.Team)
                .ToDictionary(g => g.Key, g => g.Count());

            // Initialize team counts for stacking teams
            if (primaryTeam != null && !teamCounts.ContainsKey(primaryTeam))
            {
                teamCounts[primaryTeam] = 0;
            }

            if (secondaryTeam != null && !teamCounts.ContainsKey(secondaryTeam))
            {
                teamCounts[secondaryTeam] = 0;
            }

            // Create position tracking
            var remainingPositions = new Dictionary<string, int>();
            foreach (var pos in positions)
            {
                if (!remainingPositions.ContainsKey(pos))
                {
                    remainingPositions[pos] = 0;
                }
                remainingPositions[pos]++;
            }

            // Remove positions used by must-start players
            foreach (var player in mustStartPlayers)
            {
                if (remainingPositions.ContainsKey(player.AssignedPosition))
                {
                    remainingPositions[player.AssignedPosition]--;
                    if (remainingPositions[player.AssignedPosition] <= 0)
                    {
                        remainingPositions.Remove(player.AssignedPosition);
                    }
                }
            }

            _logger.LogInformation($"Remaining positions: {string.Join(", ", remainingPositions.Select(kv => $"{kv.Key}: {kv.Value}"))}");

            // Get available primary and secondary team players
            var availablePrimaryPlayers = primaryTeam != null ?
                players.Where(p => p.Team == primaryTeam &&
                             !p.Position.Contains("P") && // Exclude pitchers
                             !usedPlayerIds.Contains(p.PlayerDkId))
                      .ToList() :
                new List<DKPlayerPool>();

            var availableSecondaryPlayers = secondaryTeam != null ?
                players.Where(p => p.Team == secondaryTeam &&
                             !p.Position.Contains("P") && // Exclude pitchers
                             !usedPlayerIds.Contains(p.PlayerDkId))
                      .ToList() :
                new List<DKPlayerPool>();

            _logger.LogInformation($"Available primary team players: {availablePrimaryPlayers.Count}");
            _logger.LogInformation($"Available secondary team players: {availableSecondaryPlayers.Count}");

            // Sort players by DKPPG within each team
            availablePrimaryPlayers = availablePrimaryPlayers
                .OrderByDescending(p => p.DKppg ?? 0)
                .ToList();

            availableSecondaryPlayers = availableSecondaryPlayers
                .OrderByDescending(p => p.DKppg ?? 0)
                .ToList();

            // Function to try to add a player from a specific team to a specific position
            bool TryAddPlayerToPosition(string position, List<DKPlayerPool> teamPlayers, ref int remainingSalary)
            {
                foreach (var player in teamPlayers)
                {
                    if (IsEligibleForPosition(player, position) && player.Salary <= remainingSalary && !usedPlayerIds.Contains(player.PlayerDkId))
                    {
                        // Add player to lineup
                        lineup.Add(new OptimizedPlayer
                        {
                            FullName = player.FullName,
                            PlayerDkId = player.PlayerDkId,
                            Position = player.Position,
                            AssignedPosition = position,
                            Salary = player.Salary,
                            Team = player.Team,
                            DKppg = player.DKppg
                        });

                        // Update tracking
                        usedPlayerIds.Add(player.PlayerDkId);
                        remainingSalary -= player.Salary;

                        // Update team count
                        if (!teamCounts.ContainsKey(player.Team))
                        {
                            teamCounts[player.Team] = 0;
                        }
                        teamCounts[player.Team]++;

                        _logger.LogInformation($"Added {player.FullName} ({player.Team}) to position {position}");

                        return true;
                    }
                }

                return false;
            }

            // Step 1: First pass - try to add players from primary team
            int targetPrimary = primaryStackSize;
            int currentPrimary = teamCounts.GetValueOrDefault(primaryTeam, 0);
            int neededPrimary = Math.Max(0, targetPrimary - currentPrimary);

            _logger.LogInformation($"Need {neededPrimary} more players from primary team {primaryTeam}");

            if (neededPrimary > 0)
            {
                // Try to add players from primary team to each position
                foreach (var posEntry in remainingPositions.ToList())
                {
                    string position = posEntry.Key;
                    int count = posEntry.Value;

                    for (int i = 0; i < count; i++)
                    {
                        if (teamCounts.GetValueOrDefault(primaryTeam, 0) >= targetPrimary)
                        {
                            break; // We've met our target
                        }

                        if (TryAddPlayerToPosition(position, availablePrimaryPlayers, ref salaryCap))
                        {
                            // Decrement remaining positions
                            remainingPositions[position]--;
                            if (remainingPositions[position] <= 0)
                            {
                                remainingPositions.Remove(position);
                            }
                        }
                    }

                    if (teamCounts.GetValueOrDefault(primaryTeam, 0) >= targetPrimary)
                    {
                        break; // We've met our target
                    }
                }
            }

            _logger.LogInformation($"After primary team fill: {teamCounts.GetValueOrDefault(primaryTeam, 0)}/{targetPrimary} from {primaryTeam}");

            // Step 2: Second pass - try to add players from secondary team
            int targetSecondary = secondaryStackSize;
            int currentSecondary = teamCounts.GetValueOrDefault(secondaryTeam, 0);
            int neededSecondary = Math.Max(0, targetSecondary - currentSecondary);

            _logger.LogInformation($"Need {neededSecondary} more players from secondary team {secondaryTeam}");

            if (neededSecondary > 0)
            {
                // Try to add players from secondary team to each position
                foreach (var posEntry in remainingPositions.ToList())
                {
                    string position = posEntry.Key;
                    int count = posEntry.Value;

                    for (int i = 0; i < count; i++)
                    {
                        if (teamCounts.GetValueOrDefault(secondaryTeam, 0) >= targetSecondary)
                        {
                            break; // We've met our target
                        }

                        if (TryAddPlayerToPosition(position, availableSecondaryPlayers, ref salaryCap))
                        {
                            // Decrement remaining positions
                            remainingPositions[position]--;
                            if (remainingPositions[position] <= 0)
                            {
                                remainingPositions.Remove(position);
                            }
                        }
                    }

                    if (teamCounts.GetValueOrDefault(secondaryTeam, 0) >= targetSecondary)
                    {
                        break; // We've met our target
                    }
                }
            }

            _logger.LogInformation($"After secondary team fill: {teamCounts.GetValueOrDefault(secondaryTeam, 0)}/{targetSecondary} from {secondaryTeam}");

            // Step 3: If we haven't met stack requirements yet, check if we need to swap positions
            if (teamCounts.GetValueOrDefault(primaryTeam, 0) < targetPrimary ||
                teamCounts.GetValueOrDefault(secondaryTeam, 0) < targetSecondary)
            {
                _logger.LogWarning("Could not meet stack requirements with direct assignment. Trying position swapping...");

                // TODO: Implement a position swapping algorithm if needed
                // This would involve removing players from the lineup and trying different combinations
            }

            // Step 4: Fill remaining positions with best players
            _logger.LogInformation($"Filling remaining positions: {string.Join(", ", remainingPositions.Select(kv => $"{kv.Key}: {kv.Value}"))}");

            foreach (var posEntry in remainingPositions.ToList())
            {
                string position = posEntry.Key;
                int count = posEntry.Value;

                // Find eligible players for this position
                var eligiblePlayers = players
                    .Where(p => IsEligibleForPosition(p, position) &&
                           !usedPlayerIds.Contains(p.PlayerDkId) &&
                           p.Salary <= salaryCap)
                    .OrderByDescending(p => p.DKppg ?? 0)
                    .ToList();

                for (int i = 0; i < count; i++)
                {
                    if (eligiblePlayers.Count == 0)
                    {
                        _logger.LogWarning($"No eligible players left for position {position}");
                        break;
                    }

                    var bestPlayer = eligiblePlayers.First();

                    // Add player to lineup
                    lineup.Add(new OptimizedPlayer
                    {
                        FullName = bestPlayer.FullName,
                        PlayerDkId = bestPlayer.PlayerDkId,
                        Position = bestPlayer.Position,
                        AssignedPosition = position,
                        Salary = bestPlayer.Salary,
                        Team = bestPlayer.Team,
                        DKppg = bestPlayer.DKppg
                    });

                    // Update tracking
                    usedPlayerIds.Add(bestPlayer.PlayerDkId);
                    salaryCap -= bestPlayer.Salary;

                    // Update team count
                    if (!teamCounts.ContainsKey(bestPlayer.Team))
                    {
                        teamCounts[bestPlayer.Team] = 0;
                    }
                    if (!bestPlayer.Position.Contains("P")) // Don't count pitchers
                    {
                        teamCounts[bestPlayer.Team]++;
                    }

                    _logger.LogInformation($"Added {bestPlayer.FullName} ({bestPlayer.Team}) to position {position}");

                    // Remove the player from eligible list
                    eligiblePlayers.Remove(bestPlayer);
                }

                // Update remaining positions
                remainingPositions.Remove(position);
            }

            // Log final team counts
            _logger.LogInformation("Final team breakdown:");
            foreach (var team in teamCounts.Keys)
            {
                _logger.LogInformation($"{team}: {teamCounts[team]} players");
            }

            // Check if we met stacking requirements
            if (teamCounts.GetValueOrDefault(primaryTeam, 0) < targetPrimary)
            {
                _logger.LogWarning($"Could not fully meet primary stack requirement for {primaryTeam}: {teamCounts.GetValueOrDefault(primaryTeam, 0)}/{targetPrimary}");
            }

            if (teamCounts.GetValueOrDefault(secondaryTeam, 0) < targetSecondary)
            {
                _logger.LogWarning($"Could not fully meet secondary stack requirement for {secondaryTeam}: {teamCounts.GetValueOrDefault(secondaryTeam, 0)}/{targetSecondary}");
            }

            // Return the sorted lineup
            return SortLineupByPositionOrder(lineup);
        }


        // Helper method to find the best player for a position while prioritizing stack requirements
        private PlayerPositionMatch FindBestPlayerForPositionWithStackPriority(
            List<DKPlayerPool> players,
            List<string> availablePositions,
            HashSet<int> usedPlayerIds,
            int salaryCap,
            List<string> teamsToStackMore,
            Dictionary<string, int> stackRequirements,
            Dictionary<string, int> currentTeamCounts,
            string optimizationCriterion)
        {
            PlayerPositionMatch bestMatch = null;
            double bestScore = 0;

            foreach (var position in availablePositions)
            {
                var eligiblePlayers = players
                    .Where(p => IsEligibleForPosition(p, position) &&
                           !usedPlayerIds.Contains(p.PlayerDkId) &&
                           p.Salary <= salaryCap &&
                           !p.Position.Contains("P") && // Only consider non-pitchers
                           teamsToStackMore.Contains(p.Team)) // Only consider players from teams we need more of
                    .ToList();

                foreach (var player in eligiblePlayers)
                {
                    // Calculate how far we are from meeting this team's requirement
                    int targetCount = stackRequirements[player.Team];
                    int currentCount = currentTeamCounts.GetValueOrDefault(player.Team, 0);
                    int deficit = targetCount - currentCount;

                    // Calculate base value
                    decimal value = GetPlayerValue(new OptimizedPlayer { DKppg = player.DKppg }, optimizationCriterion);

                    // Apply a bonus based on how urgently we need players from this team
                    // The larger the deficit, the bigger the bonus
                    double stackingBonus = 1 + (deficit * 0.5); // 50% bonus per player needed

                    double score = (double)(value * (decimal)stackingBonus);

                    if (bestMatch == null || score > bestScore)
                    {
                        bestMatch = new PlayerPositionMatch
                        {
                            Player = player,
                            Position = position,
                            Score = score
                        };
                        bestScore = score;
                    }
                }
            }

            return bestMatch;
        }

        // Helper method to find the best player for a position
        private PlayerPositionMatch FindBestPlayerForPosition(
            List<DKPlayerPool> players,
            List<string> availablePositions,
            HashSet<int> usedPlayerIds,
            int salaryCap,
            string optimizationCriterion)
        {
            PlayerPositionMatch bestMatch = null;
            double bestScore = 0;

            foreach (var position in availablePositions)
            {
                var eligiblePlayers = players
                    .Where(p => IsEligibleForPosition(p, position) &&
                           !usedPlayerIds.Contains(p.PlayerDkId) &&
                           p.Salary <= salaryCap)
                    .ToList();

                foreach (var player in eligiblePlayers)
                {
                    decimal value = GetPlayerValue(new OptimizedPlayer { DKppg = player.DKppg }, optimizationCriterion);
                    double score = (double)value;

                    if (bestMatch == null || score > bestScore)
                    {
                        bestMatch = new PlayerPositionMatch
                        {
                            Player = player,
                            Position = position,
                            Score = score
                        };
                        bestScore = score;
                    }
                }
            }

            return bestMatch;
        }

        // Helper class for player-position matching
        private class PlayerPositionMatch
        {
            public DKPlayerPool Player { get; set; }
            public string Position { get; set; }
            public double Score { get; set; }
        }
        private bool IsEligibleForPosition(DKPlayerPool player, string position)
        {
            // Log the check for debugging
            _logger.LogDebug($"Checking if {player.FullName} with position {player.Position} is eligible for {position}");

            // Pitchers can only go into P slots
            if (player.Position.Contains("SP") || player.Position.Contains("RP"))
            {
                return position == "P";
            }

            // Handle position players
            switch (position)
            {
                case "C": return player.Position.Contains("C");
                case "1B": return player.Position.Contains("1B");
                case "2B": return player.Position.Contains("2B");
                case "3B": return player.Position.Contains("3B");
                case "SS": return player.Position.Contains("SS");
                case "OF":
                    return player.Position.Contains("OF") ||
                                 player.Position.Contains("LF") ||
                                 player.Position.Contains("CF") ||
                                 player.Position.Contains("RF");
                default: return false;
            }
        }

        private List<OptimizedPlayer> SortLineupByPositionOrder(List<OptimizedPlayer> lineup)
        {
            // Define the order of positions for display
            var positionOrder = new Dictionary<string, int>
    {
        { "P", 1 },
        { "C", 2 },
        { "1B", 3 },
        { "2B", 4 },
        { "3B", 5 },
        { "SS", 6 },
        { "OF", 7 }
    };

            return lineup
                .OrderBy(p => positionOrder.ContainsKey(p.AssignedPosition) ?
                             positionOrder[p.AssignedPosition] : 100)
                .ToList();
        }



        private decimal GetPlayerValue(OptimizedPlayer player, string optimizationCriterion)
        {
            // Default to DKPPG if no criterion specified
            if (string.IsNullOrEmpty(optimizationCriterion))
            {
                return player.DKppg ?? 0;
            }

            // Handle different optimization criteria
            switch (optimizationCriterion.ToUpperInvariant())
            {
                case "DKPPG":
                    return player.DKppg ?? 0;

                case "SALARY":
                    // For maximizing salary within cap (edge case)
                    return player.Salary;

                case "VALUE":
                    // Value = DKPPG / (Salary/1000)
                    if (player.Salary <= 0) return 0;
                    return (player.DKppg ?? 0) / (player.Salary / 1000.0m);

                case "WEIGHTED_OPS":
                    // In a real implementation, you'd fetch this from a database or service
                    // For now, we'll just use DKPPG as a proxy
                    return player.DKppg ?? 0;

                default:
                    return player.DKppg ?? 0;
            }
        }
    }

    // Helper classes for MLB optimization
    public class MustStartResult
    {
        public OptimizedPlayer Player { get; set; }
        public bool IsError { get; set; }
        public string ErrorMessage { get; set; }
    }

    public class StackingResult
    {
        public bool IsSuccessful { get; set; }
        public string Message { get; set; }
        public List<RequiredPlayer> RequiredPlayers { get; set; } = new List<RequiredPlayer>();
        public string UsedStackStrategy { get; set; }
        public string StackReasoning { get; set; }
        public string PrimaryTeam { get; set; }
        public int PrimaryStackSize { get; set; }
        public string SecondaryTeam { get; set; }
        public int SecondaryStackSize { get; set; }
    }

    public class RequiredPlayer
    {
        public int PlayerId { get; set; }
        public string Team { get; set; }
        public string Position { get; set; }
    }
}