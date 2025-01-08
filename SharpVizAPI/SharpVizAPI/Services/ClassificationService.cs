using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using SharpVizAPI.Data;
using SharpVizAPI.Models;

namespace SharpVizAPI.Services
{
    public class ClassificationService : IClassificationService
    {
        private readonly NrfidbContext _context;
        private readonly HttpClient _httpClient;
        private readonly ILogger<ClassificationService> _logger;

        public ClassificationService(NrfidbContext context, HttpClient httpClient, ILogger<ClassificationService> logger)
        {
            _context = context;
            _httpClient = httpClient;
            _logger = logger;
        }

        private async Task<List<GamePreview>> GetGamePreviewsAsync(string date)
        {
            string shortDate = DateTime.ParseExact(date, "yyyy-MM-dd", CultureInfo.InvariantCulture).ToString("yy-MM-dd");
            var response = await _httpClient.GetAsync($"https://localhost:44346/api/GamePreviews/{shortDate}");

            if (!response.IsSuccessStatusCode)
            {
                throw new Exception("Failed to retrieve game previews data.");
            }

            return await response.Content.ReadFromJsonAsync<List<GamePreview>>();
        }

        public async Task<ClassificationResult> ClassificationByPitchingAdvAsync(string date)
        {
            var result = new ClassificationResult();
            var response = await _httpClient.GetAsync($"https://localhost:44346/api/Blending/startingPitcherAdvantage?date={date}");

            if (!response.IsSuccessStatusCode)
            {
                throw new Exception("Failed to retrieve pitcher advantage data.");
            }

            var advantageData = await response.Content.ReadFromJsonAsync<List<StartingPitcherAdvantage>>();
            if (advantageData == null || !advantageData.Any())
            {
                return result;
            }

            foreach (var game in advantageData)
            {
                string gameDetails = game.Game;
                string advantageInfo = game.Advantage;

                if (advantageInfo.Contains("Not enough data to determine advantage"))
                {
                    result.NoResults.Add(gameDetails);
                    continue;
                }

                var match = Regex.Match(advantageInfo, @"by ([\d.]+)");
                if (!match.Success) continue;

                double advantageScore = double.Parse(match.Groups[1].Value);

                string homeTeam = gameDetails.Split(" vs ")[0];
                string awayTeam = gameDetails.Split(" vs ")[1];

                bool isHomeAdvantage = advantageInfo.Contains("(Home)");
                string advantagedTeam = isHomeAdvantage ? homeTeam : awayTeam;

                ClassifyTeamByAdvantage(result, advantagedTeam, advantageScore);
            }

            return result;
        }

        private void ClassifyTeamByAdvantage(ClassificationResult result, string team, double advantageScore)
        {
            if (advantageScore >= 300)
            {
                result.Strong.Add(team);
            }
            else if (advantageScore >= 200)
            {
                result.Slight.Add(team);
            }
            else if (advantageScore >= 100)
            {
                result.Weak.Add(team);
            }
            else
            {
                result.Avoid.Add(team);
            }
        }


