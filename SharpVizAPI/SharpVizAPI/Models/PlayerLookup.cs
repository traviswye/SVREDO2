using System.ComponentModel.DataAnnotations;

namespace SharpVizAPI.Models
{


        public class PlayerLookup
        {
            [Key]
            public string BbrefId { get; set; }

            [Required]
            public int BsID { get; set; }

            [Required]
            [MaxLength(50)]
            public string FirstName { get; set; }

            [Required]
            [MaxLength(50)]
            public string LastName { get; set; }

            [Required]
            [MaxLength(100)]
            public string FullName { get; set; }

            [Required]
            [MaxLength(10)]
            public string Team { get; set; }

            [Required]
            public int Year { get; set; }
        }
    }


