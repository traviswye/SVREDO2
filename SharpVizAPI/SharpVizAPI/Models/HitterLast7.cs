using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace SharpVizAPI.Models{
    public class HitterLast7
{
    [Key]
    public int Id { get; set; }

    [ForeignKey("Hitters")]
    [StringLength(50)]
    public string BbrefId { get; set; }  // Foreign key reference to the Hitters table

    [Required]
    public DateTime DateUpdated { get; set; }

    [Required]
    [StringLength(10)]
    public string Team { get; set; }

    [Required]
    [StringLength(50)]
    public string Pos { get; set; }

    [Required]
    [StringLength(50)]
    public string Name { get; set; }

    [Required]
    public int AB { get; set; }

    [Required]
    public int R { get; set; }

    [Required]
    public int HR { get; set; }

    [Required]
    public int RBI { get; set; }

    [Required]
    public int SB { get; set; }

    [Required]
    public double AVG { get; set; }

    [Required]
    public double OBP { get; set; }

    [Required]
    public int H { get; set; }

    [Required]
    [Column("2B")]
    public int TwoB { get; set; }  // Column name "2B" as _2B in C#

    [Required]
    [Column("3B")]
    public int ThreeB { get; set; }  // Column name "3B" as _3B in C#

    [Required]
    public int BB { get; set; }

    [Required]
    public int K { get; set; }

    [Required]
    public double SLG { get; set; }

    [Required]
    public double OPS { get; set; }

    [Required]
    [Column(TypeName = "decimal(5,2)")]
    public decimal ROSTERED { get; set; }
}

}
