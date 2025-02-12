using Microsoft.EntityFrameworkCore;
using SharpVizApi.Models;
using SharpVizAPI.Data;
using System.Text.RegularExpressions;

namespace SharpVizApi.Services
{
    public interface IDfsOptimizationService
    {
        Task<DfsOptimizationResponse> OptimizeLineup(DfsOptimizationRequest request);
    }


    public class DfsOptimizationService : IDfsOptimizationService
    {
        private readonly NrfidbContext _context;
        private readonly ILogger<DfsOptimizationService> _logger;
        private readonly IMLBStrategyService _strategyService;

        public DfsOptimizationService(
            NrfidbContext context,
            ILogger<DfsOptimizationService> logger,
            IMLBStrategyService strategyService)
        {
            _context = context;
            _logger = logger;
            _strategyService = strategyService;
        }
        private async Task<(int PrimaryStackSize, int SecondaryStackSize)?> GetStackRequirements(int draftGroupId)
        {
            // Get total games from DKPoolsMap
            var poolInfo = await _context.DKPoolsMaps
                .FirstOrDefaultAsync(p => p.DraftGroupId == draftGroupId);

            if (poolInfo?.TotalGames == null)
            {
                _logger.LogWarning($"No game count found for draft group {draftGroupId}");
                return null;
            }

            _logger.LogInformation($"Found {poolInfo.TotalGames} games for draft group {draftGroupId}");

            var strategy = _strategyService.GetOptimalStrategy(poolInfo.TotalGames.Value);
            _logger.LogInformation($"Optimal strategy for {poolInfo.TotalGames} games: {strategy.RecommendedStrategy}");
            _logger.LogInformation($"Strategy reasoning: {strategy.Reasoning}");

            var requirements = _strategyService.GetStackRequirements(strategy.RecommendedStrategy);
            _logger.LogInformation($"Stack requirements: {requirements[0].StackSize}-{requirements[1].StackSize}");

            return (requirements[0].StackSize, requirements[1].StackSize);
        }


        private async Task<DfsOptimizationResponse> OptimizeWithStrategy(
            List<DKPlayerPool> players,
            DfsOptimizationRequest request,
            Dictionary<string, HashSet<string>> positionMappings)
        {
            if (request.Strategy == null || request.Strategy.Count != 2)
            {
                _logger.LogWarning("Invalid strategy teams provided");
                return new DfsOptimizationResponse
                {
                    IsSuccessful = false,
                    Message = "Strategy requires exactly two teams"
                };
            }

            var stackRequirements = await GetStackRequirements(request.DraftGroupId);
            if (!stackRequirements.HasValue)
            {
                return new DfsOptimizationResponse
                {
                    IsSuccessful = false,
                    Message = "Could not determine optimal stacking strategy"
                };
            }

            _logger.LogInformation($"Using stack strategy: {stackRequirements.Value.PrimaryStackSize}-{stackRequirements.Value.SecondaryStackSize} " +
                                 $"with teams {request.Strategy[0]} and {request.Strategy[1]}");

            // Try both team combinations
            var attempt1 = await TryStackCombination(
                players, request, positionMappings,
                request.Strategy[0], request.Strategy[1],
                stackRequirements.Value.PrimaryStackSize,
                stackRequirements.Value.SecondaryStackSize);

            var attempt2 = await TryStackCombination(
                players, request, positionMappings,
                request.Strategy[1], request.Strategy[0],
                stackRequirements.Value.PrimaryStackSize,
                stackRequirements.Value.SecondaryStackSize);

            // Return the better result
            if (attempt1.IsSuccessful && (!attempt2.IsSuccessful ||
                attempt1.Players.Sum(p => p.DKppg ?? 0) > attempt2.Players.Sum(p => p.DKppg ?? 0)))
            {
                return attempt1;
            }

            if (attempt2.IsSuccessful)
            {
                return attempt2;
            }

            return new DfsOptimizationResponse
            {
                IsSuccessful = false,
                Message = "Could not create valid lineup with specified stack requirements"
            };
        }

