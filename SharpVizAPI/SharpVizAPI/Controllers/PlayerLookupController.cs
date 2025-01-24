using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SharpVizAPI.Data;
using SharpVizAPI.Models;

namespace SharpVizAPI.Controllers
{

    [ApiController]
    [Route("api/playerlookup")]
    public class PlayerLookupController : ControllerBase
    {
        private readonly NrfidbContext _context;

        public PlayerLookupController(NrfidbContext context)
        {
            _context = context;
        }

        // GET: api/playerlookup
        [HttpGet]
        public async Task<IActionResult> GetAll()
        {
            var players = await _context.PlayerLookup.ToListAsync();
            return Ok(players);
        }

        // GET: api/playerlookup/{bbrefId}/{bsId}
        [HttpGet("{bbrefId}/{bsId}")]
        public async Task<IActionResult> Get(string bbrefId, int bsId)
        {
            var player = await _context.PlayerLookup.FindAsync(bbrefId, bsId);
            if (player == null)
            {
                return NotFound();
            }
            return Ok(player);
        }

        // POST: api/playerlookup
        [HttpPost]
        public async Task<IActionResult> Create([FromBody] PlayerLookup playerLookup)
        {
            if (!ModelState.IsValid)
            {
                return BadRequest(ModelState);
            }

            _context.PlayerLookup.Add(playerLookup);
            await _context.SaveChangesAsync();

            return CreatedAtAction(nameof(Get), new { bbrefId = playerLookup.BbrefId, bsId = playerLookup.BsID }, playerLookup);
        }

        // PUT: api/playerlookup/{bbrefId}/{bsId}
        [HttpPut("{bbrefId}/{bsId}")]
        public async Task<IActionResult> Update(string bbrefId, int bsId, [FromBody] PlayerLookup playerLookup)
        {
            if (bbrefId != playerLookup.BbrefId || bsId != playerLookup.BsID)
            {
                return BadRequest("Composite keys do not match.");
            }

            _context.Entry(playerLookup).State = EntityState.Modified;

            try
            {
                await _context.SaveChangesAsync();
            }
            catch (DbUpdateConcurrencyException)
            {
                if (!_context.PlayerLookup.Any(pl => pl.BbrefId == bbrefId && pl.BsID == bsId))
                {
                    return NotFound();
                }
                throw;
            }

            return NoContent();
        }

        // DELETE: api/playerlookup/{bbrefId}/{bsId}
        [HttpDelete("{bbrefId}/{bsId}")]
        public async Task<IActionResult> Delete(string bbrefId, int bsId)
        {
            var playerLookup = await _context.PlayerLookup.FindAsync(bbrefId, bsId);
            if (playerLookup == null)
            {
                return NotFound();
            }

            _context.PlayerLookup.Remove(playerLookup);
            await _context.SaveChangesAsync();

            return NoContent();
        }

    }

}

