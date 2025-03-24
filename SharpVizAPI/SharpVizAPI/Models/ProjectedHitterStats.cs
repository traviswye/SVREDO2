using System;
using System.ComponentModel.DataAnnotations.Schema;
using System.ComponentModel.DataAnnotations;

namespace SharpVizAPI.Models
{
    [Table("projectedHitterStats", Schema = "dbo")]
    public class ProjectedHitterStats
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

        [Column("PA")]
        public int PA { get; set; }

        [Column("AB")]
        public int AB { get; set; }

        [Column("R")]
        public int R { get; set; }

        [Column("HR")]
        public int HR { get; set; }

        [Column("RBI")]
        public int RBI { get; set; }

        [Column("SB")]
        public int SB { get; set; }

        [Column("AVG")]
        //[Column(TypeName = "decimal(4, 3)")]
        public decimal AVG { get; set; }

        [Column("OBP")]
        //[Column(TypeName = "decimal(4, 3)")]
        public decimal OBP { get; set; }

        [Column("H")]
        public int H { get; set; }

        [Column("2B")]
        public int Doubles { get; set; }

        [Column("3B")]
        public int Triples { get; set; }

        [Column("BB")]
        public int BB { get; set; }

        [Column("SO")]
        public int SO { get; set; }

        [Column("SLG")]
        //[Column(TypeName = "decimal(4, 3)")]
        public decimal SLG { get; set; }

        [Column("OPS")]
        //[Column(TypeName = "decimal(4, 3)")]
        public decimal OPS { get; set; }

        [Column("ROSTERED")]
        public int Rostered { get; set; }

        [Column("Position")]
        public string Position { get; set; }

        [Column("MiLB")]
        public string MiLB { get; set; }
    }
}
