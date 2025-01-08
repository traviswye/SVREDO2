using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace SharpVizAPI.Models
{
    [Table("TeamTotalPitchingTracking")]
    public class TeamTotalPitchingTracking
    {
        [Key]
        [Column(Order = 0)]
        public string TeamName { get; set; }

        [Key]
        [Column(Order = 1)]
        public int Year { get; set; }

        [Key]
        [Column(Order = 2)]
        public DateTime DateAdded { get; set; }

        public int? PitchersUsed { get; set; }
        public decimal? PAge { get; set; }
        public decimal? RAG { get; set; }
        public int? W { get; set; }
        public int? L { get; set; }
        [Column("WLPercentage")]
        public decimal? WLPercentage { get; set; }
        public decimal? ERA { get; set; }
        public int? G { get; set; }
        public int? GS { get; set; }
        public int? GF { get; set; }
        public int? CG { get; set; }
        public int? TSho { get; set; }
        public int? CSho { get; set; }
        public int? SV { get; set; }
        public decimal? IP { get; set; }
        public int? H { get; set; }
        public int? R { get; set; }
        public int? ER { get; set; }
        public int? HR { get; set; }
        public int? BB { get; set; }
        public int? IBB { get; set; }
        public int? SO { get; set; }
        public int? HBP { get; set; }
        public int? BK { get; set; }
        public int? WP { get; set; }
        public int? BF { get; set; }
        public int? ERAPlus { get; set; }
        public decimal? FIP { get; set; }
        public decimal? WHIP { get; set; }
        public decimal? H9 { get; set; }
        public decimal? HR9 { get; set; }
        public decimal? BB9 { get; set; }
        public decimal? SO9 { get; set; }
        public decimal? SOW { get; set; }
        public int? LOB { get; set; }
    }
}
