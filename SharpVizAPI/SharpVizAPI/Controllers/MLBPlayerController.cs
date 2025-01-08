using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SharpVizAPI.Data;
using SharpVizAPI.Models;
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
