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
        public int? OppRankLimit { get; set; } = null;  // How many of the worst matchups to consider (e.g., 3 means only use bottom 3 ranked matchups)
        public List<int> UserWatchlist { get; set; } = new List<int>();
        public List<int> ExcludePlayers { get; set; } = new List<int>();
    }

    public class DfsOptimizationResponse
    {
        public List<OptimizedPlayer> Players { get; set; }
        public int TotalSalary { get; set; }
        public bool IsSuccessful { get; set; }
        public string Message { get; set; }
    }

    public class OptimizedPlayer
    {
        public string FullName { get; set; }
        public int PlayerDkId { get; set; }
        public string Position { get; set; }
        public string AssignedPosition { get; set; }  // The position we're using them for (e.g., "UTIL")
        public int Salary { get; set; }
        public string Team { get; set; }
        public decimal? DKppg { get; set; }

    }

}