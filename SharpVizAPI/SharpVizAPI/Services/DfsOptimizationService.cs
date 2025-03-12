using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using SharpVizApi.Models;
using SharpVizApi.Services;
using SharpVizApi.Services.Optimization;

namespace SharpVizAPI.Services
{

    public interface IDfsOptimizationService
    {
        Task<DfsOptimizationResponse> OptimizeLineup(DfsOptimizationRequest request);
    }

    public class DfsOptimizationService : IDfsOptimizationService
    {
        private readonly LineupOptimizerFactory _optimizerFactory;
        private readonly ILogger<DfsOptimizationService> _logger;

        public DfsOptimizationService(
            LineupOptimizerFactory optimizerFactory,
            ILogger<DfsOptimizationService> logger)
        {
            _optimizerFactory = optimizerFactory;
            _logger = logger;
        }

        public async Task<DfsOptimizationResponse> OptimizeLineup(DfsOptimizationRequest request)
        {
            try
            {
                // 1. Determine the sport from the request or the draft group
                string sport = await DetermineSportFromRequest(request);

                // 2. Create the appropriate optimizer
                var optimizer = _optimizerFactory.CreateOptimizer(sport);

                // 3. Map request to optimization parameters
                var parameters = MapRequestToParameters(request, sport);

                // 4. Run the optimization
                var result = await optimizer.OptimizeLineup(parameters);

                // 5. Map the result back to the response format
                return new DfsOptimizationResponse
                {
                    IsSuccessful = result.IsSuccessful,
                    Message = result.Message,
                    Players = result.Players,
                    TotalSalary = result.TotalSalary
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error in DFS optimization service");
                return new DfsOptimizationResponse
                {
                    IsSuccessful = false,
                    Message = $"An error occurred: {ex.Message}"
                };
            }
        }

        private async Task<string> DetermineSportFromRequest(DfsOptimizationRequest request)
        {
            // TODO: Implement this to determine the sport from the request or draft group
            // For now, we'll assume it's MLB
            return "MLB";
        }

        private OptimizationParameters MapRequestToParameters(DfsOptimizationRequest request, string sport)
        {
            var parameters = new OptimizationParameters
            {
                DraftGroupId = request.DraftGroupId,
                Positions = request.Positions,
                SalaryCap = request.SalaryCap,
                UserWatchlist = request.UserWatchlist,
                ExcludePlayers = request.ExcludePlayers,
                MustStartPlayers = request.MustStartPlayers ?? new List<int>(),
                OptimizationCriterion = request.OptimizeForDkppg ? "DKPPG" : "Salary"
            };

            // Add sport-specific parameters
            if (sport.Equals("MLB", StringComparison.OrdinalIgnoreCase))
            {
                parameters.SportSpecificParameters = new MLBParameters
                {
                    StrategyTeams = request.Strategy ?? new List<string>(),
                    StackStrategy = request.Stack?.FirstOrDefault() ?? "Use suggested stack for this slate"
                };
            }

            return parameters;
        }

    }
}