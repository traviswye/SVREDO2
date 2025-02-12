using Microsoft.AspNetCore.Mvc;
using SharpVizApi.Services;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace SharpVizApi.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class MLBStrategyController : ControllerBase
    {
        private readonly IMLBStrategyService _strategyService;
        private readonly ILogger<MLBStrategyController> _logger;

        public MLBStrategyController(IMLBStrategyService strategyService, ILogger<MLBStrategyController> logger)
        {
            _strategyService = strategyService;
            _logger = logger;
        }

        /// <summary>
        /// Gets optimal stacking strategies for a given slate size
        /// </summary>
        /// <param name="numberOfGames">Number of games in the slate</param>
        /// <returns>Recommended stacking strategies and their historical win rates</returns>
        [HttpGet("optimal-strategy/{numberOfGames}")]
        public ActionResult<SlateStrategy> GetOptimalStrategy(int numberOfGames)
        {
            try
            {
                if (numberOfGames <= 0)
                {
                    return BadRequest("Number of games must be greater than 0");
                }

                _logger.LogInformation($"Getting optimal strategy for {numberOfGames} games");
                var strategy = _strategyService.GetOptimalStrategy(numberOfGames);

                return Ok(strategy);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Error getting optimal strategy for {numberOfGames} games");
                return StatusCode(500, "An error occurred while processing the request");
            }
        }

        /// <summary>
        /// Gets stack requirements for a specific strategy
        /// </summary>
        /// <param name="strategy">Strategy name (e.g., "5-3", "4-4")</param>
        /// <returns>Stack size requirements for primary and secondary teams</returns>
        [HttpGet("stack-requirements/{strategy}")]
        public ActionResult<List<(string Team, int StackSize)>> GetStackRequirements(string strategy)
        {
            try
            {
                if (!IsValidStrategyFormat(strategy))
                {
                    return BadRequest("Invalid strategy format. Must be in format 'X-Y' where X and Y are numbers (e.g., '5-3')");
                }

                _logger.LogInformation($"Getting stack requirements for strategy {strategy}");
                var requirements = _strategyService.GetStackRequirements(strategy);

                return Ok(requirements);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Error getting stack requirements for strategy {strategy}");
                return StatusCode(500, "An error occurred while processing the request");
            }
        }

        /// <summary>
        /// Validates strategy format
        /// </summary>
        private bool IsValidStrategyFormat(string strategy)
        {
            if (string.IsNullOrWhiteSpace(strategy)) return false;

            var parts = strategy.Split('-');
            if (parts.Length != 2) return false;

            return int.TryParse(parts[0], out int first) &&
                   int.TryParse(parts[1], out int second) &&
                   first > 0 && second > 0;
        }
    }

    // Response models for better API documentation
    public class StrategyResponse
    {
        public string RecommendedStrategy { get; set; }
        public List<AlternativeStrategy> AlternativeStrategies { get; set; }
        public string Reasoning { get; set; }
    }

    public class AlternativeStrategy
    {
        public string Name { get; set; }
        public double WinRate { get; set; }
    }

    public class StackRequirementResponse
    {
        public string Team { get; set; }
        public int RequiredPlayers { get; set; }
    }
}