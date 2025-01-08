// Models/ClassificationResult.cs
namespace SharpVizAPI.Models
{
    public class ClassificationResult
    {
        public List<string> Strong { get; set; } = new List<string>();
        public List<string> Slight { get; set; } = new List<string>();
        public List<string> Weak { get; set; } = new List<string>();
        public List<string> Avoid { get; set; } = new List<string>();
        public List<string> NoResults { get; set; } = new List<string>();
    }
}
