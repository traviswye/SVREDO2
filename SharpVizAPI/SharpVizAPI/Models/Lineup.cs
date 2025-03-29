using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace SharpVizAPI.Models
{
    public class Lineup
    {
        [Key]
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public int Id { get; set; }  // Auto-incremented by the database

        public string Team { get; set; }
        public int GameNumber { get; set; }
        public DateTime Date { get; set; }
        public string Opponent { get; set; }
        public string OpposingSP { get; set; }
        public bool LHP { get; set; }
        public string Result { get; set; }  // 'W' or 'L'
        public string Score { get; set; }
        public string? Batting1st { get; set; }  // Holds the bbrefId of the hitter
        public string? Batting2nd { get; set; }
        public string? Batting3rd { get; set; }
        public string? Batting4th { get; set; }
        public string? Batting5th { get; set; }
        public string? Batting6th { get; set; }
        public string? Batting7th { get; set; }
        public string? Batting8th { get; set; }
        public string? Batting9th { get; set; }
        public int Year { get; set; }
    }

    public class LineupPrediction
    {
        [Key]
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public int Id { get; set; }

        public string Team { get; set; }
        public int GameNumber { get; set; }
        public DateTime Date { get; set; }
        public string Opponent { get; set; }
        public string OpposingSP { get; set; }
        public bool LHP { get; set; }
        public string Batting1st { get; set; }
        public string Batting2nd { get; set; }
        public string Batting3rd { get; set; }
        public string Batting4th { get; set; }
        public string Batting5th { get; set; }
        public string Batting6th { get; set; }
        public string Batting7th { get; set; }
        public string Batting8th { get; set; }
        public string Batting9th { get; set; }

        // Foreign key
        public int GamePreviewId { get; set; }
        [ForeignKey("GamePreviewId")]
        public GamePreview GamePreview { get; set; }
    }

    public class ActualLineup
    {
        [Key]
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public int Id { get; set; }

        public string Team { get; set; }
        public int GameNumber { get; set; }
        public DateTime Date { get; set; }
        public string Opponent { get; set; }
        public string OpposingSP { get; set; }
        public bool LHP { get; set; }
        public string Batting1st { get; set; }
        public string Batting2nd { get; set; }
        public string Batting3rd { get; set; }
        public string Batting4th { get; set; }
        public string Batting5th { get; set; }
        public string Batting6th { get; set; }
        public string Batting7th { get; set; }
        public string Batting8th { get; set; }
        public string Batting9th { get; set; }

        // Foreign key
        public int GamePreviewId { get; set; }
        [ForeignKey("GamePreviewId")]
        public GamePreview GamePreview { get; set; }

        public bool FetchedLogs { get; set; }
    }
}
