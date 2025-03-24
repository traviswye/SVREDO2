using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SharpVizAPI.Data;
using SharpVizAPI.Models;
using SharpVizAPI.Services;

namespace SharpVizAPI.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class ProjectedHitterStatsController : ControllerBase
    {
        private readonly NrfidbContext _context;

        public ProjectedHitterStatsController(NrfidbContext context)
        {
            _context = context;
        }

        // GET: api/ProjectedHitterStats
        [HttpGet]
        public async Task<ActionResult<IEnumerable<ProjectedHitterStats>>> GetProjectedHitterStats()
        {
            return await _context.ProjectedHitterStats.ToListAsync();
        }

        // GET: api/ProjectedHitterStats/year/2025
        [HttpGet("year/{year}")]
        public async Task<ActionResult<IEnumerable<ProjectedHitterStats>>> GetProjectedHitterStatsByYear(int year)
        {
            return await _context.ProjectedHitterStats
                .Where(p => p.Year == year)
                .ToListAsync();
        }

        // GET: api/ProjectedHitterStats/id/bailepa01/2025
        [HttpGet("id/{bbrefId}/{year}")]
        public async Task<ActionResult<ProjectedHitterStats>> GetProjectedHitterStatsById(string bbrefId, int year)
        {
            var projectedHitterStats = await _context.ProjectedHitterStats
                .FindAsync(bbrefId, year);

            if (projectedHitterStats == null)
            {
                return NotFound();
            }

            return projectedHitterStats;
        }

        // GET: api/ProjectedHitterStats/id/bailepa01
        [HttpGet("id/{bbrefId}")]
        public async Task<ActionResult<IEnumerable<ProjectedHitterStats>>> GetProjectedHitterStatsById(string bbrefId)
        {
            var projections = await _context.ProjectedHitterStats
                .Where(p => p.BbrefId == bbrefId)
                .ToListAsync();

            if (projections == null || !projections.Any())
            {
                return NotFound();
            }

            return projections;
        }

        // GET: api/ProjectedHitterStats/name/Patrick Bailey
        [HttpGet("name/{name}")]
        public async Task<ActionResult<IEnumerable<ProjectedHitterStats>>> GetProjectedHitterStatsByName(string name)
        {
            return await _context.ProjectedHitterStats
                .Where(p => p.Name.Contains(name))
                .ToListAsync();
        }

        // GET: api/ProjectedHitterStats/team/SF
        [HttpGet("team/{team}")]
        public async Task<ActionResult<IEnumerable<ProjectedHitterStats>>> GetProjectedHitterStatsByTeam(string team)
        {
            return await _context.ProjectedHitterStats
                .Where(p => p.Team == team)
                .ToListAsync();
        }

        // GET: api/ProjectedHitterStats/team/SF/year/2025
        [HttpGet("team/{team}/year/{year}")]
        public async Task<ActionResult<IEnumerable<ProjectedHitterStats>>> GetProjectedHitterStatsByTeamAndYear(string team, int year)
        {
            return await _context.ProjectedHitterStats
                .Where(p => p.Team == team && p.Year == year)
                .ToListAsync();
        }

        // PUT: api/ProjectedHitterStats/bailepa01/2025
        [HttpPut("{bbrefId}/{year}")]
        public async Task<IActionResult> PutProjectedHitterStats(string bbrefId, int year, ProjectedHitterStats projectedHitterStats)
        {
            if (bbrefId != projectedHitterStats.BbrefId || year != projectedHitterStats.Year)
            {
                return BadRequest();
            }

            _context.Entry(projectedHitterStats).State = EntityState.Modified;

            try
            {
                await _context.SaveChangesAsync();
            }
            catch (DbUpdateConcurrencyException)
            {
                if (!ProjectedHitterStatsExists(bbrefId, year))
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

        // POST: api/ProjectedHitterStats
        [HttpPost]
        public async Task<ActionResult<ProjectedHitterStats>> PostProjectedHitterStats(ProjectedHitterStats projectedHitterStats)
        {
            _context.ProjectedHitterStats.Add(projectedHitterStats);
            try
            {
                await _context.SaveChangesAsync();
            }
            catch (DbUpdateException)
            {
                if (ProjectedHitterStatsExists(projectedHitterStats.BbrefId, projectedHitterStats.Year))
                {
                    // Update existing record
                    _context.Entry(projectedHitterStats).State = EntityState.Modified;
                    await _context.SaveChangesAsync();
                    return Ok(projectedHitterStats);
                }
                else
                {
                    throw;
                }
            }

            return CreatedAtAction("GetProjectedHitterStatsById", new { bbrefId = projectedHitterStats.BbrefId, year = projectedHitterStats.Year }, projectedHitterStats);
        }

        // POST: api/ProjectedHitterStats/batch
        [HttpPost("batch")]
        public async Task<ActionResult<int>> PostBatchProjectedHitterStats(List<ProjectedHitterStats> projections)
        {
            int successCount = 0;

            foreach (var projection in projections)
            {
                var existing = await _context.ProjectedHitterStats
                    .FindAsync(projection.BbrefId, projection.Year);

                if (existing != null)
                {
                    // Update existing record
                    _context.Entry(existing).CurrentValues.SetValues(projection);
                }
                else
                {
                    // Add new record
                    _context.ProjectedHitterStats.Add(projection);
                }

                successCount++;
            }

            await _context.SaveChangesAsync();
            return Ok(new { Count = successCount });
        }

        // DELETE: api/ProjectedHitterStats/bailepa01/2025
        [HttpDelete("{bbrefId}/{year}")]
        public async Task<ActionResult<ProjectedHitterStats>> DeleteProjectedHitterStats(string bbrefId, int year)
        {
            var projectedHitterStats = await _context.ProjectedHitterStats.FindAsync(bbrefId, year);
            if (projectedHitterStats == null)
            {
                return NotFound();
            }

            _context.ProjectedHitterStats.Remove(projectedHitterStats);
            await _context.SaveChangesAsync();

            return projectedHitterStats;
        }

        private bool ProjectedHitterStatsExists(string bbrefId, int year)
        {
            return _context.ProjectedHitterStats.Any(e => e.BbrefId == bbrefId && e.Year == year);
        }
    }

    [Route("api/[controller]")]
    [ApiController]
    public class ProjectedPitcherStatsController : ControllerBase
    {
        private readonly NrfidbContext _context;

        public ProjectedPitcherStatsController(NrfidbContext context)
        {
            _context = context;
        }

        // GET: api/ProjectedPitcherStats
        [HttpGet]
        public async Task<ActionResult<IEnumerable<ProjectedPitcherStats>>> GetProjectedPitcherStats()
        {
            return await _context.ProjectedPitcherStats.ToListAsync();
        }

        // GET: api/ProjectedPitcherStats/year/2025
        [HttpGet("year/{year}")]
        public async Task<ActionResult<IEnumerable<ProjectedPitcherStats>>> GetProjectedPitcherStatsByYear(int year)
        {
            return await _context.ProjectedPitcherStats
                .Where(p => p.Year == year)
                .ToListAsync();
        }

        // GET: api/ProjectedPitcherStats/id/burnsco01/2025
        [HttpGet("id/{bbrefId}/{year}")]
        public async Task<ActionResult<ProjectedPitcherStats>> GetProjectedPitcherStatsById(string bbrefId, int year)
        {
            var projectedPitcherStats = await _context.ProjectedPitcherStats
                .FindAsync(bbrefId, year);

            if (projectedPitcherStats == null)
            {
                return NotFound();
            }

            return projectedPitcherStats;
        }

        // GET: api/ProjectedPitcherStats/id/burnsco01
        [HttpGet("id/{bbrefId}")]
        public async Task<ActionResult<IEnumerable<ProjectedPitcherStats>>> GetProjectedPitcherStatsById(string bbrefId)
        {
            var projections = await _context.ProjectedPitcherStats
                .Where(p => p.BbrefId == bbrefId)
                .ToListAsync();

            if (projections == null || !projections.Any())
            {
                return NotFound();
            }

            return projections;
        }

        // GET: api/ProjectedPitcherStats/name/Corbin Burns
        [HttpGet("name/{name}")]
        public async Task<ActionResult<IEnumerable<ProjectedPitcherStats>>> GetProjectedPitcherStatsByName(string name)
        {
            return await _context.ProjectedPitcherStats
                .Where(p => p.Name.Contains(name))
                .ToListAsync();
        }

        // GET: api/ProjectedPitcherStats/team/MIL
        [HttpGet("team/{team}")]
        public async Task<ActionResult<IEnumerable<ProjectedPitcherStats>>> GetProjectedPitcherStatsByTeam(string team)
        {
            return await _context.ProjectedPitcherStats
                .Where(p => p.Team == team)
                .ToListAsync();
        }

        // GET: api/ProjectedPitcherStats/team/MIL/year/2025
        [HttpGet("team/{team}/year/{year}")]
        public async Task<ActionResult<IEnumerable<ProjectedPitcherStats>>> GetProjectedPitcherStatsByTeamAndYear(string team, int year)
        {
            return await _context.ProjectedPitcherStats
                .Where(p => p.Team == team && p.Year == year)
                .ToListAsync();
        }

        // PUT: api/ProjectedPitcherStats/burnsco01/2025
        [HttpPut("{bbrefId}/{year}")]
        public async Task<IActionResult> PutProjectedPitcherStats(string bbrefId, int year, ProjectedPitcherStats projectedPitcherStats)
        {
            if (bbrefId != projectedPitcherStats.BbrefId || year != projectedPitcherStats.Year)
            {
                return BadRequest();
            }

            _context.Entry(projectedPitcherStats).State = EntityState.Modified;

            try
            {
                await _context.SaveChangesAsync();
            }
            catch (DbUpdateConcurrencyException)
            {
                if (!ProjectedPitcherStatsExists(bbrefId, year))
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

        // POST: api/ProjectedPitcherStats
        [HttpPost]
        public async Task<ActionResult<ProjectedPitcherStats>> PostProjectedPitcherStats(ProjectedPitcherStats projectedPitcherStats)
        {
            _context.ProjectedPitcherStats.Add(projectedPitcherStats);
            try
            {
                await _context.SaveChangesAsync();
            }
            catch (DbUpdateException)
            {
                if (ProjectedPitcherStatsExists(projectedPitcherStats.BbrefId, projectedPitcherStats.Year))
                {
                    // Update existing record
                    _context.Entry(projectedPitcherStats).State = EntityState.Modified;
                    await _context.SaveChangesAsync();
                    return Ok(projectedPitcherStats);
                }
                else
                {
                    throw;
                }
            }

            return CreatedAtAction("GetProjectedPitcherStatsById", new { bbrefId = projectedPitcherStats.BbrefId, year = projectedPitcherStats.Year }, projectedPitcherStats);
        }

        // POST: api/ProjectedPitcherStats/batch
        [HttpPost("batch")]
        public async Task<ActionResult<int>> PostBatchProjectedPitcherStats(List<ProjectedPitcherStats> projections)
        {
            int successCount = 0;

            foreach (var projection in projections)
            {
                var existing = await _context.ProjectedPitcherStats
                    .FindAsync(projection.BbrefId, projection.Year);

                if (existing != null)
                {
                    // Update existing record
                    _context.Entry(existing).CurrentValues.SetValues(projection);
                }
                else
                {
                    // Add new record
                    _context.ProjectedPitcherStats.Add(projection);
                }

                successCount++;
            }

            await _context.SaveChangesAsync();
            return Ok(new { Count = successCount });
        }

        // DELETE: api/ProjectedPitcherStats/burnsco01/2025
        [HttpDelete("{bbrefId}/{year}")]
        public async Task<ActionResult<ProjectedPitcherStats>> DeleteProjectedPitcherStats(string bbrefId, int year)
        {
            var projectedPitcherStats = await _context.ProjectedPitcherStats.FindAsync(bbrefId, year);
            if (projectedPitcherStats == null)
            {
                return NotFound();
            }

            _context.ProjectedPitcherStats.Remove(projectedPitcherStats);
            await _context.SaveChangesAsync();

            return projectedPitcherStats;
        }

        private bool ProjectedPitcherStatsExists(string bbrefId, int year)
        {
            return _context.ProjectedPitcherStats.Any(e => e.BbrefId == bbrefId && e.Year == year);
        }
    }
}