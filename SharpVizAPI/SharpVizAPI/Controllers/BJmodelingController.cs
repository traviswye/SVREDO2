using Microsoft.AspNetCore.Mvc;
using SharpVizAPI.Services;
using System;
using System.Threading.Tasks;

namespace SharpVizAPI.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class BJmodelingController : ControllerBase
    {
        private readonly BJmodelingService _BJmodelingService;

        public BJmodelingController(BJmodelingService bjmodelingService)
        {
            _BJmodelingService = bjmodelingService;
        }

        [HttpGet("rawWinProbability")]
        public async Task<IActionResult> GetRawWinProbability([FromQuery] string? teamName, [FromQuery] DateTime date)
        {
            if (string.IsNullOrEmpty(teamName))
            {
                // No team provided, return all probabilities for games on the given date
                var probabilities = await _BJmodelingService.GetRawWinProbabilitiesForDateAsync(date);

                if (probabilities == null)
                {
                    return NotFound("No games found for the provided date.");
                }

                return Ok(probabilities);
            }

            // If team name is provided
            var probability = await _BJmodelingService.GetRawWinProbabilityAsync(teamName, date);

            if (probability == null)
            {
                return NotFound("Game preview or team records not found.");
            }

            return Ok(new { Team = teamName, Date = date, WinProbability = probability });
        }

        [HttpGet("pythagWinProbability")]
        public async Task<IActionResult> GetPythagWinProbability([FromQuery] string? teamName, [FromQuery] DateTime date)
        {
            if (string.IsNullOrEmpty(teamName))
            {
                // No team provided, return all probabilities for games on the given date
                var probabilities = await _BJmodelingService.GetPythagWinProbabilitiesForDateAsync(date);

                if (probabilities == null)
                {
                    return NotFound("No games found for the provided date.");
                }

                return Ok(probabilities);
            }

            // If team name is provided
            var probability = await _BJmodelingService.GetPythagWinProbabilityAsync(teamName, date);

            if (probability == null)
            {
                return NotFound("Game preview or team records not found.");
            }

            return Ok(new { Team = teamName, Date = date, WinProbability = probability });
        }

        [HttpGet("calculateBaseRuns")]
        public async Task<IActionResult> CalculateBsR([FromQuery] string bbrefid, int year, [FromQuery] string? split = null)
        {
            if (string.IsNullOrEmpty(bbrefid))
            {
                return BadRequest("bbrefid is required.");
            }
            //if we do NOT have a split defined in the request we will work off our Hitters Table stats
            if (string.IsNullOrEmpty(split))
            {
                var result = await _BJmodelingService.CalculateBsRAsync(bbrefid, year);

                if (result == null)
                {
                    return NotFound("Hitter not found for the given bbrefid.");
                }

                var (id, bsr, games, bsrPerGame) = result.Value;
                return Ok(new
                {
                    BbrefId = id,
                    BaseRuns = bsr,
                    Games = games,
                    BsRPerGame = bsrPerGame
                });
            }
            //if we do have a split defined in the request we will work off our trailingGameLogStats Table stats
            else
            {
                var result = await _BJmodelingService.CalculateBsRAsync(bbrefid, year, split);

                if (result == null)
                {
                    return NotFound("Hitter not found for the given bbrefid.");
                }

                var (id, bsr, games, bsrPerGame) = result.Value;
                return Ok(new
                {
                    BbrefId = id,
                    BaseRuns = bsr,
                    Games = games,
                    BsRPerGame = bsrPerGame
                });
            }


        }

        [HttpGet("calculateRCBase24")]
        public async Task<IActionResult> CalculateRCBase24([FromQuery] string bbrefid, int year, [FromQuery] string? split = null)
        {
            if (string.IsNullOrEmpty(bbrefid))
            {
                return BadRequest("bbrefid is required.");
            }
            //if we do NOT have a split defined in the request we will work off our Hitters Table stats
            if (string.IsNullOrEmpty(split))
            {
                var result = await _BJmodelingService.CalculateRCBase24Async(bbrefid, year);

                if (result == null)
                {
                    return NotFound("Hitter not found for the given bbrefid.");
                }

                var (id, rcBase24, games, rcBase24PerG) = result.Value;
                return Ok(new
                {
                    BbrefId = id,
                    RCBase24 = rcBase24,
                    Games = games,
                    RC24perG = rcBase24PerG
                });
            }
            //if we do have a split defined in the request we will work off our trailingGameLogStats Table stats
            else
            {
                var result = await _BJmodelingService.CalculateRCBase24Async(bbrefid, year, split);

                if (result == null)
                {
                    return NotFound("Hitter not found for the given bbrefid.");
                }

                var (id, rcBase24, games, rcBase24PerG) = result.Value;
                return Ok(new
                {
                    BbrefId = id,
                    RCBase24 = rcBase24,
                    Games = games,
                    RC24perG = rcBase24PerG
                });
            }

        }

        [HttpGet("calculateBasicRC")]
        public async Task<IActionResult> CalculateBasicRC([FromQuery] string bbrefid, int year, [FromQuery] string? split = null)
        {
            if (string.IsNullOrEmpty(bbrefid))
            {
                return BadRequest("bbrefid is required.");
            }//if we do NOT have a split defined in the request we will work off our Hitters Table stats
            if (string.IsNullOrEmpty(split))
            {
                var result = await _BJmodelingService.CalculateBasicRCAsync(bbrefid, year);

                if (result == null)
                {
                    return NotFound("Hitter not found for the given bbrefid.");
                }

                var (id, rc, games, rcPerG) = result.Value;
                return Ok(new
                {
                    BbrefId = id,
                    BasicRC = rc,
                    Games = games,
                    RCPerGame = rcPerG
                });
            }
            //if we do have a split defined in the request we will work off our trailingGameLogStats Table stats
            else
            {
                var result = await _BJmodelingService.CalculateBasicRCAsync(bbrefid, year, split);

                if (result == null)
                {
                    return NotFound("Hitter not found for the given bbrefid.");
                }

                var (id, rc, games, rcPerG) = result.Value;
                return Ok(new
                {
                    BbrefId = id,
                    BasicRC = rc,
                    Games = games,
                    RCPerGame = rcPerG
                });
            }

        }

        [HttpGet("calculateTechRC")]
        public async Task<IActionResult> CalculateTechRC([FromQuery] string bbrefid, int year, [FromQuery] string? split = null)
        {

            if (string.IsNullOrEmpty(bbrefid))
            {
                return BadRequest("bbrefid is required.");
            }
            //if we do NOT have a split defined in the request we will work off our Hitters Table stats
            if (string.IsNullOrEmpty(split)){
                var result = await _BJmodelingService.CalculateTechRCAsync(bbrefid, year);
                if (result == null)
                {
                    return NotFound("Hitter not found for the given bbrefid.");
                }

                var (id, rc, games, rcPerG) = result.Value;
                return Ok(new
                {
                    BbrefId = id,
                    TechRC = rc,
                    Games = games,
                    RCPerGame = rcPerG
                });
            }            
            //if we do have a split defined in the request we will work off our trailingGameLogStats Table stats
            else
            {
                var result = await _BJmodelingService.CalculateTechRCAsync(bbrefid, year, split);
                if (result == null)
                {
                    return NotFound("Hitter not found for the given bbrefid.");
                }

                var (id, rc, games, rcPerG) = result.Value;
                return Ok(new
                {
                    BbrefId = id,
                    TechRC = rc,
                    Games = games,
                    RCPerGame = rcPerG
                });
            }
                        
        }
        [HttpGet("normalizeStat")]
        public async Task<IActionResult> NormalizeStat([FromQuery] string bbrefid, int year, [FromQuery] string methodFlag)
        {
            if (string.IsNullOrEmpty(bbrefid))
            {
                return BadRequest("bbrefid is required.");
            }

            if (string.IsNullOrEmpty(methodFlag))
            {
                return BadRequest("methodFlag is required.");
            }

            try
            {
                var result = await _BJmodelingService.NormalizeStatAsync(bbrefid, year, methodFlag);

                if (result == null)
                {
                    return NotFound("No data found for the provided bbrefid, year, and methodFlag.");
                }

                var (id, normalizedSeasonStat, normalizedL7Stat, nssPerG, nL7sPerG) = result.Value;

                return Ok(new
                {
                    BbrefId = id,
                    NormalizedSeasonStat = normalizedSeasonStat,
                    NormalizedL7Stat = normalizedL7Stat,
                    NSSPerGame = nssPerG,
                    NL7SPerGame = nL7sPerG
                });
            }
            catch (ArgumentException ex)
            {
                return BadRequest(ex.Message);
            }
            catch (Exception ex)
            {
                return StatusCode(500, $"An error occurred: {ex.Message}");
            }
        }


    }


}
