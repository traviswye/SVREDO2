using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using SharpVizAPI.Models;

namespace SharpVizAPI.Models.MLmodels
{
    public class ML_Ballparks
    {
        [Key]
        public int BallparkID { get; set; }

        [Required]
        [StringLength(100)]
        public string Name { get; set; }

        [Required]
        [StringLength(100)]
        public string Location { get; set; }

        public int Capacity { get; set; }

        [StringLength(500)]
        public string FieldDimensions { get; set; } // JSON string representing field dimensions

        public int Altitude { get; set; }

        [StringLength(1000)]
        public string ParkFactors { get; set; } // JSON string representing park factors

        [StringLength(100)]
        public string HomeTeam { get; set; } // New column for HomeTeam

        [StringLength(50)]
        public string RoofType { get; set; } // New column for RoofType

        public int Direction { get; set; } // New column for Direction

        public int ParkFactorsID { get; set; } // New FK to ParkFactors table

    }

}
