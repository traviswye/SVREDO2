public class GamePreviewDto
{
    public DateTime Date { get; set; }
    public string Time { get; set; }
    public string HomeTeam { get; set; }
    public string AwayTeam { get; set; }
    public string HomePitcher { get; set; }
    public string AwayPitcher { get; set; }
    public string PreviewLink { get; set; }

    // Weather-related fields
    public double Temperature { get; set; }
    public double Humidity { get; set; }
    public double RainProbability { get; set; }
    public double WindSpeed { get; set; }
    public double WindDirection { get; set; }
    public double RelativeWindDirection { get; set; }
    public string WindDescription { get; set; } = string.Empty;

    // New Weather-related fields
    public double RainProb2hr { get; set; }
    public double TotalRain { get; set; }
    public double WindGusts { get; set; }
}
