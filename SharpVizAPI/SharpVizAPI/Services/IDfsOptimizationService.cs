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

        public DfsOptimizationService(NrfidbContext context, ILogger<DfsOptimizationService> logger)
        {
            _context = context;
            _logger = logger;
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

                var players = await playersQuery.ToListAsync();

                _logger.LogInformation($"Found {players.Count} players for draft group {request.DraftGroupId}" +
                    (request.UserWatchlist?.Any() == true ? " after applying watchlist filter" : "") +
                    (request.ExcludePlayers?.Any() == true ? " and exclusion filter" : ""));

                // Log excluded players if any
                if (request.ExcludePlayers?.Any() == true)
                {
                    var excludedNames = await _context.DKPlayerPools
                        .Where(p => request.ExcludePlayers.Contains(p.PlayerDkId))
                        .Select(p => p.FullName)
                        .ToListAsync();
                    _logger.LogInformation($"Excluded players: {string.Join(", ", excludedNames)}");
                }

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

                if (!players.Any())
                {
                    return new DfsOptimizationResponse
                    {
                        IsSuccessful = false,
                        Message = $"No players found after applying filters"
                    };
                }

                var positionMappings = new Dictionary<string, HashSet<string>>
        {
            { "G", new HashSet<string> { "PG", "SG" } },
            { "F", new HashSet<string> { "SF", "PF" } },
            { "UTIL", new HashSet<string> { "PG", "SG", "SF", "PF", "C" } },
            { "P", new HashSet<string> { "SP", "RP", "P" }  },
            { "OF", new HashSet<string> { "LF", "CF", "RF" }  }
        };

                if (request.OptimizeForDkppg)
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

            // Group players by their eligible positions
            var playersByPosition = new Dictionary<string, List<DKPlayerPool>>();
            foreach (var position in request.Positions)
            {
                var eligiblePlayers = players
                    .Where(p => IsPositionMatch(p.Position, position, positionMappings))
                    .OrderByDescending(p => p.DKppg)
                    .ToList();

                playersByPosition[position] = eligiblePlayers;
                _logger.LogInformation($"Found {eligiblePlayers.Count} eligible players for position {position}");
            }

            // Try each position as starting position
            foreach (var startingPosition in request.Positions)
            {
                _logger.LogInformation($"Trying combinations starting with position: {startingPosition}");

                var startingPlayers = playersByPosition[startingPosition]
                    .OrderByDescending(p => p.DKppg)
                    .Take(20)  // Try more starting players
                    .ToList();

                foreach (var startingPlayer in startingPlayers)
                {
                    _logger.LogDebug($"Trying lineup starting with {startingPlayer.FullName} ({startingPosition})");

                    var lineup = new List<OptimizedPlayer>();
                    var usedPlayerIds = new HashSet<int>();
                    var currentSalary = 0;

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
                    usedPlayerIds.Add(startingPlayer.PlayerDkId);
                    currentSalary += startingPlayer.Salary;

                    var remainingPositions = request.Positions
                        .Where(p => p != startingPosition)
                        .ToList();

                    var validLineup = await TryCompleteLineup(
                        lineup,
                        usedPlayerIds,
                        currentSalary,
                        remainingPositions,
                        playersByPosition,
                        request.SalaryCap);

                    if (validLineup != null)
                    {
                        decimal totalDkppg = validLineup.Sum(p => p.DKppg ?? 0);
                        _logger.LogInformation($"Found valid lineup - Total DKPPG: {totalDkppg:F1}, Salary: {validLineup.Sum(p => p.Salary)}");

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
                _logger.LogWarning("No valid lineup found");
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

            foreach (var position in request.Positions)
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
                    request.Positions.Count - optimizedLineup.Count);

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