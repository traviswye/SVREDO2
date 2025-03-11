using System.ComponentModel.DataAnnotations;
using System;

namespace SharpVizAPI.Models
{
    public class PlayerIDMapping
    {
        [Key]
        public int Id { get; set; }
        public int PlayerDkId { get; set; }
        public string BbrefId { get; set; }
        public string FullName { get; set; }
        public string Team { get; set; }
        public string Position { get; set; }
        public int Year { get; set; }
        public DateTime DateAdded { get; set; }
        public DateTime? LastUpdated { get; set; }
    }
}
