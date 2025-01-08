
    namespace SharpVizAPI.Models
    {
        public class PitcherRecency
        {
            public string Pitcher { get; set; }  // Maps to "pitcher" in the response
            public decimal bA_Trend { get; set; }  // Maps to "bA_Trend" in the response
            public decimal obP_Trend { get; set; }  // Maps to "obP_Trend" in the response
            public decimal slG_Trend { get; set; }  // Maps to "slG_Trend" in the response
            public decimal BAbip_Trend { get; set; }  // Maps to "BAbip_Trend" in the response
            public string PerformanceStatus { get; set; }  // Maps to "performanceStatus"
            public string Message { get; set; }  // Maps to "message"
        }
    }


