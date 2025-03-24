using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace SharpVizAPI.Models
{
    public class OpeningDayProjectedRotationModel
    {
        [Key]
        public int Id { get; set; }

        public int Year { get; set; }

        [StringLength(3)]
        public string Team { get; set; }

        [StringLength(8)]
        public string SP1 { get; set; }

        [StringLength(8)]
        public string SP2 { get; set; }

        [StringLength(8)]
        public string SP3 { get; set; }

        [StringLength(8)]
        public string SP4 { get; set; }

        [StringLength(8)]
        public string SP5 { get; set; }

        [StringLength(8)]
        public string Alt1 { get; set; }

        [StringLength(8)]
        public string Alt2 { get; set; }

        [StringLength(8)]
        public string Alt3 { get; set; }
    }
}
