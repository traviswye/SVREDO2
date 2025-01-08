using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace SharpVizAPI.Models
{
    [Table("TrailingGameLogSplits")]
    public class TrailingGameLogSplit
    {
        [Key]
        [Column(Order = 0)]
        [MaxLength(50)]
        public string BbrefId { get; set; }

        [Required]
        [MaxLength(50)]
        public string Team { get; set; }

        [Key]
        [Column(Order = 1)]
        [MaxLength(50)]
        public string Split { get; set; }

        [Required]
        public double SplitParkFactor { get; set; }

        [Required]
        public int G { get; set; }

        [Required]
        public int PA { get; set; }

        [Required]
        public int AB { get; set; }

        [Required]
        public int R { get; set; }

        [Required]
        public int H { get; set; }

        [Required]
        [Column("2B")]
        public int Doubles { get; set; } // "2B" mapped to a friendlier name

        [Required]
        [Column("3B")]
        public int Triples { get; set; } // "3B" mapped to a friendlier name

        [Required]
        public int HR { get; set; }

        [Required]
        public int RBI { get; set; }

        [Required]
        public int BB { get; set; }

        [Required]
        public int IBB { get; set; }

        [Required]
        public int SO { get; set; }

        [Required]
        public int HBP { get; set; }

        [Required]
        public int SH { get; set; }

        [Required]
        public int SF { get; set; }

        [Required]
        public int ROE { get; set; }

        [Required]
        public int GDP { get; set; }

        [Required]
        public int SB { get; set; }

        [Required]
        public int CS { get; set; }

        [Required]
        public double BA { get; set; }

        [Required]
        public double OBP { get; set; }

        [Required]
        public double SLG { get; set; }

        [Required]
        public double OPS { get; set; }

        [Required]
        public int BOP { get; set; }

        [Required]
        public double ALI { get; set; }

        [Required]
        public double WPA { get; set; }

        [Required]
        public double AcLI { get; set; }

        [Required]
        [MaxLength(10)]
        public string CWPA { get; set; }

        [Required]
        public double RE24 { get; set; }

        [Required]
        [Column("DFS_DK")]
        public double DFSDk { get; set; }

        [Required]
        [Column("DFS_FD")]
        public double DFSFd { get; set; }

        public int HomeGames { get; set; }
        public int AwayGames { get; set; }
        public double HomeParkFactor { get; set; }
        public double AwayParkFactorAvg { get; set; }


        [Key]
        [Column(Order = 2)]
        public DateTime DateUpdated { get; set; }
    }
}