        public async Task<object> ClassificationByAllFactorsAsync(string date)
        {
            var initialClassification = await ClassificationByPitchingAdvAsync(date);

            var gameOddsResponse = await _httpClient.GetAsync($"https://localhost:44346/api/GameOdds/date/{date}");
            if (!gameOddsResponse.IsSuccessStatusCode)
            {
                throw new Exception("Failed to retrieve game odds.");
            }

            var gameOdds = await gameOddsResponse.Content.ReadFromJsonAsync<List<GameOdds>>();

            // Adjust for odds and move teams from Avoid to Weak if odds are positive
            foreach (var team in initialClassification.Avoid.ToList())
            {
                var oddsData = gameOdds.FirstOrDefault(g => g.HomeTeam == team || g.AwayTeam == team);
                if (oddsData != null)
                {
                    bool isHome = oddsData.HomeTeam == team;
                    var homeOddsAvg = (int)((oddsData.FanduelHomeOdds ?? 0 + oddsData.DraftkingsHomeOdds ?? 0 + oddsData.BetmgmHomeOdds ?? 0) / 3);
                    var awayOddsAvg = (int)((oddsData.FanduelAwayOdds ?? 0 + oddsData.DraftkingsAwayOdds ?? 0 + oddsData.BetmgmAwayOdds ?? 0) / 3);
                    var oddsToUse = isHome ? homeOddsAvg : awayOddsAvg;

                    if (oddsToUse > 0)
                    {
                        initialClassification.Avoid.Remove(team);
                        initialClassification.Weak.Add(team);
                    }
                }
            }

            // Build game details list
            var gameDetailsList = await BuildGameDetailsListAsync(date);

            // Initialize confidence scores from initial classification
            var confidenceScores = new Dictionary<string, double>();
            foreach (var team in initialClassification.Strong)
                confidenceScores[team] = 100.0;
            foreach (var team in initialClassification.Slight)
                confidenceScores[team] = 80.0;
            foreach (var team in initialClassification.Weak)
                confidenceScores[team] = 60.0;
            foreach (var team in initialClassification.Avoid)
                confidenceScores[team] = 25.0;

            // Iterate through each game and adjust confidence scores based on game details
            foreach (var game in gameDetailsList)
            {
                AdjustConfidenceForTeam(confidenceScores, game, initialClassification.Strong.Concat(initialClassification.Slight).Concat(initialClassification.Weak).Concat(initialClassification.Avoid));
            }

            var finalResult = new
            {
                Strong = confidenceScores.Where(kv => kv.Value > 90)
                                          .Select(kv => new { Team = kv.Key, Confidence = kv.Value })
                                          .ToList(),
                Slight = confidenceScores.Where(kv => kv.Value > 70 && kv.Value <= 90)
                                          .Select(kv => new { Team = kv.Key, Confidence = kv.Value })
                                          .ToList(),
                Weak = confidenceScores.Where(kv => kv.Value > 50 && kv.Value <= 70)
                                          .Select(kv => new { Team = kv.Key, Confidence = kv.Value })
                                          .ToList(),
                Avoid = confidenceScores.Where(kv => kv.Value <= 50)
                                          .Select(kv => new { Team = kv.Key, Confidence = kv.Value })
                                          .ToList(),
                NoResults = initialClassification.NoResults
            };

            return finalResult;
        }

        private decimal ExtractDeltaFromMessage(string message)
        {
            var match = Regex.Match(message, @"([0-9]+\.?[0-9]*)%");
            if (match.Success && decimal.TryParse(match.Groups[1].Value, out decimal result))
            {
                return result / 100; // Convert percentage to decimal
            }
            return 0;
        }


