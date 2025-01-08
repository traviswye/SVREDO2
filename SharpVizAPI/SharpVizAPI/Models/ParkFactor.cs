using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace SharpVizAPI.Models
{
    public class ParkFactor
    {
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public int Id { get; set; }
        public string Team { get; set; }
        public string Venue { get; set; }
        public int Year { get; set; }
        public int ParkFactorRating { get; set; }
        public int wOBACon { get; set; }
        public int BACON { get; set; }
        public int R { get; set; }
        public int OBP { get; set; }
        public int H { get; set; }

        [Column("1B")]
        public int OneB { get; set; }

        [Column("2B")]
        public int TwoB { get; set; }

        [Column("3B")]
        public int ThreeB { get; set; }
        public int HR { get; set; }
        public int BB { get; set; }
        public int SO { get; set; }
        public string zipcode { get; set; }
        public string RoofType { get; set; }

        public double Latitude { get; set; }  // Existing Latitude property
        public double Longitude { get; set; } // Existing Longitude property
        public double Direction { get; set; } // New Direction property

        public int Capacity { get; set; }

        [StringLength(500)]
        public string FieldDimensions { get; set; } // JSON string representing field dimensions

        public int Altitude { get; set; }


        // Parameterless constructor for EF
        public ParkFactor()
        {
        }

        // Constructor to initialize all properties
        public ParkFactor(
            string team,
            string venue,
            int year,
            int parkFactorRating,
            int wOBACon,
            int bacon,
            int r,
            int obp,
            int h,
            int oneB,
            int twoB,
            int threeB,
            int hr,
            int bb,
            int so,
            string zipcode,
            string roofType,
            double latitude,
            double longitude,
            double direction,
            string fieldDimensions,
            int capacity,
            int altitude) // Added direction to constructor
        {
            Team = team;
            Venue = venue;
            Year = year;
            ParkFactorRating = parkFactorRating;
            this.wOBACon = wOBACon;
            BACON = bacon;
            R = r;
            OBP = obp;
            H = h;
            OneB = oneB;
            TwoB = twoB;
            ThreeB = threeB;
            HR = hr;
            BB = bb;
            SO = so;
            this.zipcode = zipcode;
            RoofType = roofType;
            Latitude = latitude;
            Longitude = longitude;
            Direction = direction; // Set direction
            Altitude = altitude;
            Capacity = capacity;
            Altitude = altitude;
        }
    }
}
