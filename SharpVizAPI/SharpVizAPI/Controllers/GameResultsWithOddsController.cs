using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SharpVizAPI.Data;
using SharpVizAPI.Models;


namespace SharpVizAPI.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class GameResultsWithOddsController : ControllerBase
    {
        private readonly NrfidbContext _context;

        public GameResultsWithOddsController(NrfidbContext context)
        {
            _context = context;
        }

        // GET: api/GameResultsWithOdds
        [HttpGet]
        public async Task<ActionResult<IEnumerable<GameResultsWithOdds>>> GetGameResultsWithOdds()
        {
            return await _context.GameResultsWithOdds.ToListAsync();
        }

        // GET: api/GameResultsWithOdds/5
        [HttpGet("{id}")]
        public async Task<ActionResult<GameResultsWithOdds>> GetGameResultsWithOdds(int id)
        {
            var gameResult = await _context.GameResultsWithOdds.FindAsync(id);

            if (gameResult == null)
            {
                return NotFound();
            }

            return gameResult;
        }

        // PUT: api/GameResultsWithOdds/5
        [HttpPut("{id}")]
        public async Task<IActionResult> PutGameResultsWithOdds(int id, GameResultsWithOdds gameResult)
        {
            if (id != gameResult.Id)
            {
                return BadRequest();
            }

            _context.Entry(gameResult).State = EntityState.Modified;

            try
            {
                await _context.SaveChangesAsync();
            }
            catch (DbUpdateConcurrencyException)
            {
                if (!GameResultsWithOddsExists(id))
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

        // POST: api/GameResultsWithOdds
        [HttpPost]
        public async Task<ActionResult<GameResultsWithOdds>> PostGameResultsWithOdds(GameResultsWithOdds gameResult)
        {
            _context.GameResultsWithOdds.Add(gameResult);
            await _context.SaveChangesAsync();

            return CreatedAtAction(nameof(GetGameResultsWithOdds), new { id = gameResult.Id }, gameResult);
        }

        // DELETE: api/GameResultsWithOdds/5
        [HttpDelete("{id}")]
        public async Task<IActionResult> DeleteGameResultsWithOdds(int id)
        {
            var gameResult = await _context.GameResultsWithOdds.FindAsync(id);
            if (gameResult == null)
            {
                return NotFound();
            }

            _context.GameResultsWithOdds.Remove(gameResult);
            await _context.SaveChangesAsync();

            return NoContent();
        }

        private bool GameResultsWithOddsExists(int id)
        {
            return _context.GameResultsWithOdds.Any(e => e.Id == id);
        }


        // New GET method to filter results by team name
        // GET: api/GameResultsWithOdds/team?teamName={teamName}
        [HttpGet("team")]
        public async Task<ActionResult<IEnumerable<GameResultsWithOdds>>> GetGameResultsByTeam([FromQuery] string teamName)
        {
            if (string.IsNullOrEmpty(teamName))
            {
                return BadRequest("Team name cannot be empty.");
            }

            var results = await _context.GameResultsWithOdds
                                        .Where(gr => gr.Team == teamName)
                                        .ToListAsync();

            if (!results.Any())
            {
                return NotFound($"No game results found for the team: {teamName}");
            }

            return Ok(results);
        }
    }
}
