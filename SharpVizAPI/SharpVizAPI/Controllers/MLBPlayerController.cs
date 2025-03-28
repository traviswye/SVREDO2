﻿using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SharpVizAPI.Data;
using SharpVizAPI.Models;
using SharpVizAPI.Services;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SharpVizAPI.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class MLBPlayerController : ControllerBase
    {
        private readonly NrfidbContext _context;

        public MLBPlayerController(NrfidbContext context)
        {
            _context = context;
        }

        [HttpGet("{bbrefId}")]
        public async Task<ActionResult<MLBplayer>> GetMLBplayer(string bbrefId)
        {
            var player = await _context.MLBplayers.FindAsync(bbrefId);
            if (player == null)
            {
                return NotFound();
            }
            return player;
        }


        [HttpGet("search")]
        public async Task<ActionResult<IEnumerable<MLBplayer>>> GetByFullNameAndTeam(string fullName, string team)
        {
            var normalizedFullName = fullName.Normalize(NormalizationForm.FormD);  // Decompose accented characters

            // Step 1: Search by full name (ignoring team)
            var playersWithFullName = await _context.MLBplayers
                .Where(p => EF.Functions.Collate(p.FullName, "Latin1_General_CI_AI") == EF.Functions.Collate(normalizedFullName, "Latin1_General_CI_AI"))
                .ToListAsync();

            // Step 2: If only one player is found, return that player
            if (playersWithFullName.Count == 1)
            {
                return playersWithFullName;
            }

            // Step 3: If multiple players are found, filter by team
            var filteredByTeam = playersWithFullName
                .Where(p => p.CurrentTeam == team)
                .ToList();

            // Step 4: If filtering by team results in exactly one player, return that result
            if (filteredByTeam.Count == 1)
            {
                return filteredByTeam;
            }

            // Step 5: If no match is found with team filtering, return the full list or empty result
            if (filteredByTeam.Count == 0)
            {
                // If team filtering returns no results, return the initial list of players with just the full name
                return playersWithFullName;
            }

            // Return the filtered list by team (if there are multiple entries for the same player with the same name in different teams)
            return filteredByTeam;
        }
        [HttpPost("batchsearch")]
        public async Task<ActionResult<List<PlayerMappingResult>>> BatchSearch([FromBody] List<PlayerLookupRequest> requests)
        {
            if (requests == null || !requests.Any())
            {
                return BadRequest("No players provided for lookup");
            }

            var results = new List<PlayerMappingResult>();

            foreach (var request in requests)
            {
                // Normalize team name
                string normalizedTeam = TeamNameNormalizer.NormalizeTeamName(request.Team);

                // Normalize the full name for comparison
                var normalizedFullName = request.FullName.Normalize(NormalizationForm.FormD);

                // Search for player using collation instead of Like
                var player = await _context.MLBplayers
                    .Where(p =>
                        EF.Functions.Collate(p.FullName, "Latin1_General_CI_AI") ==
                        EF.Functions.Collate(normalizedFullName, "Latin1_General_CI_AI") &&
                        p.CurrentTeam.ToLower() == normalizedTeam.ToLower())
                    .FirstOrDefaultAsync();

                // Try without team if not found
                if (player == null)
                {
                    player = await _context.MLBplayers
                        .Where(p =>
                            EF.Functions.Collate(p.FullName, "Latin1_General_CI_AI") ==
                            EF.Functions.Collate(normalizedFullName, "Latin1_General_CI_AI"))
                        .FirstOrDefaultAsync();
                }

                // Try with fuzzy name matching if still not found
                if (player == null)
                {
                    // Split the name to search for first and last name parts
                    var nameParts = request.FullName.ToLower().Split(' ');
                    if (nameParts.Length >= 2)
                    {
                        var firstName = nameParts[0];
                        var lastName = nameParts[nameParts.Length - 1];

                        // Use CONTAINS which translates to DB better than LIKE for this case
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
                                p.CurrentTeam.ToLower() == normalizedTeam.ToLower());

                            // If still no match with team, just take the first one
                            if (player == null && potentialMatches.Any())
                            {
                                player = potentialMatches.First();
                            }
                        }
                    }
                }

                var mappingResult = new PlayerMappingResult
                {
                    PlayerDkId = request.PlayerDkId,
                    FullName = request.FullName,
                    Team = request.Team,
                    Position = request.Position,
                    BbrefId = player?.bbrefId,
                    Found = player != null
                };

                results.Add(mappingResult);

                // Add mapping to database if player was found
                if (player != null)
                {
                    // Check if mapping already exists
                    var existingMapping = await _context.PlayerIDMappings
                        .FirstOrDefaultAsync(m => m.PlayerDkId == request.PlayerDkId);

                    if (existingMapping != null)
                    {
                        // Update existing mapping
                        existingMapping.BbrefId = player.bbrefId;
                        existingMapping.FullName = request.FullName;
                        existingMapping.Team = request.Team;
                        existingMapping.Position = request.Position;
                        existingMapping.LastUpdated = DateTime.Now;
                    }
                    else
                    {
                        // Create new mapping
                        var newMapping = new PlayerIDMapping
                        {
                            PlayerDkId = request.PlayerDkId,
                            BbrefId = player.bbrefId,
                            FullName = request.FullName,
                            Team = request.Team,
                            Position = request.Position,
                            Year = DateTime.Now.Year,
                            DateAdded = DateTime.Now,
                            LastUpdated = DateTime.Now
                        };

                        await _context.PlayerIDMappings.AddAsync(newMapping);
                    }
                }
            }

            // Save all changes at once
            await _context.SaveChangesAsync();

            return Ok(results);
        }

        public class PlayerLookupRequest
        {
            public int PlayerDkId { get; set; }
            public string FullName { get; set; }
            public string Team { get; set; }
            public string Position { get; set; }
        }

        [HttpGet("searchAbr")]
        public async Task<ActionResult<MLBplayer>> GetByInitialAndLastName(string firstInitial, string lastName, string team)
        {
            // Step 1: Filter by first initial and last name
            var players = await _context.MLBplayers
                .Where(p => p.FullName.Contains(" " + lastName) && // Match last name anywhere
                            p.FullName.StartsWith(firstInitial))   // Match first initial
                .ToListAsync();

            // Step 2: If only one player matches, return it
            if (players.Count == 1)
            {
                return Ok(players.First());
            }

            // Step 3: If multiple players match, filter by team
            var filteredByTeam = players.Where(p => p.CurrentTeam == team).ToList();

            // Step 4: If only one player matches after team filtering, return it
            if (filteredByTeam.Count == 1)
            {
                return Ok(filteredByTeam.First());
            }

            // Step 5: Handle ambiguous results
            if (filteredByTeam.Count > 1)
            {
                return BadRequest("Multiple players found with the same first initial and last name in the specified team.");
            }

            // Step 6: If no players match after team filtering, return not found
            return NotFound("Player not found with the specified first initial, last name, and team.");
        }
        [HttpPost("batch")]
        public async Task<ActionResult<Dictionary<string, string>>> GetPlayerFullNames([FromBody] List<string> bbrefIds)
        {
            if (bbrefIds == null || !bbrefIds.Any())
            {
                return BadRequest("No player IDs provided.");
            }

            // Fetch players whose bbrefIds are in the provided list
            var players = await _context.MLBplayers
                .Where(p => bbrefIds.Contains(p.bbrefId))
                .Select(p => new { p.bbrefId, p.FullName })
                .ToListAsync();

            // Convert the result into a dictionary of bbrefId to FullName
            var result = players.ToDictionary(p => p.bbrefId, p => p.FullName);

            return Ok(result);
        }
        // New endpoint to get all rows
        [HttpGet("all")]
        public async Task<IActionResult> GetAllPlayers()
        {
            var players = await _context.MLBplayers.ToListAsync();
            return Ok(players);
        }

        [HttpPut("{bbrefId}")]
        public async Task<IActionResult> PutMLBplayer(string bbrefId, MLBplayer player)
        {
            if (bbrefId != player.bbrefId)
            {
                return BadRequest();
            }

            _context.Entry(player).State = EntityState.Modified;

            try
            {
                await _context.SaveChangesAsync();
            }
            catch (DbUpdateConcurrencyException)
            {
                if (!MLBplayerExists(bbrefId))
                {
                    return NotFound();
                }
                else
                {
                    throw;
                }
            }

            return NoContent();
        }

        [HttpDelete("{bbrefId}")]
        public async Task<IActionResult> DeleteMLBplayer(string bbrefId)
        {
            var player = await _context.MLBplayers.FindAsync(bbrefId);
            if (player == null)
            {
                return NotFound();
            }

            _context.MLBplayers.Remove(player);
            await _context.SaveChangesAsync();

            return NoContent();
        }

        private bool MLBplayerExists(string bbrefId)
        {
            return _context.MLBplayers.Any(e => e.bbrefId == bbrefId);
        }

        [HttpPost]
        public async Task<ActionResult<MLBplayer>> PostMLBplayer(MLBplayer player)
        {
            // Add the new player to the context
            _context.MLBplayers.Add(player);

            try
            {
                // Save changes to the database
                await _context.SaveChangesAsync();
            }
            catch (DbUpdateException)
            {
                // If a player with the same bbrefId already exists, return a conflict response
                if (MLBplayerExists(player.bbrefId))
                {
                    return Conflict();
                }
                else
                {
                    throw;
                }
            }

            // Return a 201 Created response with the new player data
            return CreatedAtAction(nameof(GetMLBplayer), new { bbrefId = player.bbrefId }, player);
        }
    }


}
