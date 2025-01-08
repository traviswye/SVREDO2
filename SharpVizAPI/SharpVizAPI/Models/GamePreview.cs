public class GamePreview
{
    public int Id { get; set; }
    public DateTime Date { get; set; }
    public string Time { get; set; } = string.Empty;
    public string HomeTeam { get; set; } = string.Empty;
    public string AwayTeam { get; set; } = string.Empty;
    public string Venue { get; set; } = string.Empty;
    public string HomePitcher { get; set; } = string.Empty;
    public string AwayPitcher { get; set; } = string.Empty;
    public string PreviewLink { get; set; } = string.Empty;
    public DateTime DateModified { get; set; } = DateTime.UtcNow;

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
    public double totalRain { get; set; }
    public double WindGusts { get; set; }
}
