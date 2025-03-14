using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using SharpVizApi.Models;

namespace SharpVizApi.Services.Optimization
{
    // Core parameter class for all optimizations
    public class OptimizationParameters
    {
        public int DraftGroupId { get; set; }
        public List<string> Positions { get; set; }
        public int SalaryCap { get; set; }
        public List<int> UserWatchlist { get; set; } = new List<int>();
        public List<int> ExcludePlayers { get; set; } = new List<int>();
        public List<int> MustStartPlayers { get; set; } = new List<int>();
        public string OptimizationCriterion { get; set; } = "DKPPG"; // Default optimization criterion
        public bool IgnorePlayerStatus { get; set; } = false; // Add this property

        // Sport-specific parameters
        public object SportSpecificParameters { get; set; }
    }

    // Result of an optimization
    public class OptimizationResult
    {
        public bool IsSuccessful { get; set; }
        public string Message { get; set; }
        public List<OptimizedPlayer> Players { get; set; } = new List<OptimizedPlayer>();
        public int TotalSalary { get; set; }
        public decimal TotalValue { get; set; } // Value according to the optimization criterion
        public Dictionary<string, object> StackInfo { get; set; } // Added for stack info
        public Dictionary<string, int> TeamBreakdown { get; set; } // Added for team breakdown
        public List<string> ErrorDetails { get; set; } = new List<string>();  // Add this property
    }

    // Interface for all lineup optimizers
    public interface ILineupOptimizer
    {
        Task<OptimizationResult> OptimizeLineup(OptimizationParameters parameters);
    }

    // Base abstract class for all sport-specific optimizers
    public abstract class BaseLineupOptimizer : ILineupOptimizer
    {
        public virtual async Task<OptimizationResult> OptimizeLineup(OptimizationParameters parameters)
        {
            // 1. Validate basic parameters
            if (parameters.DraftGroupId <= 0 || parameters.Positions == null || !parameters.Positions.Any())
            {
                return new OptimizationResult
                {
                    IsSuccessful = false,
                    Message = "Invalid optimization parameters. Draft group ID and positions are required."
                };
            }

            // 2. Call the sport-specific implementation
            return await OptimizeLineupInternal(parameters);
        }

        protected abstract Task<OptimizationResult> OptimizeLineupInternal(OptimizationParameters parameters);
    }

    // Factory to create the appropriate optimizer based on sport
    public class LineupOptimizerFactory
    {
        private readonly IServiceProvider _serviceProvider;

        public LineupOptimizerFactory(IServiceProvider serviceProvider)
        {
            _serviceProvider = serviceProvider;
        }

        public ILineupOptimizer CreateOptimizer(string sport)
        {
            return sport.ToLower() switch
            {
                "mlb" => _serviceProvider.GetRequiredService<MLBLineupOptimizer>(),
                //"nba" => _serviceProvider.GetRequiredService<NBALineupOptimizer>(),
                //"nfl" => _serviceProvider.GetRequiredService<NFLLineupOptimizer>(),
                _ => throw new ArgumentException($"Unsupported sport: {sport}")
            };
        }
    }
}