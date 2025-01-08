using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SharpVizAPI.Data;
using SharpVizAPI.Models;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace SharpVizAPI.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class TeamRecSplitsArchiveController : ControllerBase
    {
        private readonly NrfidbContext _context;

        public TeamRecSplitsArchiveController(NrfidbContext context)
        {
            _context = context;
        }

        // GET: api/TeamRecSplitsArchive/{year}
        [HttpGet("{year}")]
        public async Task<ActionResult<IEnumerable<TeamRecSplitsArchive>>> GetArchivedTeamRecSplits(int year)
        {
            var archivedRecords = await _context.TeamRecSplitsArchive
                .Where(record => record.Year == year)
                .ToListAsync();

            if (!archivedRecords.Any())
            {
                return NotFound($"No records found for year {year}.");
            }

            return archivedRecords;
        }

        // GET: api/TeamRecSplitsArchive/{year}/{team}
        [HttpGet("{year}/{team}")]
        public async Task<ActionResult<TeamRecSplitsArchive>> GetTeamRecSplitForYear(int year, string team)
        {
            var record = await _context.TeamRecSplitsArchive
                .FirstOrDefaultAsync(r => r.Year == year && r.Team == team);

            if (record == null)
            {
                return NotFound($"No record found for team {team} in year {year}.");
            }

            return record;
        }
    }
}
