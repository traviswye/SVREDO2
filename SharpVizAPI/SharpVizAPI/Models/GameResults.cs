using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace SharpVizAPI.Models
{
    public class GameResults
    {
        [Key]
        public int Id { get; set; }

        [Required]
        public string Date { get; set; }

        [Required]
        public string Time { get; set; }

        //[ForeignKey("GamePreview")]
        public int GamePreviewID { get; set; }

        //[ForeignKey("GameOdds")] 
        public int OddsID { get; set; }

        [Required]
        [StringLength(100)]
        public string HomeTeam { get; set; }

        [Required]
        [StringLength(100)]
        public string AwayTeam { get; set; }

        [Required]
        [StringLength(10)]
        public string Result { get; set; } // Example: "Win" or "Loss"

        [Required]
        public int HomeTeamScore { get; set; }

        [Required]
        public int AwayTeamScore { get; set; }

        [StringLength(100)]
        public string WinningPitcher { get; set; }

        [StringLength(100)]
        public string LosingPitcher { get; set; }

        public bool NRFI { get; set; } // True for NRFI, False otherwise

        public int? F5AwayScore { get; set; } // Nullable if not available
        public int? F5HomeScore { get; set; } // Nullable if not available

        [StringLength(10)]
        public string F5Result { get; set; } // Example: "Win", "Loss", or "Draw"

        public DateTime DateModified { get; set; } = DateTime.UtcNow; // Automatically tracks when modified

        [StringLength(12)]
        public string AwaySP { get; set; } // Starting pitcher for the away team

        [StringLength(12)]
        public string HomeSP { get; set; } // Starting pitcher for the home team

        // New fields for F5 odds
        public double? F5homeOdds { get; set; } // Nullable if not available
        public double? F5awayOdds { get; set; } // Nullable if not available

        // Navigation properties
        //public virtual GamePreview? GamePreview { get; set; }
        //public virtual GameOdds? GameOdds { get; set; }
    }
}
