namespace SharpVizAPI.DTO
{
    public class HitterStatsDto
    {
        public string bbrefId { get; set; }
        public string Bats { get; set; }

        public double OBP { get; set; }
        public double BA { get; set; }
        public double SLG { get; set; }
        public double KPercentage { get; set; }
        public double BBPercentage { get; set; }
        public double SinglePercentage { get; set; }
        public double DoublePercentage { get; set; }
        public double TriplePercentage { get; set; }
        public double homeRunPercentage { get; set; }


        // Add other fields as necessary
    }

}
