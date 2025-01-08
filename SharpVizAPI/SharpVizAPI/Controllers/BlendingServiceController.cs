using Microsoft.AspNetCore.Mvc;
using SharpVizAPI.Services;
using SharpVizAPI.Data;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using System;
using System.Linq;
using System.Collections.Generic;
using SharpVizAPI.Models;

namespace SharpVizAPI.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class BlendingController : ControllerBase
    {
        private readonly BlendingService _blendingService;
        private readonly NrfidbContext _context;

        public BlendingController(BlendingService blendingService, NrfidbContext context)
        {
            _blendingService = blendingService;
            _context = context;
        }

        // This method returns the default weights structure
        [HttpGet("defaultWeights")]
        public IActionResult GetDefaultWeights()
        {
            // Define the default weights as per your current logic
            var defaultWeights = new Dictionary<string, double>
        {
            {"AB/R", 1},
            {"AB/H", 1},
            {"PA/HR", 1},
            {"AB/SB", 0.01},
            {"SB/SB+CS", 0.5}, // Lower is better
            {"PA/BB", 1},
            {"AB/SO", 0.5}, // Lower is better
            {"SOW", 0.5},
            {"BA", 1},  // Lower is better
            {"OBP", 1}, // Lower is better
            {"SLG", 1}, // Lower is better
            {"OPS", 1}, // Lower is better
            {"PA/TB", 1},
            {"AB/GDP", 0.5},
            {"BAbip", 1}, // Lower is better
            {"tOPSPlus", 1},
            {"sOPSPlus", 1}
        };

            return Ok(defaultWeights);
        }

        [HttpGet("todaysSPHistoryVsRecency")]
        public async Task<IActionResult> GetPitchersBlendingResults([FromQuery] string date = null)
        {
            DateTime selectedDate;

            // Parse the input date or default to today's date
            if (!string.IsNullOrEmpty(date) && DateTime.TryParse(date, out selectedDate))
            {
                selectedDate = DateTime.Parse(date);
            }
            else
            {
                selectedDate = DateTime.Today;
            }

            // Retrieve games from the gamePreview table for the selected date
            var gamesOnDate = await _context.GamePreviews
                                            .Where(g => g.Date == selectedDate)
                                            .ToListAsync();

            if (gamesOnDate == null || !gamesOnDate.Any())
            {
                return NotFound($"No games found for the date {selectedDate.ToString("yyyy-MM-dd")}.");
            }

            var blendingResults = new List<object>();

            // Loop through each game and get the pitchers
            foreach (var game in gamesOnDate)
            {
                if (!string.IsNullOrEmpty(game.HomePitcher))
                {
                    var homePitcherTrends = await _blendingService.GetBlendingResultsForPitcher(game.HomePitcher);
                    if (homePitcherTrends != null)
                    {
                        var analysisResult = _blendingService.AnalyzeTrends(game.HomePitcher, homePitcherTrends);
                        blendingResults.Add(analysisResult);
                    }
                    else
                    {
                        blendingResults.Add(new { Pitcher = game.HomePitcher, Results = "No data available" });
                    }
                }

                if (!string.IsNullOrEmpty(game.AwayPitcher))
                {
                    var awayPitcherTrends = await _blendingService.GetBlendingResultsForPitcher(game.AwayPitcher);
                    if (awayPitcherTrends != null)
                    {
                        var analysisResult = _blendingService.AnalyzeTrends(game.AwayPitcher, awayPitcherTrends);
                        blendingResults.Add(analysisResult);
                    }
                    else
                    {
                        blendingResults.Add(new { Pitcher = game.AwayPitcher, Results = "No data available" });
                    }
                }
            }

            return Ok(blendingResults);
        }

        // New endpoint for calculating the starting pitcher advantage
        [HttpGet("startingPitcherAdvantage")]
        public async Task<IActionResult> GetStartingPitcherAdvantage([FromQuery] string date = null)
        {
            DateTime selectedDate;

            // Parse the input date or default to today's date
            if (!string.IsNullOrEmpty(date) && DateTime.TryParse(date, out selectedDate))
            {
                selectedDate = DateTime.Parse(date);
            }
            else
            {
                selectedDate = DateTime.Today;
            }

            // Call the BlendingService method to calculate the starting pitcher advantage
            var advantageResults = await _blendingService.CalculateStartingPitcherAdvantage(selectedDate);

            if (advantageResults == null || !advantageResults.Any())
            {
                return NotFound($"No advantages found for the date {selectedDate.ToString("yyyy-MM-dd")}.");
            }

            return Ok(advantageResults);
        }



        // New Compare2SP endpoint
        [HttpGet("compare2sp")]
        public async Task<IActionResult> Compare2SP([FromQuery] string pitchera, [FromQuery] string pitcherb)
        {
            // Ensure both pitcher IDs are provided
            if (string.IsNullOrEmpty(pitchera) || string.IsNullOrEmpty(pitcherb))
            {
                return BadRequest("Both pitcherA and pitcherB bbrefId are required.");
            }

            // Call the service method to compare the two pitchers
            var comparisonResult = await _blendingService.Compare2SP(pitchera, pitcherb);

            if (comparisonResult == null || comparisonResult.ContainsKey("message"))
            {
                return NotFound(comparisonResult["message"]);
            }

            // Return the comparison result as JSON
            return Ok(comparisonResult);
        }


        // This is the compare2spCustom method that accepts custom weights
        [HttpGet("compare2spCustom")]
        public async Task<IActionResult> Compare2SPCustom([FromQuery] string pitcheraId, [FromQuery] string pitcherbId, [FromQuery] CustomWeights2SP weights)
        {
            // Define the default weights
            var defaultWeights = new Dictionary<string, double>
    {
        {"AB/R", 1},
        {"AB/H", 1},
        {"PA/HR", 1},
        {"AB/SB", 0.01},
        {"SB/SB+CS", 0.5}, // Lower is better
        {"PA/BB", 1},
        {"AB/SO", 0.5}, // Lower is better
        {"SOW", 0.5},
        {"BA", 1},  // Lower is better
        {"OBP", 1}, // Lower is better
        {"SLG", 1}, // Lower is better
        {"OPS", 1}, // Lower is better
        {"PA/TB", 1},
        {"AB/GDP", 0.5},
        {"BAbip", 1}, // Lower is better
        {"tOPSPlus", 1},
        {"sOPSPlus", 1}
    };

            // Create the custom weights dictionary
            var weightsDict = new Dictionary<string, double>
    {
        {"AB/R", weights.AB_R != 0 ? weights.AB_R : defaultWeights["AB/R"]},
        {"AB/H", weights.AB_H != 0 ? weights.AB_H : defaultWeights["AB/H"]},
        {"PA/HR", weights.PA_HR != 0 ? weights.PA_HR : defaultWeights["PA/HR"]},
        {"AB/SB", weights.AB_SB != 0 ? weights.AB_SB : defaultWeights["AB/SB"]},
        {"SB/SB+CS", weights.SB_SB_CS != 0 ? weights.SB_SB_CS : defaultWeights["SB/SB+CS"]},
        {"PA/BB", weights.PA_BB != 0 ? weights.PA_BB : defaultWeights["PA/BB"]},
        {"AB/SO", weights.AB_SO != 0 ? weights.AB_SO : defaultWeights["AB/SO"]},
        {"SOW", weights.SOW != 0 ? weights.SOW : defaultWeights["SOW"]},
        {"BA", weights.BA != 0 ? weights.BA : defaultWeights["BA"]},
        {"OBP", weights.OBP != 0 ? weights.OBP : defaultWeights["OBP"]},
        {"SLG", weights.SLG != 0 ? weights.SLG : defaultWeights["SLG"]},
        {"OPS", weights.OPS != 0 ? weights.OPS : defaultWeights["OPS"]},
        {"PA/TB", weights.PA_TB != 0 ? weights.PA_TB : defaultWeights["PA/TB"]},
        {"AB/GDP", weights.AB_GDP != 0 ? weights.AB_GDP : defaultWeights["AB/GDP"]},
        {"BAbip", weights.BAbip != 0 ? weights.BAbip : defaultWeights["BAbip"]},
        {"tOPSPlus", weights.tOPSPlus != 0 ? weights.tOPSPlus : defaultWeights["tOPSPlus"]},
        {"sOPSPlus", weights.sOPSPlus != 0 ? weights.sOPSPlus : defaultWeights["sOPSPlus"]}
    };

            var result = await _blendingService.Compare2SPCustom(pitcheraId, pitcherbId, weightsDict);

            if (result.ContainsKey("message"))
            {
                return NotFound(result["message"]);
            }

            return Ok(result);
        }

    }
}
