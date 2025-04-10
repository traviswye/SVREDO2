using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace SharpVizAPI.Models
{
    public class StatcastPitcherData
    {
        [Key]
        [Column(Order = 0)]
        [Required]
        public string bsID { get; set; }

        [Key]
        [Column(Order = 1)]
        [Required]
        [MaxLength(50)]
        public string Split { get; set; }

        [Key]
        [Column(Order = 2)]
        [Required]
        public int Year { get; set; }

        [MaxLength(50)]
        public string firstName { get; set; }

        [MaxLength(50)]
        public string lastName { get; set; }

        [MaxLength(20)]
        public string? BbrefId { get; set; }

        public int? PA { get; set; }

        public int? BIP { get; set; }

        public double? BA { get; set; }

        public double? xBA { get; set; }

        public double? SLG { get; set; }

        public double? xSLG { get; set; }

        public double? aWoba { get; set; }

        public double? xaWoba { get; set; }

        public double? ERA { get; set; }

        public double? xERA { get; set; }

        public double? K_perc { get; set; }

        public double? HR_perc { get; set; }

        public double? EV { get; set; }

        public double? LA { get; set; }

        public double? Barrel_perc { get; set; }

        public double? HardHit_perc { get; set; }

        public DateTime? DateAdded { get; set; }
    }
}