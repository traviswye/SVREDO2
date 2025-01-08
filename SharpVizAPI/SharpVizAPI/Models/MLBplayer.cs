using System.ComponentModel.DataAnnotations;

namespace SharpVizAPI.Models
{
    public class MLBplayer
    {
        [Key]
        public string bbrefId { get; set; }
        public string FullName { get; set; }
        public string CurrentTeam { get; set; }
    }

}
