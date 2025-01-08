namespace SharpVizAPI.Models.MLmodels
{
    public class ML_Weather
    {
        public int WeatherID { get; set; }
        public int GameID { get; set; }
        public float Temperature { get; set; }
        public float Humidity { get; set; }
        public float WindSpeed { get; set; }
        public string WindDirection { get; set; } // String or representation
        public float Precipitation { get; set; } // Default is 0

        public ML_Games Game { get; set; } // Navigation property
    }

}
