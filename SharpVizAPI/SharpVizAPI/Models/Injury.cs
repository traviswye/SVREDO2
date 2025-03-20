using System;
using System.ComponentModel.DataAnnotations;

namespace SharpVizAPI.Models
{
    public class Injury
    {
        [Key]
        public string bbrefId { get; set; } // Primary Key

        public string InjuryDescription { get; set; }

        public string CurrentTeam { get; set; }

        [Required]
        public DateTime Date { get; set; } // Use "Date" instead of "InjuryDate"

        public int Year { get; set; }
    }
}