        private async Task<List<GameDetails>> BuildGameDetailsListAsync(string date)
        {
            _logger.LogInformation($"Building game details list for date {date}.");

            var gamePreviews = await GetGamePreviewsAsync(date);

            // Fetch the pitcher trends data and deserialize directly into a list of PitcherRecency objects
            var pitcherTrendsResponse = await _httpClient.GetAsync($"https://localhost:44346/api/Blending/todaysSPHistoryVsRecency?date={date}");
            if (!pitcherTrendsResponse.IsSuccessStatusCode)
            {
                _logger.LogError($"Failed to retrieve pitcher trends data for date {date}.");
                throw new Exception("Failed to retrieve pitcher trends data.");
            }

            // Deserialize the response content into a strongly typed list of PitcherRecency
            var pitcherTrends = await pitcherTrendsResponse.Content.ReadFromJsonAsync<List<PitcherRecency>>();

            var lineupScores = await GetLineupScoresAsync(date, gamePreviews);


            var teamRecords = await GetTeamRecordsAsync();

            var gameDetailsList = new List<GameDetails>();

            // Iterate through game previews and match trends
            foreach (var game in gamePreviews)
            {
                var homePitcherId = game.HomePitcher;
                var awayPitcherId = game.AwayPitcher;

                // Get the home pitcher trend, and set to "N/A" if no data is available
                var homePitcherTrend = pitcherTrends.FirstOrDefault(p => p.Pitcher == homePitcherId);
                var homeSPTrend = homePitcherTrend != null && homePitcherTrend.Message != "No data available"
                                  ? homePitcherTrend.PerformanceStatus
                                  : "N/A";

                // Get the away pitcher trend, and set to "N/A" if no data is available
                var awayPitcherTrend = pitcherTrends.FirstOrDefault(p => p.Pitcher == awayPitcherId);
                var awaySPTrend = awayPitcherTrend != null && awayPitcherTrend.Message != "No data available"
                                  ? awayPitcherTrend.PerformanceStatus
                                  : "N/A";

                var homeSPThrows = await GetPitcherThrowsAsync(homePitcherId);
                var awaySPThrows = await GetPitcherThrowsAsync(awayPitcherId);
                
               var homeLineupScore = lineupScores.ContainsKey(game.HomeTeam) ? lineupScores[game.HomeTeam].AvgScore : 0;
                var awayLineupScore = lineupScores.ContainsKey(game.AwayTeam) ? lineupScores[game.AwayTeam].AvgScore : 0;
                _logger.LogInformation($"finding lineup socres for{game.HomeTeam}");
                _logger.LogInformation($"finding lineup socres for{game.AwayTeam}");
                var homeRecordVsSP = teamRecords.ContainsKey(game.HomeTeam) ?
                    (awaySPThrows == "RHP" ? teamRecords[game.HomeTeam].VsRHP : teamRecords[game.HomeTeam].VsLHP) : "N/A";

                var awayRecordVsSP = teamRecords.ContainsKey(game.AwayTeam) ?
                    (homeSPThrows == "RHP" ? teamRecords[game.AwayTeam].VsRHP : teamRecords[game.AwayTeam].VsLHP) : "N/A";

                gameDetailsList.Add(new GameDetails
                {
                    HomeTeam = game.HomeTeam,
                    AwayTeam = game.AwayTeam,
                    HomeSP = game.HomePitcher,
                    AwaySP = game.AwayPitcher,
                    HomeSPThrows = homeSPThrows,
                    AwaySPThrows = awaySPThrows,
                    HomeSPTrend = homeSPTrend,
                    AwaySPTrend = awaySPTrend,
                    HomeLineupScoreAvg = homeLineupScore,
                    AwayLineupScoreAvg = awayLineupScore,
                    HomeRecordVsOpposingSPThrows = homeRecordVsSP,
                    AwayRecordVsOpposingSPThrows = awayRecordVsSP,
                    HomeRecordHome = teamRecords.ContainsKey(game.HomeTeam) ? teamRecords[game.HomeTeam].HomeRec : "N/A",
                    AwayRecordAway = teamRecords.ContainsKey(game.AwayTeam) ? teamRecords[game.AwayTeam].AwayRec : "N/A"
                });
            }

            _logger.LogInformation($"Completed building game details list for date {date}.");

            // Log the game details list for verification
            foreach (var gameDetails in gameDetailsList)
            {
                _logger.LogInformation("Game Details:");
                _logger.LogInformation($"Home Team: {gameDetails.HomeTeam}, Away Team: {gameDetails.AwayTeam}");
                _logger.LogInformation($"Home SP: {gameDetails.HomeSP}, Away SP: {gameDetails.AwaySP}");
                _logger.LogInformation($"Home SP Throws: {gameDetails.HomeSPThrows}, Away SP Throws: {gameDetails.AwaySPThrows}");
                _logger.LogInformation($"Home SP Trend: {gameDetails.HomeSPTrend}, Away SP Trend: {gameDetails.AwaySPTrend}");
                _logger.LogInformation($"Home Lineup Avg Score: {gameDetails.HomeLineupScoreAvg}, Away Lineup Avg Score: {gameDetails.AwayLineupScoreAvg}");
                _logger.LogInformation($"Home Record vs Opposing SP Throws: {gameDetails.HomeRecordVsOpposingSPThrows}, Away Record vs Opposing SP Throws: {gameDetails.AwayRecordVsOpposingSPThrows}");
                _logger.LogInformation($"Home Record (Home): {gameDetails.HomeRecordHome}, Away Record (Away): {gameDetails.AwayRecordAway}");
                _logger.LogInformation("--------------------------------------------------");
            }
            return gameDetailsList;
        }


