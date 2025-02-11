using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SharpVizApi.Models;
using SharpVizAPI.Data;

namespace SharpVizApi.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class DKPlayerPoolsController : ControllerBase
    {
        private readonly NrfidbContext _context;
        private readonly ILogger<DKPlayerPoolsController> _logger;

        public DKPlayerPoolsController(NrfidbContext context, ILogger<DKPlayerPoolsController> logger)
        {
            _context = context;
            _logger = logger;
        }

        // GET: api/DKPlayerPools/draftgroup/{draftGroupId}
        [HttpGet("draftgroup/{draftGroupId}")]
        public async Task<ActionResult<IEnumerable<DKPlayerPool>>> GetPlayersByDraftGroup(int draftGroupId)
        {
            var players = await _context.DKPlayerPools
                .Where(p => p.DraftGroupId == draftGroupId)
                .ToListAsync();

            if (!players.Any())
            {
                return NotFound($"No players found for draft group {draftGroupId}");
            }

            return Ok(players);
        }

        // POST: api/DKPlayerPools/batch
        [HttpPost("batch")]
        public async Task<IActionResult> PostPlayerBatch([FromBody] DKPlayerPoolBatchRequest request)
        {
            if (!ModelState.IsValid)
            {
                return BadRequest(ModelState);
            }

            try
            {
                // Delete existing players for this draft group
                var existingPlayers = await _context.DKPlayerPools
                    .Where(p => p.DraftGroupId == request.DraftGroupId)
                    .ToListAsync();

                if (existingPlayers.Any())
                {
                    _context.DKPlayerPools.RemoveRange(existingPlayers);
                }

                // Add new players
                var playersToAdd = request.Players.Select(p => new DKPlayerPool
                {
                    DraftGroupId = request.DraftGroupId,
                    PlayerDkId = p.PlayerDkId,
                    FullName = p.FullName,
                    Position = p.Position,
                    Salary = p.Salary,
                    GameId = p.GameId,
                    Game = p.Game,
                    GameStart = p.GameStart,
                    Team = p.Team,
                    DKppg = p.DKppg,
                    OppRank = p.OppRank,
                    DateAdded = DateTime.UtcNow
                }).ToList();

                await _context.DKPlayerPools.AddRangeAsync(playersToAdd);
                await _context.SaveChangesAsync();

                _logger.LogInformation($"Successfully updated {playersToAdd.Count} players for draft group {request.DraftGroupId}");

                return Ok(new
                {
                    message = $"Successfully added {playersToAdd.Count} players to draft group {request.DraftGroupId}",
                    playersAdded = playersToAdd.Count
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Error updating players for draft group {request.DraftGroupId}");
                return StatusCode(500, "An error occurred while processing the request");
            }
        }
    }
}