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
    public class ML_PitchingStatsController : ControllerBase
    {
        private readonly NrfidbContext _context;

        public ML_PitchingStatsController(NrfidbContext context)
        {
            _context = context;
        }

        // GET: api/ML_PitchingStats
        [HttpGet]
        public ActionResult<IEnumerable<ML_PitchingStats>> GetPitchingStats()
        {
            return _context.ML_PitchingStats.ToList();
        }

        // GET: api/ML_PitchingStats/5
        [HttpGet("{id}")]
        public ActionResult<ML_PitchingStats> GetPitchingStat(int id)
        {
            var pitchingStat = _context.ML_PitchingStats.Find(id);

            if (pitchingStat == null)
            {
                return NotFound();
            }

            return pitchingStat;
        }

        // POST: api/ML_PitchingStats
        [HttpPost]
        public ActionResult<ML_PitchingStats> PostPitchingStat(ML_PitchingStats pitchingStat)
        {
            _context.ML_PitchingStats.Add(pitchingStat);
            _context.SaveChanges();

            return CreatedAtAction("GetPitchingStat", new { id = pitchingStat.PitchingID }, pitchingStat);
        }

        // PUT: api/ML_PitchingStats/5
        [HttpPut("{id}")]
        public IActionResult PutPitchingStat(int id, ML_PitchingStats pitchingStat)
        {
            if (id != pitchingStat.PitchingID)
            {
                return BadRequest();
            }

            _context.Entry(pitchingStat).State = Microsoft.EntityFrameworkCore.EntityState.Modified;

            try
            {
                _context.SaveChanges();
            }
            catch (DbUpdateConcurrencyException)
            {
                if (!_context.ML_PitchingStats.Any(e => e.PitchingID == id))
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

        // DELETE: api/ML_PitchingStats/5
        [HttpDelete("{id}")]
        public ActionResult<ML_PitchingStats> DeletePitchingStat(int id)
        {
            var pitchingStat = _context.ML_PitchingStats.Find(id);
            if (pitchingStat == null)
            {
                return NotFound();
            }

            _context.ML_PitchingStats.Remove(pitchingStat);
            _context.SaveChanges();

            return pitchingStat;
        }
    }
}
