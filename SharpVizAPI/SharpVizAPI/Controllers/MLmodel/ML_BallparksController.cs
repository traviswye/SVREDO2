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
    public class ML_BallparksController : ControllerBase
    {
        private readonly NrfidbContext _context;

        public ML_BallparksController(NrfidbContext context)
        {
            _context = context;
        }

        // GET: api/ML_Ballparks
        [HttpGet]
        public ActionResult<IEnumerable<ML_Ballparks>> GetBallparks()
        {
            return _context.ML_Ballparks.ToList();
        }

        // GET: api/ML_Ballparks/5
        [HttpGet("{id}")]
        public ActionResult<ML_Ballparks> GetBallpark(int id)
        {
            var ballpark = _context.ML_Ballparks.Find(id);

            if (ballpark == null)
            {
                return NotFound();
            }

            return ballpark;
        }

        // POST: api/ML_Ballparks
        [HttpPost]
        public ActionResult<ML_Ballparks> PostBallpark(ML_Ballparks ballpark)
        {
            _context.ML_Ballparks.Add(ballpark);
            _context.SaveChanges();

            return CreatedAtAction("GetBallpark", new { id = ballpark.BallparkID }, ballpark);
        }

        // PUT: api/ML_Ballparks/5
        [HttpPut("{id}")]
        public IActionResult PutBallpark(int id, ML_Ballparks ballpark)
        {
            if (id != ballpark.BallparkID)
            {
                return BadRequest();
            }

            _context.Entry(ballpark).State = Microsoft.EntityFrameworkCore.EntityState.Modified;

            try
            {
                _context.SaveChanges();
            }
            catch (DbUpdateConcurrencyException)
            {
                if (!_context.ML_Ballparks.Any(e => e.BallparkID == id))
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

        // DELETE: api/ML_Ballparks/5
        [HttpDelete("{id}")]
        public ActionResult<ML_Ballparks> DeleteBallpark(int id)
        {
            var ballpark = _context.ML_Ballparks.Find(id);
            if (ballpark == null)
            {
                return NotFound();
            }

            _context.ML_Ballparks.Remove(ballpark);
            _context.SaveChanges();

            return ballpark;
        }
    }
}
