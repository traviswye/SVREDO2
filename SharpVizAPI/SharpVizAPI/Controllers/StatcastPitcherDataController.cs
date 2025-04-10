using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SharpVizAPI.Data;
using SharpVizAPI.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace SharpVizAPI.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class StatcastPitcherDataController : ControllerBase
    {
        private readonly NrfidbContext _context;

        public StatcastPitcherDataController(NrfidbContext context)
        {
            _context = context;
        }

        // GET: api/StatcastPitcherData
        [HttpGet]
        public async Task<ActionResult<IEnumerable<StatcastPitcherData>>> GetAll()
        {
            return await _context.StatcastPitcherData.ToListAsync();
        }

        // GET: api/StatcastPitcherData/Player/656605/Season/2025
        [HttpGet("Player/{bsId}/{split}/{year}")]
        public async Task<ActionResult<StatcastPitcherData>> GetPlayer(string bsId, string split, int year)
        {
            var data = await _context.StatcastPitcherData
                .Where(p => p.bsID == bsId && p.Split == split && p.Year == year)
                .FirstOrDefaultAsync();

            if (data == null)
            {
                return NotFound();
            }

            return data;
        }

        // GET: api/StatcastPitcherData/Name/Keller/Mitch/Season/2025
        [HttpGet("Name/{lastName}/{firstName}/{split}/{year}")]
        public async Task<ActionResult<StatcastPitcherData>> GetByName(string lastName, string firstName, string split, int year)
        {
            var data = await _context.StatcastPitcherData
                .Where(p => p.lastName == lastName && p.firstName == firstName && p.Split == split && p.Year == year)
                .FirstOrDefaultAsync();

            if (data == null)
            {
                return NotFound();
            }

            return data;
        }

        // GET: api/StatcastPitcherData/BbrefId/kellemi01/Season/2025
        [HttpGet("BbrefId/{bbrefId}/{split}/{year}")]
        public async Task<ActionResult<StatcastPitcherData>> GetByBbrefId(string bbrefId, string split, int year)
        {
            var data = await _context.StatcastPitcherData
                .Where(p => p.BbrefId == bbrefId && p.Split == split && p.Year == year)
                .FirstOrDefaultAsync();

            if (data == null)
            {
                return NotFound();
            }

            return data;
        }

        // GET: api/StatcastPitcherData/Year/2025
        [HttpGet("Year/{year}")]
        public async Task<ActionResult<IEnumerable<StatcastPitcherData>>> GetByYear(int year)
        {
            return await _context.StatcastPitcherData
                .Where(p => p.Year == year)
                .ToListAsync();
        }

        // POST: api/StatcastPitcherData
        [HttpPost]
        public async Task<ActionResult<StatcastPitcherData>> Create(StatcastPitcherData data)
        {
            // Validate model
            if (!ModelState.IsValid)
            {
                return BadRequest(ModelState);
            }

            // Check if entry already exists
            var existingData = await _context.StatcastPitcherData
                .FindAsync(data.bsID, data.Split, data.Year);

            if (existingData != null)
            {
                // Update existing entry
                _context.Entry(existingData).State = EntityState.Detached;
                _context.Entry(data).State = EntityState.Modified;
            }
            else
            {
                // Add new entry
                _context.StatcastPitcherData.Add(data);
            }

            try
            {
                await _context.SaveChangesAsync();
            }
            catch (DbUpdateConcurrencyException)
            {
                if (!StatcastPitcherDataExists(data.bsID, data.Split, data.Year))
                {
                    return NotFound();
                }
                else
                {
                    throw;
                }
            }

            return CreatedAtAction(nameof(GetPlayer),
                new { bsId = data.bsID, split = data.Split, year = data.Year }, data);
        }

        // PUT: api/StatcastPitcherData/656605/Season/2025
        [HttpPut("{bsId}/{split}/{year}")]
        public async Task<IActionResult> Update(string bsId, string split, int year, StatcastPitcherData data)
        {
            if (bsId != data.bsID || split != data.Split || year != data.Year)
            {
                return BadRequest("Composite key values in URL do not match the data");
            }

            _context.Entry(data).State = EntityState.Modified;

            try
            {
                await _context.SaveChangesAsync();
            }
            catch (DbUpdateConcurrencyException)
            {
                if (!StatcastPitcherDataExists(bsId, split, year))
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

        // DELETE: api/StatcastPitcherData/656605/Season/2025
        [HttpDelete("{bsId}/{split}/{year}")]
        public async Task<IActionResult> Delete(string bsId, string split, int year)
        {
            var data = await _context.StatcastPitcherData.FindAsync(bsId, split, year);
            if (data == null)
            {
                return NotFound();
            }

            _context.StatcastPitcherData.Remove(data);
            await _context.SaveChangesAsync();

            return NoContent();
        }

        private bool StatcastPitcherDataExists(string bsId, string split, int year)
        {
            return _context.StatcastPitcherData.Any(e => e.bsID == bsId && e.Split == split && e.Year == year);
        }
    }
}