        private async Task<Dictionary<string, LineupScore>> GetLineupScoresAsync(string date, List<GamePreview> gamePreviews)
        {
            var actualLineupsResponse = await _httpClient.GetAsync($"https://localhost:44346/api/Lineups/Actual/{date}");
            var actualLineups = actualLineupsResponse.IsSuccessStatusCode
                                ? await actualLineupsResponse.Content.ReadFromJsonAsync<List<ActualLineup>>()
                                : new List<ActualLineup>();

            var predictedLineupsResponse = await _httpClient.GetAsync($"https://localhost:44346/api/Lineups/Predictions/date/{date}");
            var predictedLineups = predictedLineupsResponse.IsSuccessStatusCode
                                   ? await predictedLineupsResponse.Content.ReadFromJsonAsync<List<LineupPrediction>>()
                                   : new List<LineupPrediction>();

            var actualLineupsDict = actualLineups.ToDictionary(lineup => lineup.Team, lineup => ConvertToLineup(lineup));
            var predictedLineupsDict = predictedLineups.ToDictionary(lineup => lineup.Team, lineup => ConvertToLineup(lineup));

            var outperformersResponse = await _httpClient.GetAsync($"https://localhost:44346/api/HitterLast7/outperformers/{date}");
            var outperformers = outperformersResponse.IsSuccessStatusCode
                                ? await outperformersResponse.Content.ReadFromJsonAsync<List<Outperformer>>()
                                : new List<Outperformer>();

            _logger.LogInformation($"Actual lineups response: {actualLineupsResponse.StatusCode}");
            _logger.LogInformation($"Predicted lineups response: {predictedLineupsResponse.StatusCode}");
            _logger.LogInformation($"Outperformers response: {outperformersResponse.StatusCode}");

            var playerScores = outperformers.ToDictionary(o => o.bbrefId.ToLower().Trim(), o => o.OutperformanceScore);

            var teamScores = new Dictionary<string, LineupScore>();

            foreach (var game in gamePreviews)
            {
                _logger.LogInformation($"Processing game: HomeTeam={game.HomeTeam}, AwayTeam={game.AwayTeam}");

                foreach (var team in new[] { game.HomeTeam, game.AwayTeam })
                {
                    Lineup lineup = actualLineupsDict.ContainsKey(team)
                                    ? actualLineupsDict[team]
                                    : predictedLineupsDict.ContainsKey(team) ? predictedLineupsDict[team] : null;

                    if (lineup == null)
                    {
                        // Log missing lineup for debugging
                        _logger.LogInformation($"No lineup found for team: {team}");
                        continue;
                    }

                    var suffixes = new[] { "st", "nd", "rd", "th" };

                    var battingOrder = Enumerable.Range(1, 9)
                        .Select(i =>
                        {
                            string suffix = (i == 1) ? "st" : (i == 2) ? "nd" : (i == 3) ? "rd" : "th";
                            return lineup.GetType().GetProperty($"Batting{i}{suffix}")?.GetValue(lineup)?.ToString()?.ToLower().Trim();
                        })
                        .Where(playerId => !string.IsNullOrEmpty(playerId))
                        .ToList();


                    if (!battingOrder.Any())
                    {
                        Console.WriteLine($"No valid players in batting order for team: {team}");
                        continue;
                    }

                    double totalScore = 0;
                    int validPlayerCount = 0;

                    foreach (var playerId in battingOrder)
                    {
                        if (playerScores.TryGetValue(playerId, out double score))
                        {
                            totalScore += score;
                            validPlayerCount++;
                        }
                        else
                        {
                            // Log unmatched player for debugging
                            _logger.LogInformation($"No score found for playerId: {playerId} in team {team}");
                        }
                    }

                    decimal totalScoreDecimal = (decimal)totalScore;
                    decimal avgScore = validPlayerCount > 0 ? totalScoreDecimal / validPlayerCount : 0;

                    teamScores[team] = new LineupScore
                    {
                        TotalScore = totalScoreDecimal,
                        AvgScore = avgScore
                    };

                    // Log team score for debugging
                    _logger.LogInformation($"Team: {team}, TotalScore: {totalScoreDecimal}, AvgScore: {avgScore}");
                }
            }

            return teamScores;
        }


