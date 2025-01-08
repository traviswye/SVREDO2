using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using System.Linq;
using System.Threading.Tasks;
using System.Collections.Generic;
using SharpVizAPI.Data;
namespace SharpVizAPI.Controllers
{


    [ApiController]
    [Route("api/[controller]")]
    public class PitchingAverageController : ControllerBase
    {
        private readonly NrfidbContext _context;

        public PitchingAverageController(NrfidbContext context)
        {
            _context = context;
        }

        [HttpGet]
        public async Task<IActionResult> GetAll()
        {
            var pitchingAverages = await _context.PitchingAverages.ToListAsync();
            return Ok(pitchingAverages);
        }

        [HttpGet("{year}")]
        public async Task<IActionResult> GetByYear(int year)
        {
            var pitchingAverage = await _context.PitchingAverages
                .Where(p => p.Year == year)
                .ToListAsync();

            if (pitchingAverage == null || pitchingAverage.Count == 0)
            {
                return NotFound($"No pitching averages found for year: {year}");
            }

            return Ok(pitchingAverage);
        }
    }

}
