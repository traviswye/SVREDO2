using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using SharpVizAPI.Data;
using SharpVizAPI.Models;
using SharpVizApi.Models;

namespace SharpVizAPI.Services
{
    public class PlayerIDMappingService
    {
        private readonly NrfidbContext _context;
        private readonly HttpClient _httpClient;
        private readonly ILogger<PlayerIDMappingService> _logger;

        // Dictionary to handle specific team abbreviation differences between systems
        private static readonly Dictionary<string, string> TeamAbbreviationMap = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase)
        {
            { "SD", "SDP" },
            { "SF", "SFG" },
            { "KC", "KCR" },
            { "TB", "TBR" },
            { "WAS", "WSN" },
            { "CWS", "CHW" }
            // Add any other mappings as you discover them
        };

        public PlayerIDMappingService(NrfidbContext context, HttpClient httpClient, ILogger<PlayerIDMappingService> logger)
        {
            _context = context;
            _httpClient = httpClient;
            _logger = logger;
        }

        public async Task<string> GetBbrefIdFromDkIdAsync(int playerDkId)
        {
            // Check if mapping exists
            var mapping = await _context.PlayerIDMappings
                .Where(m => m.PlayerDkId == playerDkId)
                .OrderByDescending(m => m.LastUpdated)
                .FirstOrDefaultAsync();

            return mapping?.BbrefId;
        }

        public async Task<int?> GetDkIdFromBbrefIdAsync(string bbrefId)
        {
            // Check if mapping exists
            var mapping = await _context.PlayerIDMappings
                .Where(m => m.BbrefId == bbrefId)
                .OrderByDescending(m => m.LastUpdated)
                .FirstOrDefaultAsync();

            return mapping?.PlayerDkId;
        }

        public async Task ProcessNewPlayersInDkPoolAsync(List<DKPlayerPool> playerPool)
        {
            try
            {
                // Extract unique players not already in our mapping
                var existingMappingIds = await _context.PlayerIDMappings
                    .Select(m => m.PlayerDkId)
                    .ToListAsync();

                var existingMappings = new HashSet<int>(existingMappingIds);

                var newPlayers = playerPool
                    .Where(p => !existingMappings.Contains(p.PlayerDkId))
                    .ToList();

                if (!newPlayers.Any())
                {
                    _logger.LogInformation("No new players to process for ID mapping");
                    return;
                }

                _logger.LogInformation($"Processing {newPlayers.Count} new players for ID mapping");

                // Create individual lookups since batch process is failing
                foreach (var player in newPlayers)
                {
                    try
                    {
                        await ProcessSinglePlayerAsync(player);
                    }
                    catch (Exception ex)
                    {
                        _logger.LogError(ex, $"Error processing player {player.FullName} ({player.PlayerDkId})");
                        // Continue with the next player
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error in ProcessNewPlayersInDkPoolAsync");
            }
        }

        private async Task ProcessSinglePlayerAsync(DKPlayerPool player)
        {
            // Normalize the team abbreviation
            string normalizedTeam = NormalizeTeamAbbreviation(player.Team);

            // Search for the player in MLBplayers
            var mlbPlayer = await FindPlayerInDatabase(player.FullName, normalizedTeam);

            if (mlbPlayer != null)
            {
                // Create a new mapping
                var newMapping = new PlayerIDMapping
                {
                    PlayerDkId = player.PlayerDkId,
                    BbrefId = mlbPlayer.bbrefId,
                    FullName = player.FullName,
                    Team = player.Team,
                    Position = player.Position,
                    Year = DateTime.Now.Year,
                    DateAdded = DateTime.Now,
                    LastUpdated = DateTime.Now
                };

                await _context.PlayerIDMappings.AddAsync(newMapping);
                await _context.SaveChangesAsync();

                _logger.LogInformation($"Created mapping: {player.FullName} ({player.PlayerDkId}) -> {mlbPlayer.bbrefId}");
            }
            else
            {
                _logger.LogWarning($"Could not find bbrefId for player: {player.FullName} ({player.Team})");
            }
        }

        private string NormalizeTeamAbbreviation(string teamAbbr)
        {
            if (string.IsNullOrEmpty(teamAbbr))
                return teamAbbr;

            // Try to map the team abbreviation
            if (TeamAbbreviationMap.TryGetValue(teamAbbr, out string normalizedAbbr))
            {
                return normalizedAbbr;
            }

            return teamAbbr; // Return original if no mapping found
        }

        private async Task<MLBplayer> FindPlayerInDatabase(string fullName, string team)
        {
            // Try exact match on name and team
            var player = await _context.MLBplayers
                .FirstOrDefaultAsync(p =>
                    p.FullName.ToLower() == fullName.ToLower() &&
                    p.CurrentTeam.ToLower() == team.ToLower());

            // If not found, try exact match on name only
            if (player == null)
            {
                player = await _context.MLBplayers
                    .FirstOrDefaultAsync(p =>
                        p.FullName.ToLower() == fullName.ToLower());
            }

            // If still not found, try partial name matching
            if (player == null)
            {
                var nameParts = fullName.ToLower().Split(' ');
                if (nameParts.Length >= 2)
                {
                    var firstName = nameParts[0];
                    var lastName = nameParts[nameParts.Length - 1];

                    // Search for players with similar names
                    var potentialMatches = await _context.MLBplayers
                        .Where(p =>
                            p.FullName.ToLower().Contains(firstName) &&
                            p.FullName.ToLower().Contains(lastName))
                        .ToListAsync();

                    if (potentialMatches.Count == 1)
                    {
                        player = potentialMatches.First();
                    }
                    else if (potentialMatches.Count > 1)
                    {
                        // Try to find the best match with team
                        player = potentialMatches.FirstOrDefault(p =>
                            p.CurrentTeam.ToLower() == team.ToLower());

                        // If no match with team, just take the first one
                        if (player == null && potentialMatches.Any())
                        {
                            player = potentialMatches.First();
                        }
                    }
                }
            }

            return player;
        }
    }

    public class PlayerLookupRequest
    {
        public int PlayerDkId { get; set; }
        public string FullName { get; set; }
        public string Team { get; set; }
        public string Position { get; set; }
    }

    public class PlayerMappingResult
    {
        public int PlayerDkId { get; set; }
        public string FullName { get; set; }
        public string Team { get; set; }
        public string Position { get; set; }
        public string BbrefId { get; set; }
        public bool Found { get; set; }
    }
}