        private Lineup ConvertToLineup(ActualLineup actualLineup)
        {
            return new Lineup
            {
                Team = actualLineup.Team,
                GameNumber = actualLineup.GameNumber,
                Date = actualLineup.Date,
                Opponent = actualLineup.Opponent,
                OpposingSP = actualLineup.OpposingSP,
                LHP = actualLineup.LHP,
                Batting1st = actualLineup.Batting1st,
                Batting2nd = actualLineup.Batting2nd,
                Batting3rd = actualLineup.Batting3rd,
                Batting4th = actualLineup.Batting4th,
                Batting5th = actualLineup.Batting5th,
                Batting6th = actualLineup.Batting6th,
                Batting7th = actualLineup.Batting7th,
                Batting8th = actualLineup.Batting8th,
                Batting9th = actualLineup.Batting9th
            };
        }

        private Lineup ConvertToLineup(LineupPrediction predictedLineup)
        {
            return new Lineup
            {
                Team = predictedLineup.Team,
                GameNumber = predictedLineup.GameNumber,
                Date = predictedLineup.Date,
                Opponent = predictedLineup.Opponent,
                OpposingSP = predictedLineup.OpposingSP,
                LHP = predictedLineup.LHP,
                Batting1st = predictedLineup.Batting1st,
                Batting2nd = predictedLineup.Batting2nd,
                Batting3rd = predictedLineup.Batting3rd,
                Batting4th = predictedLineup.Batting4th,
                Batting5th = predictedLineup.Batting5th,
                Batting6th = predictedLineup.Batting6th,
                Batting7th = predictedLineup.Batting7th,
                Batting8th = predictedLineup.Batting8th,
                Batting9th = predictedLineup.Batting9th
            };
        }

        private async Task<Dictionary<string, TeamRecSplits>> GetTeamRecordsAsync()
        {
            var teamRecords = await _context.TeamRecSplits.ToListAsync();
            return teamRecords.ToDictionary(record => record.Team, record => record);
        }

        private async Task<string> GetPitcherThrowsAsync(string bbrefId)
        {
            var response = await _httpClient.GetAsync($"https://localhost:44346/api/Pitchers/{bbrefId}");
            if (response.IsSuccessStatusCode)
            {
                var pitcherDetails = await response.Content.ReadFromJsonAsync<Pitcher>();
                if (!string.IsNullOrEmpty(pitcherDetails?.Throws))
                {
                    return pitcherDetails.Throws;
                }
            }

            var fallbackRecord = await _context.PitcherPlatoonAndTrackRecord
                                    .FirstOrDefaultAsync(p => p.BbrefID == bbrefId);

            if (fallbackRecord != null)
            {
                return "RHP"; // Assuming fallback is RHP
            }

            return "RHP"; // Default if all else fails
        }

