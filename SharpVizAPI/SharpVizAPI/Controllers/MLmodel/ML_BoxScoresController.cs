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
    public class ML_BoxScoresController : ControllerBase
    {
        private readonly NrfidbContext _context;

        public ML_BoxScoresController(NrfidbContext context)
        {
            _context = context;
        }

        // GET: api/ML_BoxScores
        [HttpGet]
        public ActionResult<IEnumerable<ML_BoxScores>> GetBoxScores()
        {
            return _context.ML_BoxScores.ToList();
        }

        // GET: api/ML_BoxScores/5
        [HttpGet("{id}")]
        public ActionResult<ML_BoxScores> GetBoxScore(int id)
        {
            var boxScore = _context.ML_BoxScores.Find(id);

            if (boxScore == null)
            {
                return NotFound();
            }

            return boxScore;
        }

        // POST: api/ML_BoxScores
        [HttpPost]
        public ActionResult<ML_BoxScores> PostBoxScore(ML_BoxScores boxScore)
        {
            _context.ML_BoxScores.Add(boxScore);
            _context.SaveChanges();

            return CreatedAtAction("GetBoxScore", new { id = boxScore.BoxScoreID }, boxScore);
        }

        // PUT: api/ML_BoxScores/5
        [HttpPut("{id}")]
        public IActionResult PutBoxScore(int id, ML_BoxScores boxScore)
        {
            if (id != boxScore.BoxScoreID)
            {
                return BadRequest();
            }

            _context.Entry(boxScore).State = Microsoft.EntityFrameworkCore.EntityState.Modified;

            try
            {
                _context.SaveChanges();
            }
            catch (DbUpdateConcurrencyException)
            {
                if (!_context.ML_BoxScores.Any(e => e.BoxScoreID == id))
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

        // DELETE: api/ML_BoxScores/5
        [HttpDelete("{id}")]
        public ActionResult<ML_BoxScores> DeleteBoxScore(int id)
        {
            var boxScore = _context.ML_BoxScores.Find(id);
            if (boxScore == null)
            {
                return NotFound();
            }

            _context.ML_BoxScores.Remove(boxScore);
            _context.SaveChanges();

            return boxScore;
        }
    }
}
