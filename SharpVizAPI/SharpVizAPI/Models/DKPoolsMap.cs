using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace SharpVizApi.Models
{
    [Table("DKPoolsMap")]
    public class DKPoolsMap
    {
        [Key]
        public int Id { get; set; }

        [Required]
        [StringLength(10)]
        public string Sport { get; set; }

        [Required]
        public int DraftGroupId { get; set; }

        [Required]
        [Column(TypeName = "date")]
        public DateTime Date { get; set; }

        [Required]
        [StringLength(20)]
        public string StartTime { get; set; }

        [Required]
        [StringLength(20)]
        public string GameType { get; set; }

        [Required]
        public DateTime DateAdded { get; set; }
    }

    // DTO for creating new pool map entry
    public class DKPoolsMapInput
    {
        [Required]
        public string Sport { get; set; }

        [Required]
        public int DraftGroupId { get; set; }

        [Required]
        public DateTime Date { get; set; }

        [Required]
        public string StartTime { get; set; }

        [Required]
        public string GameType { get; set; }
    }
}