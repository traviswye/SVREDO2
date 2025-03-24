using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace SharpVizAPI.Models
{
    public class OpeningDayProjectedLineupModel
    {
        [Key]
        public int Id { get; set; }

        public int Year { get; set; }

        [StringLength(3)]
        public string Team { get; set; }

        [StringLength(8)]
        public string Batting1st { get; set; }

        [StringLength(8)]
        public string Batting2nd { get; set; }

        [StringLength(8)]
        public string Batting3rd { get; set; }

        [StringLength(8)]
        public string Batting4th { get; set; }

        [StringLength(8)]
        public string Batting5th { get; set; }

        [StringLength(8)]
        public string Batting6th { get; set; }

        [StringLength(8)]
        public string Batting7th { get; set; }

        [StringLength(8)]
        public string Batting8th { get; set; }

        [StringLength(8)]
        public string Batting9th { get; set; }

        [StringLength(8)]
        public string Bench1 { get; set; }

        [StringLength(8)]
        public string Bench2 { get; set; }

        [StringLength(8)]
        public string Bench3 { get; set; }

        [StringLength(8)]
        public string Bench4 { get; set; }
    }
}
