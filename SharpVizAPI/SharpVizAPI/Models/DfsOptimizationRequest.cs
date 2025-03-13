using System.ComponentModel.DataAnnotations;

namespace SharpVizApi.Models
{
    public class DfsOptimizationRequest
    {
        [Required]
        public int DraftGroupId { get; set; }

        [Required]
        public List<string> Positions { get; set; }

        [Required]
        public int SalaryCap { get; set; }

        // Optional flags
        public bool OptimizeForDkppg { get; set; } = false;
        public string OptimizationMetric { get; set; } = "DKPPG"; // Default to DKPPG, could be "OOPS" etc.
        public int? OppRankLimit { get; set; } = null;  // How many of the worst matchups to consider (e.g., 3 means only use bottom 3 ranked matchups)
        public List<int> UserWatchlist { get; set; } = new List<int>();
        public List<int> ExcludePlayers { get; set; } = new List<int>();
        public List<int>? MustStartPlayers { get; set; }
        public List<string>? Strategy { get; set; }
        public List<string>? Stack { get; set; }
    }

    public class OptimizedPlayer
    {
        public string FullName { get; set; }
        public int PlayerDkId { get; set; }
        public string Position { get; set; }
        public string AssignedPosition { get; set; }
        public int Salary { get; set; }
        public string Team { get; set; }
        public decimal? DKppg { get; set; }
        public string OptimalPosition { get; set; } // Added property for stack tracking
    }

    // Updated DfsOptimizationResponse class to include stack information
    public class DfsOptimizationResponse
    {
        public bool IsSuccessful { get; set; }
        public List<OptimizedPlayer> Players { get; set; }
        public int TotalSalary { get; set; }
        public string Message { get; set; }
        public Dictionary<string, object> StackInfo { get; set; } // Added property for stack information
        public Dictionary<string, int> TeamBreakdown { get; set; } // Added property for team breakdown
    }
}