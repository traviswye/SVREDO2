using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace SharpVizApi.Models
{
    [Table("DKPlayerPools")]
    public class DKPlayerPool
    {
        [Key]
        public int Id { get; set; }

        [Required]
        public int DraftGroupId { get; set; }

        [Required]
        public int PlayerDkId { get; set; }

        [Required]
        [StringLength(100)]
        public string FullName { get; set; }

        [Required]
        [StringLength(10)]
        public string Position { get; set; }

        [Required]
        public int Salary { get; set; }

        [Required]
        public int GameId { get; set; }

        [Required]
        [StringLength(50)]
        public string Game { get; set; }

        [Required]
        public DateTime GameStart { get; set; }

        [Required]
        [StringLength(10)]
        public string Team { get; set; }

        [Column(TypeName = "decimal(5,1)")]
        public decimal? DKppg { get; set; }

        [StringLength(10)]
        public string OppRank { get; set; }
        [StringLength(20)]
        public string Status { get; set; }

        [Required]
        public DateTime DateAdded { get; set; }
    }

    // DTO for bulk insert request
    public class DKPlayerPoolBatchRequest
    {
        [Required]
        public int DraftGroupId { get; set; }

        [Required]
        public List<DKPlayerPoolInput> Players { get; set; }
    }

    public class DKPlayerPoolInput
    {
        public int PlayerDkId { get; set; }
        public string FullName { get; set; }
        public string Position { get; set; }
        public int Salary { get; set; }
        public int GameId { get; set; }
        public string Game { get; set; }
        public DateTime GameStart { get; set; }
        public string Team { get; set; }
        public decimal? DKppg { get; set; }
        public string OppRank { get; set; }
        public string Status { get; set; }
    }
}