        private async Task<DfsOptimizationResponse> TryStackCombination(
            List<DKPlayerPool> players,
            DfsOptimizationRequest request,
            Dictionary<string, HashSet<string>> positionMappings,
            string primaryTeam,
            string secondaryTeam,
            int primaryStackSize,
            int secondaryStackSize)
        {
            // Separate position players from pitchers
            var pitchers = players.Where(p => p.Position.Contains("SP") || p.Position.Contains("RP") || p.Position.Contains("P")).ToList();
            var positionPlayers = players.Where(p => !p.Position.Contains("SP") && !p.Position.Contains("RP") && !p.Position.Contains("P")).ToList();

            var primaryTeamPositionPlayers = positionPlayers.Where(p => p.Team == primaryTeam).ToList();
            var secondaryTeamPositionPlayers = positionPlayers.Where(p => p.Team == secondaryTeam).ToList();

            _logger.LogInformation($"Found {primaryTeamPositionPlayers.Count} position players from {primaryTeam} " +
                                 $"and {secondaryTeamPositionPlayers.Count} position players from {secondaryTeam}");

            // Separate must-start players into pitchers and position players
            var mustStartPitchers = new List<int>();
            var mustStartPositionPlayers = new List<int>();
            var mustStartPrimaryCount = 0;
            var mustStartSecondaryCount = 0;

            if (request.MustStartPlayers?.Any() == true)
            {
                foreach (var mustStartId in request.MustStartPlayers)
                {
                    var player = players.First(p => p.PlayerDkId == mustStartId);
                    _logger.LogInformation($"Must-start player {player.FullName} from team {player.Team} position {player.Position}");

                    if (player.Position.Contains("SP") || player.Position.Contains("RP") || player.Position.Contains("P"))
                    {
                        mustStartPitchers.Add(mustStartId);
                        continue;
                    }

                    mustStartPositionPlayers.Add(mustStartId);
                    if (player.Team == primaryTeam)
                        mustStartPrimaryCount++;
                    else if (player.Team == secondaryTeam)
                        mustStartSecondaryCount++;
                }

                _logger.LogInformation($"Must-start breakdown - Pitchers: {mustStartPitchers.Count}, " +
                                     $"Primary Position Players: {mustStartPrimaryCount}, " +
                                     $"Secondary Position Players: {mustStartSecondaryCount}");
            }

            // Adjust required stack sizes based on must-start position players
            var remainingPrimaryNeeded = Math.Max(0, primaryStackSize - mustStartPrimaryCount);
            var remainingSecondaryNeeded = Math.Max(0, secondaryStackSize - mustStartSecondaryCount);

            _logger.LogInformation($"After accounting for must-starts, need {remainingPrimaryNeeded} more from {primaryTeam} " +
                                 $"and {remainingSecondaryNeeded} more from {secondaryTeam}");

            if (primaryTeamPositionPlayers.Count < remainingPrimaryNeeded ||
                secondaryTeamPositionPlayers.Count < remainingSecondaryNeeded)
            {
                _logger.LogWarning($"Not enough position players available for {primaryStackSize}-{secondaryStackSize} stack after must-starts");
                return new DfsOptimizationResponse
                {
                    IsSuccessful = false,
                    Message = $"Not enough position players available for {primaryStackSize}-{secondaryStackSize} stack"
                };
            }

            // Start with must-start players (both pitchers and position players)
            var modifiedRequest = new DfsOptimizationRequest
            {
                DraftGroupId = request.DraftGroupId,
                Positions = request.Positions,
                SalaryCap = request.SalaryCap,
                OptimizeForDkppg = request.OptimizeForDkppg,
                UserWatchlist = new List<int>(),
                ExcludePlayers = request.ExcludePlayers,
                MustStartPlayers = new List<int>(mustStartPitchers), // Start with pitchers
                OppRankLimit = request.OppRankLimit
            };

            // Add must-start position players
            modifiedRequest.MustStartPlayers.AddRange(mustStartPositionPlayers);

            // Add remaining required players from primary team
            var additionalPrimaryPlayers = primaryTeamPositionPlayers
                .Where(p => !modifiedRequest.MustStartPlayers.Contains(p.PlayerDkId))
                .OrderByDescending(p => p.DKppg)
                .Take(remainingPrimaryNeeded);

            foreach (var player in additionalPrimaryPlayers)
            {
                modifiedRequest.MustStartPlayers.Add(player.PlayerDkId);
                _logger.LogInformation($"Adding primary stack player: {player.FullName} ({player.Position})");
            }

            // Add remaining required players from secondary team
            var additionalSecondaryPlayers = secondaryTeamPositionPlayers
                .Where(p => !modifiedRequest.MustStartPlayers.Contains(p.PlayerDkId))
                .OrderByDescending(p => p.DKppg)
                .Take(remainingSecondaryNeeded);

            foreach (var player in additionalSecondaryPlayers)
            {
                modifiedRequest.MustStartPlayers.Add(player.PlayerDkId);
                _logger.LogInformation($"Adding secondary stack player: {player.FullName} ({player.Position})");
            }

            _logger.LogInformation($"Final must-start count: {modifiedRequest.MustStartPlayers.Count} players");

            // Use existing optimization logic with the modified request
            if (request.OptimizeForDkppg)
            {
                return await OptimizeForDkppg(players, modifiedRequest, positionMappings);
            }
            else
            {
                return await OptimizeForSalary(players, modifiedRequest, positionMappings);
            }
        }
        public async Task<DfsOptimizationResponse> OptimizeLineup(DfsOptimizationRequest request)
        {
            try
            {
                // Get all players for the draft group
                var playersQuery = _context.DKPlayerPools
                    .Where(p => p.DraftGroupId == request.DraftGroupId && p.Status != "OUT");

                _logger.LogInformation("Automatically excluding players with OUT status");

                // Apply watchlist filter if provided
                if (request.UserWatchlist != null && request.UserWatchlist.Any())
                {
                    _logger.LogInformation($"Filtering by watchlist with {request.UserWatchlist.Count} players");
                    playersQuery = playersQuery.Where(p => request.UserWatchlist.Contains(p.PlayerDkId));
                }

                // Apply exclusion filter if provided
                if (request.ExcludePlayers != null && request.ExcludePlayers.Any())
                {
                    _logger.LogInformation($"Excluding {request.ExcludePlayers.Count} players from consideration");
                    playersQuery = playersQuery.Where(p => !request.ExcludePlayers.Contains(p.PlayerDkId));
                }

                if (request.MustStartPlayers != null && request.MustStartPlayers.Any())
                {
                    _logger.LogInformation($"Validating {request.MustStartPlayers.Count} must-start players");
                    _logger.LogInformation($"Must start player IDs: {string.Join(", ", request.MustStartPlayers)}");

                    var mustStartQuery = _context.DKPlayerPools
                        .Where(p => request.MustStartPlayers.Contains(p.PlayerDkId) &&
                                    p.DraftGroupId == request.DraftGroupId);

                    // Log the generated SQL query
                    _logger.LogInformation($"Must start query SQL: {mustStartQuery.ToQueryString()}");

                    var mustStartPlayers = await mustStartQuery.ToListAsync();

                    _logger.LogInformation($"Found {mustStartPlayers.Count} out of {request.MustStartPlayers.Count} must-start players");

                    // Log details of found players
                    foreach (var player in mustStartPlayers)
                    {
                        _logger.LogInformation($"Found must-start player: ID={player.PlayerDkId}, Name={player.FullName}, DraftGroupId={player.DraftGroupId}");
                    }

                    // Log details of missing players
                    var foundPlayerIds = mustStartPlayers.Select(p => p.PlayerDkId).ToHashSet();
                    var missingPlayerIds = request.MustStartPlayers.Where(id => !foundPlayerIds.Contains(id));
                    foreach (var missingId in missingPlayerIds)
                    {
                        _logger.LogWarning($"Could not find must-start player with ID: {missingId}");

                        // Additional debug query to check if player exists at all
                        var playerCheck = await _context.DKPlayerPools
                            .Where(p => p.PlayerDkId == missingId)
                            .Select(p => new { p.PlayerDkId, p.DraftGroupId, p.FullName })
                            .ToListAsync();

                        if (playerCheck.Any())
                        {
                            _logger.LogWarning($"Player {missingId} exists in other draft groups:");
                            foreach (var p in playerCheck)
                            {
                                _logger.LogWarning($"- DraftGroup: {p.DraftGroupId}, Name: {p.FullName}");
                            }
                        }
                        else
                        {
                            _logger.LogWarning($"Player {missingId} not found in any draft group");
                        }
                    }

                    if (mustStartPlayers.Count != request.MustStartPlayers.Count)
                    {
                        return new DfsOptimizationResponse
                        {
                            IsSuccessful = false,
                            Message = $"One or more must-start players not found in player pool. Missing players: {string.Join(", ", missingPlayerIds)}"
                        };
                    }

                    // Validate must-start players don't exceed salary cap
                    int mustStartSalary = mustStartPlayers.Sum(p => p.Salary);
                    if (mustStartSalary > request.SalaryCap)
                    {
                        return new DfsOptimizationResponse
                        {
                            IsSuccessful = false,
                            Message = "Must-start players total salary exceeds salary cap"
                        };
                    }
                }

                var players = await playersQuery.ToListAsync();

                _logger.LogInformation($"Found {players.Count} players for draft group {request.DraftGroupId}");

                if (!players.Any())
                {
                    return new DfsOptimizationResponse
                    {
                        IsSuccessful = false,
                        Message = GetNoPlayersFoundMessage(request)
                    };
                }

                // Apply OppRank filtering if specified
                if (request.OppRankLimit.HasValue)
                {
                    _logger.LogInformation($"Applying OppRank filter with limit: {request.OppRankLimit.Value}");
                    players = FilterByOppRank(players, request.OppRankLimit.Value);
                    _logger.LogInformation($"After OppRank filtering: {players.Count} players remaining");
                }

                var positionMappings = new Dictionary<string, HashSet<string>>
            {
                { "G", new HashSet<string> { "PG", "SG" } },
                { "F", new HashSet<string> { "SF", "PF" } },
                { "UTIL", new HashSet<string> { "PG", "SG", "SF", "PF", "C" } },
                { "P", new HashSet<string> { "SP", "RP", "P" }  },
                { "OF", new HashSet<string> { "LF", "CF", "RF" }  }
            };

                if (request.Strategy?.Any() == true)
                {
                    _logger.LogInformation("Starting strategy-based optimization");
                    return await OptimizeWithStrategy(players, request, positionMappings);
                }
                else if (request.OptimizeForDkppg)
                {
                    _logger.LogInformation("Starting DKPPG optimization");
                    return await OptimizeForDkppg(players, request, positionMappings);
                }
                else
                {
                    _logger.LogInformation("Starting salary optimization");
                    return await OptimizeForSalary(players, request, positionMappings);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error optimizing lineup");
                return new DfsOptimizationResponse
                {
                    IsSuccessful = false,
                    Message = "Error occurred while optimizing lineup"
                };
            }
        }


        private string GetNoPlayersFoundMessage(DfsOptimizationRequest request)
        {
            var messageComponents = new List<string>();

            if (request.UserWatchlist?.Any() == true)
            {
                messageComponents.Add("watchlist");
            }

            if (request.ExcludePlayers?.Any() == true)
            {
                messageComponents.Add("exclusion list");
            }

            if (!messageComponents.Any())
            {
                return $"No players found for draft group {request.DraftGroupId}";
            }

            return $"No players found matching {string.Join(" and ", messageComponents)} for draft group {request.DraftGroupId}";
        }
        private List<DKPlayerPool> FilterByOppRank(List<DKPlayerPool> players, int oppRankLimit)
        {
            _logger.LogInformation($"FilterByOppRank called with limit: {oppRankLimit}");

            // If oppRankLimit is 0, return all players (no filtering)
            if (oppRankLimit == 0)
            {
                _logger.LogInformation("OppRank limit is 0, returning all players without filtering");
                return players;
            }

            // Log initial state
            _logger.LogInformation($"Starting OppRank filtering with {players.Count} players");
            _logger.LogInformation($"Will include players with ranks {31 - oppRankLimit} through 30");

            var filteredPlayers = players.Where(p => {
                if (string.IsNullOrEmpty(p.OppRank))
                {
                    _logger.LogDebug($"Player {p.FullName} has no OppRank");
                    return false;
                }

                // Extract number from strings like "28th"
                var match = Regex.Match(p.OppRank, @"\d+");
                if (!match.Success)
                {
                    _logger.LogDebug($"Player {p.FullName} has invalid OppRank format: {p.OppRank}");
                    return false;
                }

                int rank = int.Parse(match.Value);
                bool isIncluded = rank >= (31 - oppRankLimit);

                _logger.LogDebug($"Player {p.FullName}: Rank={rank}, isIncluded={isIncluded}");

                return isIncluded;
            }).ToList();

            _logger.LogInformation($"After OppRank filtering: {filteredPlayers.Count} players remain");

            // Log sample of filtered players
            _logger.LogInformation("Sample of filtered players:");
            foreach (var player in filteredPlayers.Take(5))
            {
                _logger.LogInformation($"Filtered Player: {player.FullName}, OppRank: {player.OppRank}");
            }

            return filteredPlayers;
        }

        private async Task<DfsOptimizationResponse> OptimizeForDkppg(
            List<DKPlayerPool> players,
            DfsOptimizationRequest request,
            Dictionary<string, HashSet<string>> positionMappings)
        {
            var bestLineup = new List<OptimizedPlayer>();
            decimal bestTotalDkppg = 0;

            _logger.LogInformation($"Starting DKPPG optimization with {players.Count} players");

            // Handle must-start players first
            var mustStartPlayers = new List<OptimizedPlayer>();
            var remainingPositions = new List<string>(request.Positions);
            var usedPlayerIds = new HashSet<int>();
            var currentSalary = 0;

            if (request.MustStartPlayers?.Any() == true)
            {
                foreach (var mustStartId in request.MustStartPlayers)
                {
                    var player = players.First(p => p.PlayerDkId == mustStartId);

                    // Find the best position for this must-start player
                    string bestPosition = FindBestPositionForPlayer(player, remainingPositions, positionMappings);
                    if (bestPosition == null)
                    {
                        return new DfsOptimizationResponse
                        {
                            IsSuccessful = false,
                            Message = $"Cannot find valid position for must-start player {player.FullName}"
                        };
                    }

                    var optimizedPlayer = new OptimizedPlayer
                    {
                        FullName = player.FullName,
                        PlayerDkId = player.PlayerDkId,
                        Position = player.Position,
                        AssignedPosition = bestPosition,
                        Salary = player.Salary,
                        Team = player.Team,
                        DKppg = player.DKppg
                    };

                    mustStartPlayers.Add(optimizedPlayer);
                    usedPlayerIds.Add(player.PlayerDkId);
                    currentSalary += player.Salary;
                    remainingPositions.Remove(bestPosition);
                }
            }

            // Group remaining players by their eligible positions
            var playersByPosition = new Dictionary<string, List<DKPlayerPool>>();
            foreach (var position in remainingPositions)
            {
                var eligiblePlayers = players
                    .Where(p => !usedPlayerIds.Contains(p.PlayerDkId) &&
                               IsPositionMatch(p.Position, position, positionMappings))
                    .OrderByDescending(p => p.DKppg)
                    .ToList();

                playersByPosition[position] = eligiblePlayers;
                _logger.LogInformation($"Found {eligiblePlayers.Count} eligible players for position {position}");
            }

            // Try each position as starting position for remaining slots
            foreach (var startingPosition in remainingPositions)
            {
                _logger.LogInformation($"Trying combinations starting with position: {startingPosition}");

                var startingPlayers = playersByPosition[startingPosition]
                    .OrderByDescending(p => p.DKppg)
                    .Take(20)
                    .ToList();

                foreach (var startingPlayer in startingPlayers)
                {
                    var lineup = new List<OptimizedPlayer>(mustStartPlayers);
                    var currentUsedPlayerIds = new HashSet<int>(usedPlayerIds);
                    var currentTotalSalary = currentSalary;

                    // Add starting player
                    var startingOptimizedPlayer = new OptimizedPlayer
                    {
                        FullName = startingPlayer.FullName,
                        PlayerDkId = startingPlayer.PlayerDkId,
                        Position = startingPlayer.Position,
                        AssignedPosition = startingPosition,
                        Salary = startingPlayer.Salary,
                        Team = startingPlayer.Team,
                        DKppg = startingPlayer.DKppg
                    };

                    lineup.Add(startingOptimizedPlayer);
                    currentUsedPlayerIds.Add(startingPlayer.PlayerDkId);
                    currentTotalSalary += startingPlayer.Salary;

                    var nextPositions = remainingPositions
                        .Where(p => p != startingPosition)
                        .ToList();

                    var validLineup = await TryCompleteLineup(
                        lineup,
                        currentUsedPlayerIds,
                        currentTotalSalary,
                        nextPositions,
                        playersByPosition,
                        request.SalaryCap);

                    if (validLineup != null)
                    {
                        decimal totalDkppg = validLineup.Sum(p => p.DKppg ?? 0);
                        if (totalDkppg > bestTotalDkppg)
                        {
                            bestTotalDkppg = totalDkppg;
                            bestLineup = validLineup;
                            _logger.LogInformation($"New best lineup found! DKPPG: {totalDkppg:F1}");
                        }
                    }
                }
            }

            if (!bestLineup.Any())
            {
                return new DfsOptimizationResponse
                {
                    IsSuccessful = false,
                    Message = "Could not find a valid lineup within constraints"
                };
            }

            return new DfsOptimizationResponse
            {
                IsSuccessful = true,
                Players = bestLineup,
                TotalSalary = bestLineup.Sum(p => p.Salary),
                Message = $"Successfully optimized lineup for DKPPG (Total DKPPG: {bestTotalDkppg:F1})"
            };
        }

        private string FindBestPositionForPlayer(
    DKPlayerPool player,
    List<string> availablePositions,
    Dictionary<string, HashSet<string>> positionMappings)
        {
            foreach (var position in availablePositions)
            {
                if (IsPositionMatch(player.Position, position, positionMappings))
                {
                    return position;
                }
            }
            return null;
        }
        private async Task<List<OptimizedPlayer>> TryCompleteLineup(
    List<OptimizedPlayer> currentLineup,
    HashSet<int> usedPlayerIds,
    int currentSalary,
    List<string> remainingPositions,
    Dictionary<string, List<DKPlayerPool>> playersByPosition,
    int salaryCap)
        {
            if (!remainingPositions.Any())
            {
                return currentLineup;
            }

            var position = remainingPositions[0];
            var nextRemainingPositions = remainingPositions.Skip(1).ToList();

            var eligiblePlayers = playersByPosition[position]
                .Where(p => !usedPlayerIds.Contains(p.PlayerDkId) &&
                            currentSalary + p.Salary <= salaryCap)
                .OrderByDescending(p => p.DKppg)
                .Take(15)  // Consider more players for each position
                .ToList();

            foreach (var player in eligiblePlayers)
            {
                var newLineup = new List<OptimizedPlayer>(currentLineup)
        {
            new OptimizedPlayer
            {
                FullName = player.FullName,
                PlayerDkId = player.PlayerDkId,
                Position = player.Position,
                AssignedPosition = position,
                Salary = player.Salary,
                Team = player.Team,
                DKppg = player.DKppg
            }
        };

                var newUsedPlayerIds = new HashSet<int>(usedPlayerIds) { player.PlayerDkId };
                var newSalary = currentSalary + player.Salary;

                var completedLineup = await TryCompleteLineup(
                    newLineup,
                    newUsedPlayerIds,
                    newSalary,
                    nextRemainingPositions,
                    playersByPosition,
                    salaryCap);

                if (completedLineup != null)
                {
                    return completedLineup;
                }
            }

            return null;
        }
        private async Task<DfsOptimizationResponse> OptimizeForSalary(
              List<DKPlayerPool> players,
              DfsOptimizationRequest request,
              Dictionary<string, HashSet<string>> positionMappings)
        {
            var optimizedLineup = new List<OptimizedPlayer>();
            var usedPlayerIds = new HashSet<int>();
            var remainingSalary = request.SalaryCap;
            var remainingPositions = new List<string>(request.Positions);

            // Handle must-start players first
            if (request.MustStartPlayers?.Any() == true)
            {
                foreach (var mustStartId in request.MustStartPlayers)
                {
                    var player = players.First(p => p.PlayerDkId == mustStartId);

                    // Find the best position for this must-start player
                    string bestPosition = FindBestPositionForPlayer(player, remainingPositions, positionMappings);
                    if (bestPosition == null)
                    {
                        return new DfsOptimizationResponse
                        {
                            IsSuccessful = false,
                            Message = $"Cannot find valid position for must-start player {player.FullName}"
                        };
                    }

                    var optimizedPlayer = new OptimizedPlayer
                    {
                        FullName = player.FullName,
                        PlayerDkId = player.PlayerDkId,
                        Position = player.Position,
                        AssignedPosition = bestPosition,
                        Salary = player.Salary,
                        Team = player.Team,
                        DKppg = player.DKppg
                    };

                    optimizedLineup.Add(optimizedPlayer);
                    usedPlayerIds.Add(player.PlayerDkId);
                    remainingSalary -= player.Salary;
                    remainingPositions.Remove(bestPosition);
                }
            }

            // Fill remaining positions
            foreach (var position in remainingPositions)
            {
                var eligiblePlayers = players
                    .Where(p => !usedPlayerIds.Contains(p.PlayerDkId) &&
                               IsPositionMatch(p.Position, position, positionMappings))
                    .OrderByDescending(p => p.DKppg)
                    .ToList();

                if (!eligiblePlayers.Any())
                {
                    return new DfsOptimizationResponse
                    {
                        IsSuccessful = false,
                        Message = $"Could not find eligible player for position {position}"
                    };
                }

                var selectedPlayer = FindBestPlayerForSalary(eligiblePlayers, remainingSalary,
                    remainingPositions.Count - optimizedLineup.Count + 1);

                if (selectedPlayer == null)
                {
                    return new DfsOptimizationResponse
                    {
                        IsSuccessful = false,
                        Message = $"Could not find suitable player for position {position} within salary constraints"
                    };
                }

                optimizedLineup.Add(new OptimizedPlayer
                {
                    FullName = selectedPlayer.FullName,
                    PlayerDkId = selectedPlayer.PlayerDkId,
                    Position = selectedPlayer.Position,
                    AssignedPosition = position,
                    Salary = selectedPlayer.Salary,
                    Team = selectedPlayer.Team,
                    DKppg = selectedPlayer.DKppg
                });

                usedPlayerIds.Add(selectedPlayer.PlayerDkId);
                remainingSalary -= selectedPlayer.Salary;
            }

            decimal totalDkppg = optimizedLineup.Sum(p => p.DKppg ?? 0);
            return new DfsOptimizationResponse
            {
                IsSuccessful = true,
                Players = optimizedLineup,
                TotalSalary = request.SalaryCap - remainingSalary,
                Message = $"Successfully optimized lineup (Total DKPPG: {totalDkppg:F1})"
            };
        }

        private bool IsPositionMatch(string playerPosition, string requiredPosition,
                    Dictionary<string, HashSet<string>> positionMappings)
        {
            // Split player position on '/' to handle multi-position players
            var playerPositions = playerPosition.Split('/', StringSplitOptions.RemoveEmptyEntries)
                                              .Select(p => p.Trim())
                                              .ToHashSet();

            // Direct match - check if any of the player's positions match the required position
            if (playerPositions.Contains(requiredPosition))
                return true;

            // Check flexible positions (G, F, UTIL)
            if (positionMappings.ContainsKey(requiredPosition))
            {
                // Check if any of the player's positions match any of the mapped positions
                return playerPositions.Any(pos => positionMappings[requiredPosition].Contains(pos));
            }

            return false;
        }

        private DKPlayerPool FindBestPlayerForSalary(List<DKPlayerPool> players, int remainingSalary, int remainingPlayers)
        {
            var targetSalary = remainingSalary / remainingPlayers;

            return players
                .Where(p => p.Salary <= remainingSalary)
                .OrderBy(p => Math.Abs(p.Salary - targetSalary))
                .ThenByDescending(p => p.DKppg)
                .FirstOrDefault();
        }
    }
}