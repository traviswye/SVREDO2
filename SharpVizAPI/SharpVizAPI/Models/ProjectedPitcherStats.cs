using System;
using System.ComponentModel.DataAnnotations.Schema;
using System.ComponentModel.DataAnnotations;

namespace SharpVizAPI.Models
{
    [Table("projectedPitcherStats", Schema = "dbo")]
    public class ProjectedPitcherStats
    {
        [Key]
        [Column("bbrefid")]
        public string BbrefId { get; set; }

        [Column("year")]
        public int Year { get; set; }

        [Column("name")]
        [Required]
        [MaxLength(100)]
        public string Name { get; set; }

        [Column("Team")]
        [MaxLength(5)]
        public string Team { get; set; }

        [Column("IP")]
        //[Column(TypeName = "decimal(5, 1)")]
        public decimal IP { get; set; }

        [Column("K")]
        public int K { get; set; }

        [Column("W")]
        public int W { get; set; }

        [Column("L")]
        public int L { get; set; }

        [Column("SV")]
        public int SV { get; set; }

        [Column("ERA")]
        //[Column(TypeName = "decimal(4, 3)")]
        public decimal ERA { get; set; }

        [Column("WHIP")]
        //[Column(TypeName = "decimal(4, 3)")]
        public decimal WHIP { get; set; }

        [Column("ER")]
        public int ER { get; set; }

        [Column("H")]
        public int H { get; set; }

        [Column("BB")]
        public int BB { get; set; }

        [Column("HR")]
        public int HR { get; set; }

        [Column("G")]
        public int G { get; set; }

        [Column("GS")]
        public int GS { get; set; }

        [Column("CG")]
        public int CG { get; set; }

        [Column("ROSTERED")]
        public int Rostered { get; set; }

        [Column("Position")]
        public string Position { get; set; }

        [Column("MiLB")]
        public string MiLB { get; set; }
    }
}
