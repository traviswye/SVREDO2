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
    public class ML_LineupsController : ControllerBase
    {
        private readonly NrfidbContext _context;

        public ML_LineupsController(NrfidbContext context)
        {
            _context = context;
        }

        // GET: api/ML_Lineups
        [HttpGet]
        public ActionResult<IEnumerable<ML_Lineups>> GetLineups()
        {
            return _context.ML_Lineups.ToList();
        }

        // GET: api/ML_Lineups/5
        [HttpGet("{id}")]
        public ActionResult<ML_Lineups> GetLineup(int id)
        {
            var lineup = _context.ML_Lineups.Find(id);

            if (lineup == null)
            {
                return NotFound();
            }

            return lineup;
        }

        // POST: api/ML_Lineups
        [HttpPost]
        public ActionResult<ML_Lineups> PostLineup(ML_Lineups lineup)
        {
            _context.ML_Lineups.Add(lineup);
            _context.SaveChanges();

            return CreatedAtAction("GetLineup", new { id = lineup.LineupID }, lineup);
        }

        // PUT: api/ML_Lineups/5
        [HttpPut("{id}")]
        public IActionResult PutLineup(int id, ML_Lineups lineup)
        {
            if (id != lineup.LineupID)
            {
                return BadRequest();
            }

            _context.Entry(lineup).State = Microsoft.EntityFrameworkCore.EntityState.Modified;

            try
            {
                _context.SaveChanges();
            }
            catch (DbUpdateConcurrencyException)
            {
                if (!_context.ML_Lineups.Any(e => e.LineupID == id))
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

        // DELETE: api/ML_Lineups/5
        [HttpDelete("{id}")]
        public ActionResult<ML_Lineups> DeleteLineup(int id)
        {
            var lineup = _context.ML_Lineups.Find(id);
            if (lineup == null)
            {
                return NotFound();
            }

            _context.ML_Lineups.Remove(lineup);
            _context.SaveChanges();

            return lineup;
        }
    }
}
