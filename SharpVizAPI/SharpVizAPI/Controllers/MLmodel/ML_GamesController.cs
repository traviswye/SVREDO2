
using Microsoft.AspNetCore.Mvc;
using System.Collections.Generic;
using System.Linq;
using SharpVizAPI.Models;
using SharpVizAPI.Models.MLmodels;

using Microsoft.EntityFrameworkCore;
using SharpVizAPI.Data;

namespace SharpVizAPI.Controllers.MLmodel
{

    [Route("api/[controller]")]
    [ApiController]
    public class ML_GamesController : ControllerBase
    {
        private readonly NrfidbContext _context;

        public ML_GamesController(NrfidbContext context)
        {
            _context = context;
        }

        // GET: api/ML_Games
        [HttpGet]
        public ActionResult<IEnumerable<ML_Games>> GetGames()
        {
            return _context.ML_Games.ToList();
        }

        // GET: api/ML_Games/5
        [HttpGet("{id}")]
        public ActionResult<ML_Games> GetGame(int id)
        {
            var game = _context.ML_Games.Find(id);

            if (game == null)
            {
                return NotFound();
            }

            return game;
        }

        // POST: api/ML_Games
        [HttpPost]
        public ActionResult<ML_Games> PostGame(ML_Games game)
        {
            _context.ML_Games.Add(game);
            _context.SaveChanges();

            return CreatedAtAction("GetGame", new { id = game.GameID }, game);
        }

        // PUT: api/ML_Games/5
        [HttpPut("{id}")]
        public IActionResult PutGame(int id, ML_Games game)
        {
            if (id != game.GameID)
            {
                return BadRequest();
            }

            _context.Entry(game).State = Microsoft.EntityFrameworkCore.EntityState.Modified;

            try
            {
                _context.SaveChanges();
            }
            catch (DbUpdateConcurrencyException)
            {
                if (!_context.ML_Games.Any(e => e.GameID == id))
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

        // DELETE: api/ML_Games/5
        [HttpDelete("{id}")]
        public ActionResult<ML_Games> DeleteGame(int id)
        {
            var game = _context.ML_Games.Find(id);
            if (game == null)
            {
                return NotFound();
            }

            _context.ML_Games.Remove(game);
            _context.SaveChanges();

            return game;
        }
    }
}