        // Helper function to adjust confidence for a team based on the game details
        private void AdjustConfidenceForTeam(Dictionary<string, double> confidenceScores, GameDetails game, IEnumerable<string> classifiedTeams)
        {
            // If the classified team is either the home or away team, we perform the adjustments
            foreach (var team in classifiedTeams)
            {
                if (game.HomeTeam == team || game.AwayTeam == team)
                {
                    bool isHomeTeam = game.HomeTeam == team;

                    // Adjust based on pitcher trends
                    if (game.HomeSPTrend == "HOT" && game.AwaySPTrend == "COLD")
                    {
                        AdjustConfidence(confidenceScores, game.HomeTeam, 10);
                        AdjustConfidence(confidenceScores, game.AwayTeam, -10);
                    }
                    else if (game.HomeSPTrend == "COLD" && game.AwaySPTrend == "HOT")
                    {
                        AdjustConfidence(confidenceScores, game.HomeTeam, -10);
                        AdjustConfidence(confidenceScores, game.AwayTeam, 10);
                    }
                    if (game.HomeSPTrend == "HOT" && game.AwaySPTrend == "CONSISTENT")
                    {
                        AdjustConfidence(confidenceScores, game.HomeTeam, 5);
                        AdjustConfidence(confidenceScores, game.AwayTeam, -5);
                    }
                    else if (game.HomeSPTrend == "CONSISTENT" && game.AwaySPTrend == "HOT")
                    {
                        AdjustConfidence(confidenceScores, game.HomeTeam, -5);
                        AdjustConfidence(confidenceScores, game.AwayTeam, 5);
                    }
                    if (game.HomeSPTrend == "COLD" && game.AwaySPTrend == "CONSISTENT")
                    {
                        AdjustConfidence(confidenceScores, game.HomeTeam, -5);
                        AdjustConfidence(confidenceScores, game.AwayTeam, 5);
                    }
                    else if (game.HomeSPTrend == "CONSISTENT" && game.AwaySPTrend == "COLD")
                    {
                        AdjustConfidence(confidenceScores, game.HomeTeam, 5);
                        AdjustConfidence(confidenceScores, game.AwayTeam, -5);
                    }

                    // Adjust based on lineup scores
                    if (game.HomeLineupScoreAvg > game.AwayLineupScoreAvg)
                    {
                        AdjustConfidence(confidenceScores, game.HomeTeam, 5);
                    }
                    else if (game.HomeLineupScoreAvg < game.AwayLineupScoreAvg)
                    {
                        AdjustConfidence(confidenceScores, game.AwayTeam, 5);
                    }
                    if (game.HomeLineupScoreAvg > 0 && game.AwayLineupScoreAvg <0)
                    {
                        AdjustConfidence(confidenceScores, game.HomeTeam, 5);
                        AdjustConfidence(confidenceScores, game.AwayTeam, -5);
                    }
                    else if (game.HomeLineupScoreAvg <0 && game.AwayLineupScoreAvg > 0)
                    {
                        AdjustConfidence(confidenceScores, game.AwayTeam, 5);
                        AdjustConfidence(confidenceScores, game.HomeTeam, -5);
                    }
                    //----------------------------------------------------------------------------------------------------------------------------
                    // Adjust based on team records vs opposing SP throws --Dont think any of this below is working
                    if (game.HomeRecordVsOpposingSPThrows.Contains("W") && game.AwayRecordVsOpposingSPThrows.Contains("L"))
                    {
                        AdjustConfidence(confidenceScores, game.HomeTeam, 5);
                        AdjustConfidence(confidenceScores, game.AwayTeam, -5);

                    }
                    else if (game.AwayRecordVsOpposingSPThrows.Contains("W") && game.HomeRecordVsOpposingSPThrows.Contains("L"))
                    {
                        AdjustConfidence(confidenceScores, game.AwayTeam, 5);
                        AdjustConfidence(confidenceScores, game.AwayTeam, -5);

                    }

                    // Adjust based on home and away records
                    if (game.HomeRecordHome.Contains("W") && game.AwayRecordAway.Contains("L"))
                    {
                        AdjustConfidence(confidenceScores, game.HomeTeam, 5);
                        AdjustConfidence(confidenceScores, game.AwayTeam, -5);

                    }
                    else if (game.AwayRecordAway.Contains("W") && game.HomeRecordHome.Contains("L"))
                    {
                        AdjustConfidence(confidenceScores, game.AwayTeam, 5);
                        AdjustConfidence(confidenceScores, game.HomeTeam, -5);

                    }
                    //----------------------------------------------------------------------------------------------------------------------------

                }
            }
        }

        // Adjusts the confidence score for a specific team
        private void AdjustConfidence(Dictionary<string, double> confidenceScores, string team, double adjustment)
        {
            if (confidenceScores.ContainsKey(team))
            {
                confidenceScores[team] += adjustment;
            }
        }
    }
}
