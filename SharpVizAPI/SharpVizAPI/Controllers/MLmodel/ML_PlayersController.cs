using Microsoft.AspNetCore.Mvc;
using System.Collections.Generic;
using System.Linq;
using SharpVizAPI.Models.MLmodels;
using SharpVizAPI.Data;
using Microsoft.EntityFrameworkCore;

namespace SharpVizAPI.Controllers.MLmodel
{
    [Route("api/[controller]")]
    [ApiController]
    public class ML_PlayersController : ControllerBase
    {
        private readonly NrfidbContext _context;

        public ML_PlayersController(NrfidbContext context)
        {
            _context = context;
        }

        // GET: api/ML_Players
        [HttpGet]
        public ActionResult<IEnumerable<ML_Players>> GetPlayers()
        {
            return _context.ML_Players.ToList();
        }

        // GET: api/ML_Players/5
        [HttpGet("{id}")]
        public ActionResult<ML_Players> GetPlayer(int id)
        {
            var player = _context.ML_Players.Find(id);

            if (player == null)
            {
                return NotFound();
            }

            return player;
        }

        // POST: api/ML_Players
        [HttpPost]
        public ActionResult<ML_Players> PostPlayer(ML_Players player)
        {
            _context.ML_Players.Add(player);
            _context.SaveChanges();

            return CreatedAtAction("GetPlayer", new { id = player.PlayerID }, player);
        }

        // PUT: api/ML_Players/5
        [HttpPut("{id}")]
        public IActionResult PutPlayer(int id, ML_Players player)
        {
            if (id != player.PlayerID)
            {
                return BadRequest();
            }

            _context.Entry(player).State = Microsoft.EntityFrameworkCore.EntityState.Modified;

            try
            {
                _context.SaveChanges();
            }
            catch (DbUpdateConcurrencyException)
            {
                if (!_context.ML_Players.Any(e => e.PlayerID == id))
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

        // DELETE: api/ML_Players/5
        [HttpDelete("{id}")]
        public ActionResult<ML_Players> DeletePlayer(int id)
        {
            var player = _context.ML_Players.Find(id);
            if (player == null)
            {
                return NotFound();
            }

            _context.ML_Players.Remove(player);
            _context.SaveChanges();

            return player;
        }
    }
}
