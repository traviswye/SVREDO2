using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace SharpVizAPI.Models
{
    public class GameResult
    {
        [Key]
        public int Id { get; set; }

        [ForeignKey("GamePreview")]
        public int GamePreviewId { get; set; }
        public GamePreview GamePreview { get; set; }

        [Required]
        public int HomeTeamScore { get; set; }

        [Required]
        public int AwayTeamScore { get; set; }

        [Required]
        [MaxLength(50)]
        public string GameResultStatus { get; set; } // e.g., "HomeWin", "AwayWin", "Draw"

        public string WinningPitcher { get; set; } // bbrefID of the winning pitcher

        public string LosingPitcher { get; set; } // bbrefID of the losing pitcher

        [Required]
        public bool NRFI { get; set; } // 1 if No Runs in the First Inning, 0 otherwise

        [MaxLength(10)]
        public string F5Score { get; set; } // Score after the first 5 innings, format "3-2"

        [MaxLength(50)]
        public string F5Result { get; set; } // e.g., "HomeWin", "AwayWin", "Draw"

        [MaxLength(10)]
        public string OUResult { get; set; } // e.g., "Over", "Under", or "Push"

        public DateTime DateModified { get; set; } = DateTime.Now; // Automatically set to the current date and time
    }

}