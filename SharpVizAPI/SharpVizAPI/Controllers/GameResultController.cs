using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SharpVizAPI.Data;
using SharpVizAPI.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;


namespace SharpVizAPI
{


    [Route("api/[controller]")]
    [ApiController]
    public class GameResultsController : ControllerBase
    {
        private readonly NrfidbContext _context;

        public GameResultsController(NrfidbContext context)
        {
            _context = context;
        }

        // GET: api/GameResults
        [HttpGet]
        public async Task<ActionResult<IEnumerable<GameResults>>> GetAllGameResults()
        {
            return await _context.GameResults.ToListAsync();
        }

        // GET: api/GameResults/5
        [HttpGet("{id}")]
        public async Task<ActionResult<GameResults>> GetGameResults(int id)
        {
            var gameResults = await _context.GameResults.FindAsync(id);

            if (gameResults == null)
            {
                return NotFound();
            }

            return gameResults;
        }

        // GET: api/GameResults/date/{date}
        //[HttpGet("date/{date}")]
        //public async Task<ActionResult<IEnumerable<GameResults>>> GetGameResultsByDate(DateTime date)
        //{
        //    return await _context.GameResults
        //        .Where(gr => gr.Date == date)
        //        .ToListAsync();
        //}

        // POST: api/GameResults
        [HttpPost]
        public async Task<ActionResult<GameResults>> PostGameResults(GameResults gameResults)
        {
            _context.GameResults.Add(gameResults);
            await _context.SaveChangesAsync();

            return CreatedAtAction(nameof(GetGameResults), new { id = gameResults.Id }, gameResults);
        }

        // PUT: api/GameResults/5
        [HttpPut("{id}")]
        public async Task<IActionResult> PutGameResults(int id, GameResults gameResults)
        {
            if (id != gameResults.Id)
            {
                return BadRequest();
            }

            _context.Entry(gameResults).State = EntityState.Modified;

            try
            {
                await _context.SaveChangesAsync();
            }
            catch (DbUpdateConcurrencyException)
            {
                if (!GameResultsExists(id))
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

        // DELETE: api/GameResults/5
        [HttpDelete("{id}")]
        public async Task<IActionResult> DeleteGameResults(int id)
        {
            var gameResults = await _context.GameResults.FindAsync(id);
            if (gameResults == null)
            {
                return NotFound();
            }

            _context.GameResults.Remove(gameResults);
            await _context.SaveChangesAsync();

            return NoContent();
        }

        private bool GameResultsExists(int id)
        {
            return _context.GameResults.Any(e => e.Id == id);
        }


        // GET: api/GameResults/hometeam/{homeTeam}
        [HttpGet("hometeam/{homeTeam}")]
        public async Task<ActionResult<IEnumerable<GameResults>>> GetGameResultsByHomeTeam(string homeTeam)
        {
            var gameResults = await _context.GameResults
                .Where(gr => gr.HomeTeam == homeTeam)
                .ToListAsync();

            if (gameResults == null || gameResults.Count == 0)
            {
                return NotFound();
            }

            return gameResults;
        }

    }
}