using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace SharpVizAPI.Models
{
    [Table("BullpenUsage")]
    public class BullpenUsage
    {
        [Key, Column(Order = 0)]
        [Required]
        [StringLength(255)]
        public string Bbrefid { get; set; }

        [Key, Column(Order = 1)]
        [Required]
        public int TeamGameNumber { get; set; }

        [Required]
        [StringLength(255)]
        public string Name { get; set; }

        [Required]
        [StringLength(50)]
        public string Team { get; set; }

        [Required]
        public int Year { get; set; }

        [Required]
        public DateTime DatePitched { get; set; }

        [Required]
        public int DaysOfRest { get; set; }

        [Required]
        public int PitcherOrder { get; set; }

        [Required]
        public int SPscore { get; set; }

        [Required]
        public int Win { get; set; }

        [Required]
        public int Loss { get; set; }

        [Required]
        public int Hold { get; set; }

        [Required]
        public int Sv { get; set; }

        [Required]
        public int Bsv { get; set; }

        [StringLength(255)]
        public string Umpire { get; set; }

        [Required]
        [StringLength(255)]
        public string Opponent { get; set; }

        public int? BallparkFactor { get; set; }

        [StringLength(50)]
        public string Result { get; set; }

        [Required]
        public int ExtraInnings { get; set; }

        [StringLength(2083)]
        public string BoxScoreUrl { get; set; }
    }
}
