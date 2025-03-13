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

                // 4. Determine the stacking strategy
                var stackDefinition = await DetermineStackStrategy(parameters, mlbParams);

                // If we have a valid stacking strategy, try both arrangements
                if (stackDefinition.IsValid &&
                    mlbParams.StrategyTeams != null &&
                    mlbParams.StrategyTeams.Count >= 2)
                {
                    // Create two versions of the stacking arrangements
                    var normalArrangement = new StackArrangement
                    {
                        PrimaryTeam = mlbParams.StrategyTeams[0],
                        SecondaryTeam = mlbParams.StrategyTeams[1],
                        PrimarySize = stackDefinition.PrimarySize,
                        SecondarySize = stackDefinition.SecondarySize
                    };

                    var reversedArrangement = new StackArrangement
                    {
                        PrimaryTeam = mlbParams.StrategyTeams[1],
                        SecondaryTeam = mlbParams.StrategyTeams[0],
                        PrimarySize = stackDefinition.PrimarySize,
                        SecondarySize = stackDefinition.SecondarySize
                    };

                    // Try both arrangements and choose the best one
                    var normalLineup = await OptimizeWithStackArrangement(
                        players,
                        normalArrangement,
                        mustStartPlayers,
                        remainingPositions,
                        remainingSalary,
                        parameters);

                    var reversedLineup = await OptimizeWithStackArrangement(
                        players,
                        reversedArrangement,
                        mustStartPlayers,
                        remainingPositions,
                        remainingSalary,
                        parameters);

                    // Choose the best lineup based on projected points
                    var bestLineup = ChooseBestLineup(normalLineup, reversedLineup, parameters.OptimizationCriterion);

                    // Include stack info in the response
                    var stackInfo = CreateStackInfo(
                        bestLineup == normalLineup ? normalArrangement : reversedArrangement,
                        stackDefinition.Reasoning);

                    // Create team breakdown
                    var teamBreakdown = bestLineup.Players
                        .GroupBy(p => p.Team)
                        .ToDictionary(g => g.Key, g => g.Count());

                    return new OptimizationResult
                    {
                        IsSuccessful = bestLineup.IsSuccessful,
                        Message = bestLineup.Message,
                        Players = bestLineup.Players,
                        TotalSalary = bestLineup.TotalSalary,
                        TotalValue = bestLineup.TotalValue,
                        StackInfo = stackInfo,
                        TeamBreakdown = teamBreakdown
                    };
                }
                else
                {
                    // No valid stacking strategy or not enough teams, proceed with standard optimization
                    return await OptimizeWithoutStacking(
                        players, mustStartPlayers, remainingPositions, remainingSalary, parameters);
                }
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

        private OptimizationResult ChooseBestLineup(
            OptimizationResult lineup1,
            OptimizationResult lineup2,
            string optimizationCriterion)
        {
            // If either lineup failed, return the successful one
            if (!lineup1.IsSuccessful) return lineup2;
            if (!lineup2.IsSuccessful) return lineup1;

            // Calculate total value for each lineup based on optimization criterion
            decimal lineup1Value = lineup1.Players.Sum(p => GetPlayerValue(p, optimizationCriterion));
            decimal lineup2Value = lineup2.Players.Sum(p => GetPlayerValue(p, optimizationCriterion));

            // Return the lineup with the higher value
            return lineup1Value >= lineup2Value ? lineup1 : lineup2;
        }

        private Dictionary<string, object> CreateStackInfo(StackArrangement arrangement, string reasoning)
        {
            return new Dictionary<string, object>
            {
                { "Strategy", $"{arrangement.PrimarySize}-{arrangement.SecondarySize}" },
                { "Reasoning", reasoning },
                { "Teams", new Dictionary<string, object>
                    {
                        { "Primary", new Dictionary<string, object>
                            {
                                { "team", arrangement.PrimaryTeam },
                                { "stackSize", arrangement.PrimarySize }
                            }
                        },
                        { "Secondary", new Dictionary<string, object>
                            {
                                { "team", arrangement.SecondaryTeam },
                                { "stackSize", arrangement.SecondarySize }
                            }
                        }
                    }
                }
            };
        }

        private async Task<OptimizationResult> OptimizeWithoutStacking(
            List<DKPlayerPool> players,
            List<MustStartResult> mustStartPlayers,
            List<string> remainingPositions,
            int remainingSalary,
            OptimizationParameters parameters)
        {
            // 5. Optimize the lineup using the knapsack approach
            var lineup = await OptimizeLineupUsingKnapsack(
                players,
                remainingPositions,
                remainingSalary,
                parameters.OptimizationCriterion,
                mustStartPlayers.Select(p => p.Player).ToList(),
                new List<RequiredPlayer>());

            // 6. Construct the final result
            return new OptimizationResult
            {
                IsSuccessful = true,
                Players = lineup,
                TotalSalary = lineup.Sum(p => p.Salary),
                TotalValue = lineup.Sum(p => GetPlayerValue(p, parameters.OptimizationCriterion)),
                Message = "Lineup successfully optimized"
            };
        }

        private async Task<OptimizationResult> OptimizeWithStackArrangement(
            List<DKPlayerPool> players,
            StackArrangement arrangement,
            List<MustStartResult> mustStartPlayers,
            List<string> remainingPositions,
            int remainingSalary,
            OptimizationParameters parameters)
        {
            try
            {
                // Count how many players from each team are already must-starts
                int primaryMustStarts = mustStartPlayers.Count(m => !m.IsError && m.Player.Team == arrangement.PrimaryTeam && !m.Player.Position.Contains("P"));
                int secondaryMustStarts = mustStartPlayers.Count(m => !m.IsError && m.Player.Team == arrangement.SecondaryTeam && !m.Player.Position.Contains("P"));

                // Adjust required stack sizes based on must-starts (without exceeding)
                int primaryNeeded = Math.Min(arrangement.PrimarySize - primaryMustStarts, arrangement.PrimarySize);
                primaryNeeded = Math.Max(0, primaryNeeded); // Ensure it's not negative

                int secondaryNeeded = Math.Min(arrangement.SecondarySize - secondaryMustStarts, arrangement.SecondarySize);
                secondaryNeeded = Math.Max(0, secondaryNeeded); // Ensure it's not negative

                // Check if we have enough players for the strategy
                var primaryTeamPlayers = players
                    .Where(p => p.Team == arrangement.PrimaryTeam &&
                           !p.Position.Contains("P") && // Exclude pitchers
                           !mustStartPlayers.Any(m => !m.IsError && m.Player.PlayerDkId == p.PlayerDkId))
                    .ToList();

                if (primaryTeamPlayers.Count < primaryNeeded)
                {
                    return new OptimizationResult
                    {
                        IsSuccessful = false,
                        Message = $"Not enough position players available from {arrangement.PrimaryTeam} for stack of size {arrangement.PrimarySize}"
                    };
                }

                var secondaryTeamPlayers = players
                    .Where(p => p.Team == arrangement.SecondaryTeam &&
                              !p.Position.Contains("P") && // Exclude pitchers
                              !mustStartPlayers.Any(m => !m.IsError && m.Player.PlayerDkId == p.PlayerDkId))
                          .ToList();

                if (secondaryTeamPlayers.Count < secondaryNeeded)
                {
                    return new OptimizationResult
                    {
                        IsSuccessful = false,
                        Message = $"Not enough position players available from {arrangement.SecondaryTeam} for stack of size {arrangement.SecondarySize}"
                    };
                }

                // Create required players constraints
                var requiredPlayers = new List<RequiredPlayer>();

                // Only add team as constraint if we need more players from it
                if (primaryNeeded > 0)
                {
                    requiredPlayers.Add(new RequiredPlayer
                    {
                        Team = arrangement.PrimaryTeam,
                        Position = "STACK", // Special marker to indicate this is a stacking requirement
                        Count = primaryNeeded, // Exact number needed
                        IsExactCount = true  // This is now an exact count constraint, not a minimum
                    });
                }

                if (secondaryNeeded > 0)
                {
                    requiredPlayers.Add(new RequiredPlayer
                    {
                        Team = arrangement.SecondaryTeam,
                        Position = "STACK", // Special marker to indicate this is a stacking requirement
                        Count = secondaryNeeded, // Exact number needed
                        IsExactCount = true  // This is now an exact count constraint, not a minimum
                    });
                }

                // Optimize the lineup using the updated constraints
                var lineup = await OptimizeLineupUsingKnapsack(
                    players,
                    remainingPositions,
                    remainingSalary,
                    parameters.OptimizationCriterion,
                    mustStartPlayers.Select(p => p.Player).ToList(),
                    requiredPlayers);

                // Return the optimized result
                var totalValue = lineup.Sum(p => GetPlayerValue(p, parameters.OptimizationCriterion));

                return new OptimizationResult
                {
                    IsSuccessful = true,
                    Players = lineup,
                    TotalSalary = lineup.Sum(p => p.Salary),
                    TotalValue = totalValue,
                    Message = "Lineup successfully optimized with stack"
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Error optimizing with stack arrangement {arrangement.PrimaryTeam}-{arrangement.SecondaryTeam}");
                return new OptimizationResult
                {
                    IsSuccessful = false,
                    Message = $"Error optimizing with stack: {ex.Message}"
                };
            }
        }

        private async Task<StackDefinition> DetermineStackStrategy(OptimizationParameters parameters, MLBParameters mlbParams)
        {
            if (string.IsNullOrEmpty(mlbParams.StackStrategy) || mlbParams.StrategyTeams == null || !mlbParams.StrategyTeams.Any())
            {
                return new StackDefinition { IsValid = false };
            }

            // Parse the stack strategy
            int primaryStackSize = 0;
            int secondaryStackSize = 0;
            string reasoning = string.Empty;

            if (mlbParams.StackStrategy == "Use suggested stack for this slate")
            {
                // Get the optimal strategy from the service
                var draftGroupInfo = await _context.DKPoolsMaps.FirstOrDefaultAsync(p => p.DraftGroupId == parameters.DraftGroupId);

                if (draftGroupInfo?.TotalGames == null)
                {
                    return new StackDefinition { IsValid = false };
                }

                var strategy = _strategyService.GetOptimalStrategy(draftGroupInfo.TotalGames.Value);
                var stackRequirements = _strategyService.GetStackRequirements(strategy.RecommendedStrategy);

                primaryStackSize = stackRequirements[0].StackSize;
                secondaryStackSize = stackRequirements[1].StackSize;
                reasoning = strategy.Reasoning;

                _logger.LogInformation($"Using suggested stack strategy: {primaryStackSize}-{secondaryStackSize}");
            }
            else if (mlbParams.StackStrategy.Contains("-"))
            {
                // Parse the user-specified strategy (e.g., "5-2")
                var parts = mlbParams.StackStrategy.Split('-');
                if (parts.Length != 2 || !int.TryParse(parts[0], out primaryStackSize) || !int.TryParse(parts[1], out secondaryStackSize))
                {
                    return new StackDefinition { IsValid = false };
                }

                reasoning = $"For a custom stack, using {primaryStackSize} players from one team and {secondaryStackSize} from another team.";
                _logger.LogInformation($"Using user-specified stack strategy: {primaryStackSize}-{secondaryStackSize}");
            }
            else
            {
                return new StackDefinition { IsValid = false };
            }

            return new StackDefinition
            {
                IsValid = true,
                PrimarySize = primaryStackSize,
                SecondarySize = secondaryStackSize,
                Reasoning = reasoning
            };
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
                    DKppg = player.DKppg,
                    OptimalPosition = positionToUse // Set the optimal position
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

        private async Task<List<OptimizedPlayer>> OptimizeLineupUsingKnapsack(
            List<DKPlayerPool> players,
            List<string> positions,
            int salaryCap,
            string optimizationCriterion,
            List<OptimizedPlayer> mustStartPlayers,
            List<RequiredPlayer> requiredPlayers)
        {
            // Start with the must-start players
            var lineup = new List<OptimizedPlayer>(mustStartPlayers);

            // Calculate the remaining players needed for each position
            var positionCounts = positions.GroupBy(p => p)
                                         .ToDictionary(g => g.Key, g => g.Count());

            // Subtract positions used by must-start players
            foreach (var player in mustStartPlayers)
            {
                if (positionCounts.ContainsKey(player.AssignedPosition))
                {
                    positionCounts[player.AssignedPosition]--;
                }
            }

            // Remove positions that are already filled
            positionCounts = positionCounts.Where(kv => kv.Value > 0)
                                          .ToDictionary(kv => kv.Key, kv => kv.Value);

            // Get stacking requirements
            var stackRequirements = requiredPlayers
                .Where(p => p.Position == "STACK")
                .GroupBy(p => p.Team)
                .ToDictionary(g => g.Key, g => g.First());

            // Create tracking for each team to ensure we don't exceed the exact count limits
            var teamCounts = mustStartPlayers
                .Where(p => !p.Position.Contains("P")) // Only consider non-pitchers for stacking
                .GroupBy(p => p.Team)
                .ToDictionary(g => g.Key, g => g.Count());

            // Create a list of players we've already used
            var usedPlayerIds = mustStartPlayers.Select(p => p.PlayerDkId).ToHashSet();

            // Organize available players by position
            var availablePlayersByPosition = new Dictionary<string, List<DKPlayerPool>>();
            foreach (var position in positionCounts.Keys)
            {
                availablePlayersByPosition[position] = players
                    .Where(p => IsEligibleForPosition(p, position) &&
                           !usedPlayerIds.Contains(p.PlayerDkId))
                    .ToList();
            }

            // First, let's try to fill stacking requirements with exactly the right number of players
            foreach (var stackReq in stackRequirements.Values)
            {
                string team = stackReq.Team;
                int exactCount = stackReq.Count;
                bool isExactCount = stackReq.IsExactCount;

                // Initialize team count if it doesn't exist
                if (!teamCounts.ContainsKey(team))
                {
                    teamCounts[team] = 0;
                }

                // Calculate how many more players we need from this team
                int playersNeeded = exactCount;

                // Skip if we already have enough or too many players from this team
                if (teamCounts[team] >= exactCount && isExactCount)
                {
                    continue;
                }

                // Adjust if we already have some players from this team
                playersNeeded -= teamCounts[team];

                // Get available players from this team
                var teamPlayers = players
                    .Where(p => p.Team == team &&
                          !p.Position.Contains("P") && // Exclude pitchers
                          !usedPlayerIds.Contains(p.PlayerDkId))
                    .OrderByDescending(p => GetPlayerValue(new OptimizedPlayer { DKppg = p.DKppg }, optimizationCriterion))
                    .ToList();

                // Try to fill positions with players from this team
                int playersAdded = 0;
                foreach (var position in positionCounts.Keys.ToList())
                {
                    // Skip if we've already added enough players from this team
                    if (playersAdded >= playersNeeded) break;

                    // Find eligible players for this position
                    var eligiblePlayers = teamPlayers
                        .Where(p => IsEligibleForPosition(p, position))
                        .ToList();

                    if (eligiblePlayers.Any() && positionCounts[position] > 0)
                    {
                        // Take the best player for this position
                        var selectedPlayer = eligiblePlayers.First();

                        // Add to lineup
                        lineup.Add(new OptimizedPlayer
                        {
                            FullName = selectedPlayer.FullName,
                            PlayerDkId = selectedPlayer.PlayerDkId,
                            Position = selectedPlayer.Position,
                            AssignedPosition = position,
                            Salary = selectedPlayer.Salary,
                            Team = selectedPlayer.Team,
                            DKppg = selectedPlayer.DKppg,
                            OptimalPosition = position // Set the optimal position
                        });

                        // Update tracking
                        usedPlayerIds.Add(selectedPlayer.PlayerDkId);
                        positionCounts[position]--;
                        if (positionCounts[position] == 0)
                        {
                            positionCounts.Remove(position);
                        }
                        playersAdded++;
                        teamCounts[team]++;

                        // Update remaining salary
                        salaryCap -= selectedPlayer.Salary;

                        // Remove this player from consideration
                        teamPlayers.Remove(selectedPlayer);
                    }
                }
            }

            // Now, fill remaining positions with the best available players that don't violate stack constraints
            while (positionCounts.Any())
            {
                // Calculate the value-to-salary ratio for each player in each remaining position
                var bestPositionPlayer = new KeyValuePair<string, DKPlayerPool>(null, null);
                double bestRatio = 0;

                foreach (var positionEntry in positionCounts)
                {
                    string position = positionEntry.Key;
                    var eligiblePlayers = availablePlayersByPosition[position]
                        .Where(p => !usedPlayerIds.Contains(p.PlayerDkId) && p.Salary <= salaryCap)
                        .ToList();

                    // Filter out players that would exceed exact stack count constraints
                    eligiblePlayers = eligiblePlayers.Where(p =>
                        !stackRequirements.ContainsKey(p.Team) ||
                        !stackRequirements[p.Team].IsExactCount ||
                        (teamCounts.ContainsKey(p.Team) ? teamCounts[p.Team] : 0) < stackRequirements[p.Team].Count
                    ).ToList();

                    foreach (var player in eligiblePlayers)
                    {
                        // Check if this player helps fulfill any remaining stack requirements
                        bool helpsStacking = stackRequirements.ContainsKey(player.Team) &&
                                            !stackRequirements[player.Team].IsExactCount &&
                                            (teamCounts.ContainsKey(player.Team) ? teamCounts[player.Team] : 0) < stackRequirements[player.Team].Count;

                        // Also check if adding this player would exceed max stack size for a team
                        bool exceedsStackLimit = stackRequirements.ContainsKey(player.Team) &&
                                                stackRequirements[player.Team].IsExactCount &&
                                                (teamCounts.ContainsKey(player.Team) ? teamCounts[player.Team] : 0) >= stackRequirements[player.Team].Count;

                        // Skip this player if it would exceed the stack limit
                        if (exceedsStackLimit)
                        {
                            continue;
                        }

                        // Calculate value - use a bonus for stack-helping players
                        decimal value = GetPlayerValue(new OptimizedPlayer { DKppg = player.DKppg }, optimizationCriterion);
                        if (helpsStacking)
                        {
                            value *= 1.5m; // 50% bonus for helping with stack
                        }

                        // Calculate ratio
                        double ratio = (double)(value / player.Salary);

                        if (ratio > bestRatio)
                        {
                            bestRatio = ratio;
                            bestPositionPlayer = new KeyValuePair<string, DKPlayerPool>(position, player);
                        }
                    }
                }

                // If we couldn't find a player for any position, break
                if (bestPositionPlayer.Key == null)
                {
                    _logger.LogWarning("Could not find valid player for any remaining position within salary cap");
                    break;
                }

                // Add the best player to the lineup
                string selectedPosition = bestPositionPlayer.Key;
                DKPlayerPool selectedPlayer = bestPositionPlayer.Value;

                lineup.Add(new OptimizedPlayer
                {
                    FullName = selectedPlayer.FullName,
                    PlayerDkId = selectedPlayer.PlayerDkId,
                    Position = selectedPlayer.Position,
                    AssignedPosition = selectedPosition,
                    Salary = selectedPlayer.Salary,
                    Team = selectedPlayer.Team,
                    DKppg = selectedPlayer.DKppg,
                    OptimalPosition = selectedPosition // Set the optimal position
                });

                // Update tracking
                usedPlayerIds.Add(selectedPlayer.PlayerDkId);
                positionCounts[selectedPosition]--;
                if (positionCounts[selectedPosition] == 0)
                {
                    positionCounts.Remove(selectedPosition);
                }

                // Update team counts
                if (!teamCounts.ContainsKey(selectedPlayer.Team))
                {
                    teamCounts[selectedPlayer.Team] = 0;
                }
                teamCounts[selectedPlayer.Team]++;

                // Update remaining salary
                salaryCap -= selectedPlayer.Salary;
            }

            // Check if we successfully filled all positions
            if (positionCounts.Any())
            {
                _logger.LogWarning($"Could not fill all positions: {string.Join(", ", positionCounts.Select(kv => $"{kv.Key}: {kv.Value}"))}");

                // Try a fallback approach - try to maximize DKppg without position constraints
                // This ensures we return a valid lineup even if it doesn't meet all constraints
                var remainingSalary = salaryCap;
                var remainingPlayers = players
                    .Where(p => !usedPlayerIds.Contains(p.PlayerDkId))
                    .OrderByDescending(p => p.DKppg)
                    .ToList();

                foreach (var position in positionCounts.Keys.ToList())
                {
                    for (int i = 0; i < positionCounts[position]; i++)
                    {
                        // Find the best player who can play this position
                        var bestPlayer = remainingPlayers
                            .Where(p => IsEligibleForPosition(p, position) && p.Salary <= remainingSalary)
                            .OrderByDescending(p => p.DKppg)
                            .FirstOrDefault();

                        if (bestPlayer != null)
                        {
                            lineup.Add(new OptimizedPlayer
                            {
                                FullName = bestPlayer.FullName,
                                PlayerDkId = bestPlayer.PlayerDkId,
                                Position = bestPlayer.Position,
                                AssignedPosition = position,
                                Salary = bestPlayer.Salary,
                                Team = bestPlayer.Team,
                                DKppg = bestPlayer.DKppg,
                                OptimalPosition = position // Set the optimal position
                            });

                            remainingSalary -= bestPlayer.Salary;
                            remainingPlayers.Remove(bestPlayer);
                        }
                    }
                }
            }

            // Sort lineup by position order for better presentation
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

    public class StackDefinition
    {
        public bool IsValid { get; set; }
        public int PrimarySize { get; set; }
        public int SecondarySize { get; set; }
        public string Reasoning { get; set; }
    }

    public class StackArrangement
    {
        public string PrimaryTeam { get; set; }
        public string SecondaryTeam { get; set; }
        public int PrimarySize { get; set; }
        public int SecondarySize { get; set; }
    }

    public class RequiredPlayer
    {
        public int PlayerId { get; set; }
        public string Team { get; set; }
        public string Position { get; set; }
        public int Count { get; set; } = 1;
        public bool IsExactCount { get; set; } = false;
    }
}