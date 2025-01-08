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
    public class GameOddsController : ControllerBase
    {
        private readonly NrfidbContext _context;

        public GameOddsController(NrfidbContext context)
        {
            _context = context;
        }

        // GET: api/GameOdds
        [HttpGet]
        public async Task<ActionResult<IEnumerable<GameOdds>>> GetAllGameOdds()
        {
            return await _context.GameOdds.ToListAsync();
        }

        // GET: api/GameOdds/5
        [HttpGet("{id}")]
        public async Task<ActionResult<GameOdds>> GetGameOdds(int id)
        {
            var gameOdds = await _context.GameOdds.FindAsync(id);

            if (gameOdds == null)
            {
                return NotFound();
            }

            return gameOdds;
        }

        // GET: api/GameOdds/date/{date}
        [HttpGet("date/{date}")]
        public async Task<ActionResult<IEnumerable<GameOdds>>> GetGameOddsByDate(DateTime date)
        {
            return await _context.GameOdds
                .Where(go => go.Date == date)
                .ToListAsync();
        }

        // POST: api/GameOdds
        [HttpPost]
        public async Task<ActionResult<GameOdds>> PostGameOdds(GameOdds gameOdds)
        {
            _context.GameOdds.Add(gameOdds);
            await _context.SaveChangesAsync();

            return CreatedAtAction(nameof(GetGameOdds), new { id = gameOdds.Id }, gameOdds);
        }

        // PUT: api/GameOdds/5
        [HttpPut("{id}")]
        public async Task<IActionResult> PutGameOdds(int id, GameOdds gameOdds)
        {
            if (id != gameOdds.Id)
            {
                return BadRequest();
            }

            _context.Entry(gameOdds).State = EntityState.Modified;

            try
            {
                await _context.SaveChangesAsync();
            }
            catch (DbUpdateConcurrencyException)
            {
                if (!GameOddsExists(id))
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

        // DELETE: api/GameOdds/5
        [HttpDelete("{id}")]
        public async Task<IActionResult> DeleteGameOdds(int id)
        {
            var gameOdds = await _context.GameOdds.FindAsync(id);
            if (gameOdds == null)
            {
                return NotFound();
            }

            _context.GameOdds.Remove(gameOdds);
            await _context.SaveChangesAsync();

            return NoContent();
        }

        private bool GameOddsExists(int id)
        {
            return _context.GameOdds.Any(e => e.Id == id);
        }
    }
}