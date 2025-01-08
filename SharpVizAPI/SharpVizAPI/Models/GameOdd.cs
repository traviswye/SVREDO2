using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
namespace SharpVizAPI.Models
{
    public class GameOdd
    {
        [Key]
        public int Id { get; set; }

        [ForeignKey("GamePreview")]
        public int GamePreviewId { get; set; }
        public GamePreview GamePreview { get; set; }

        [Required]
        [MaxLength(50)]
        public string HomeML { get; set; } // Home team moneyline

        [Required]
        [MaxLength(50)]
        public string AwayML { get; set; } // Away team moneyline

        [MaxLength(50)]
        public string F5HomeML { get; set; } // First 5 innings home team moneyline

        [MaxLength(50)]
        public string F5AwayML { get; set; } // First 5 innings away team moneyline

        [MaxLength(10)]
        public string OverUnder { get; set; } // Over/Under total for the game

        [MaxLength(10)]
        public string F5OverUnder { get; set; } // First 5 innings Over/Under total

        [MaxLength(255)]
        public string OddsLink { get; set; } // URL to the betting odds

        [Required]
        [MaxLength(255)]
        public string PreviewLink { get; set; } // URL from GamePreviews

        public DateTime DateModified { get; set; } = DateTime.Now; // Automatically set to the current date and time
    }

}