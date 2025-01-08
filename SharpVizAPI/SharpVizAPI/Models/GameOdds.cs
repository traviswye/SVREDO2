using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace SharpVizAPI.Models
{
    public class GameOdds
    {
        [Key]
        public int Id { get; set; }

        [Required]
        public DateTime Date { get; set; }

        [Required]
        [StringLength(10)]  // Adjust the string length based on what you expect
        public string GameTime { get; set; }

        [Required]
        [StringLength(100)]
        public string HomeTeam { get; set; }

        [Required]
        [StringLength(100)]
        public string AwayTeam { get; set; }

        [ForeignKey("GamePreview")]
        public int GamePreviewID { get; set; }

        public decimal? FanduelHomeOdds { get; set; }
        public decimal? FanduelAwayOdds { get; set; }
        public decimal? DraftkingsHomeOdds { get; set; }
        public decimal? DraftkingsAwayOdds { get; set; }
        public decimal? BetmgmHomeOdds { get; set; }
        public decimal? BetmgmAwayOdds { get; set; }

        // Do not require the full GamePreview object during POST/PUT
        [NotMapped]
        public virtual GamePreview? GamePreview { get; set; }
    }
}
