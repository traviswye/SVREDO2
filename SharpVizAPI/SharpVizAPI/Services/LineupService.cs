using HtmlAgilityPack;
using System.Net.Http;
using System.Threading.Tasks;
using System.Linq;
using System.Collections.Generic;
using System;
using Newtonsoft.Json;
using Microsoft.Extensions.Logging;
using SharpVizAPI.Models;
using Microsoft.EntityFrameworkCore;
using SharpVizAPI.Data;
using System.Reflection.Metadata.Ecma335;

namespace SharpVizAPI.Services
{
    public class LineupService
    {
        private readonly HttpClient _httpClient;
        private readonly ILogger<LineupService> _logger;
        //private List<Pitcher> _startingPitchers;
        private List<StartingPitcher> _startingPitchers;
        private List<MLBplayer> _players;
        private readonly NrfidbContext _context;

        public LineupService(HttpClient httpClient, ILogger<LineupService> logger, NrfidbContext context)
        {
            _httpClient = httpClient;
            _logger = logger;
            _startingPitchers = new List<StartingPitcher>();
            _context = context;
        }

        public async Task FetchAndPostLineupsAndPredictionsAsync(string homeTeamFullName, string awayTeamFullName, int gamePreviewId)
        {
            _logger.LogInformation($"Starting to fetch, post lineups, and predict lineups for {homeTeamFullName} and {awayTeamFullName}.");

            // Fetch and post lineups
            await FetchAndPostLineupForTeamAsync(homeTeamFullName);
            await FetchAndPostLineupForTeamAsync(awayTeamFullName);

            // Predict lineups and store in LineupPredictions table
            await FetchAndStorePredictedLineupAsync(homeTeamFullName, gamePreviewId);
            await FetchAndStorePredictedLineupAsync(awayTeamFullName, gamePreviewId);

            _logger.LogInformation($"Finished fetching, posting, and predicting lineups for {homeTeamFullName} and {awayTeamFullName}.");
        }


        private async Task FetchAndStorePredictedLineupAsync(string teamFullName, int gamePreviewId)
        {
            _logger.LogInformation($"Predicting lineup for team {teamFullName} for gamePreviewId {gamePreviewId}.");

            try
            {
                // Retrieve the game preview from the database
                var gamePreview = await _context.GamePreviews.FirstOrDefaultAsync(gp => gp.Id == gamePreviewId);
                if (gamePreview == null)
                {
                    _logger.LogWarning($"Game preview with ID {gamePreviewId} not found.");
                    return;
                }

                // Determine the opponent and opposingSP based on the teamFullName
                string opponent;
                string opposingSP;

                if (gamePreview.HomeTeam == teamFullName)
                {
                    opponent = gamePreview.AwayTeam;
                    opposingSP = gamePreview.AwayPitcher;
                }
                else if (gamePreview.AwayTeam == teamFullName)
                {
                    opponent = gamePreview.HomeTeam;
                    opposingSP = gamePreview.HomePitcher;
                }
                else
                {
                    _logger.LogWarning($"Team {teamFullName} not found in game preview with ID {gamePreviewId}.");
                    return;
                }

                // Fetch pitcher information to determine if the opposingSP is an LHP or RHP
                bool isLHP = false;
                if (!string.IsNullOrEmpty(opposingSP))
                {
                    var pitcherResponse = await _httpClient.GetAsync($"https://localhost:44346/api/Pitchers/{opposingSP}");
                    if (pitcherResponse.IsSuccessStatusCode)
                    {
                        var pitcherJson = await pitcherResponse.Content.ReadAsStringAsync();
                        var pitcher = JsonConvert.DeserializeObject<Pitcher>(pitcherJson);
                        isLHP = pitcher.Throws == "LHP";
                    }
                }

                // Set initial values for recentGames and weightRecent
                int recentGames = 8;
                int weightRecent = 3;
                int nullCount;
                Dictionary<string, Dictionary<string, string>> predictedLineup = null;

                do
                {
                    // Call the PredictLineup endpoint
                    var response = await _httpClient.GetAsync($"https://localhost:44346/api/Lineups/predictLineup/{teamFullName}?recentGames={recentGames}&weightRecent={weightRecent}&throw={(isLHP ? "LHP" : "RHP")}");
                    if (!response.IsSuccessStatusCode)
                    {
                        _logger.LogWarning($"Failed to predict lineup for {teamFullName}. Status code: {response.StatusCode}");
                        return;
                    }

                    var jsonString = await response.Content.ReadAsStringAsync();
                    predictedLineup = JsonConvert.DeserializeObject<Dictionary<string, Dictionary<string, string>>>(jsonString);

                    // Count null values in the response across all batting positions
                    nullCount = predictedLineup[$"vs{(isLHP ? "LHP" : "RHP")}"].Values.Count(v => v == null);

                    // If nulls exist in any position, increment recentGames and weightRecent, and retry
                    if (nullCount > 0)
                    {

                        // Check if the limits are reached
                        if (recentGames >= 40 || weightRecent >= 15)
                        {
                            _logger.LogInformation($"Reached the limit of recentGames or weightRecent. Using the available lineup and filling remaining slots with 'PROSPECT'.");
                            // Manually fill null positions with "PROSPECT"
                            foreach (var key in predictedLineup[$"vs{(isLHP ? "LHP" : "RHP")}"].Keys.ToList())
                            {
                                if (predictedLineup[$"vs{(isLHP ? "LHP" : "RHP")}"][key] == null)
                                {
                                    predictedLineup[$"vs{(isLHP ? "LHP" : "RHP")}"][key] = "PROSPECT";
                                }
                            }
                            break;
                        }
                        recentGames += 2;
                        weightRecent += 1;
                        _logger.LogInformation($"Null values found in lineup response. Incrementing recentGames to {recentGames} and weightRecent to {weightRecent}, retrying.");
                    }
                }
                while (nullCount > 0); // Continue until all positions from batting1 to batting9 are filled

                // Store the predicted lineup in the LineupPredictions table
                var lineupPrediction = new LineupPrediction
                {
                    Team = teamFullName,
                    GameNumber = gamePreviewId, // Use gamePreviewId as a reference to the game
                    Date = DateTime.Now, // Adjust as necessary
                    Opponent = opponent,
                    OpposingSP = opposingSP,
                    LHP = isLHP,
                    Batting1st = predictedLineup[$"vs{(isLHP ? "LHP" : "RHP")}"]["batting1"],
                    Batting2nd = predictedLineup[$"vs{(isLHP ? "LHP" : "RHP")}"]["batting2"],
                    Batting3rd = predictedLineup[$"vs{(isLHP ? "LHP" : "RHP")}"]["batting3"],
                    Batting4th = predictedLineup[$"vs{(isLHP ? "LHP" : "RHP")}"]["batting4"],
                    Batting5th = predictedLineup[$"vs{(isLHP ? "LHP" : "RHP")}"]["batting5"],
                    Batting6th = predictedLineup[$"vs{(isLHP ? "LHP" : "RHP")}"]["batting6"],
                    Batting7th = predictedLineup[$"vs{(isLHP ? "LHP" : "RHP")}"]["batting7"],
                    Batting8th = predictedLineup[$"vs{(isLHP ? "LHP" : "RHP")}"]["batting8"],
                    Batting9th = predictedLineup[$"vs{(isLHP ? "LHP" : "RHP")}"]["batting9"],
                    GamePreviewId = gamePreviewId // Link to the GamePreview table
                };

                _context.LineupPredictions.Add(lineupPrediction);
                await _context.SaveChangesAsync();

                _logger.LogInformation($"Stored predicted lineup for team {teamFullName} in LineupPredictions table.");
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error predicting lineup for {teamFullName}: {ex.Message}");
            }
        }

        //NEED TO FIX HOW THE DB IS KEPT UP. WE ARE NEVER TAKING PLAYERS OUT. BBREFID IS PRIMARY SO WE ARE ONLY ADDING BUT NEVER SUBTRACTING
        //private async Task<List<string>> GetInjuredPlayersAsync()
        //{
        //    try
        //    {
        //        // Fetch injured players with today's date
        //        var injuredPlayers = await _context.Injuries
        //            .Where(i => i.Date == DateTime.Today)
        //            .Select(i => i.BbrefId)
        //            .ToListAsync();

        //        _logger.LogInformation($"Fetched {injuredPlayers.Count} injured players for today.");
        //        return injuredPlayers;
        //    }
        //    catch (Exception ex)
        //    {
        //        _logger.LogError($"Error fetching injured players: {ex.Message}");
        //        return new List<string>();  // Return empty list if there is an error
        //    }
        //}


        private async Task FetchStartingPitchersAsync()
        {
            try
            {
                var response = await _httpClient.GetStringAsync("https://localhost:44346/api/GamePreviews/startingL7Pitchers");
                _startingPitchers = JsonConvert.DeserializeObject<List<StartingPitcher>>(response);
                _logger.LogInformation($"Successfully fetched starting pitchers for the last 7 days.");
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error fetching starting pitchers: {ex.Message}");
            }
        }
        private async Task FetchAndPostLineupForTeamAsync(string teamAbbr)
        {
            // Ensure we use the abbreviation for the URL
            string url = $"https://www.baseball-reference.com/teams/{GetTeamAbbreviation(teamAbbr)}/2024-batting-orders.shtml";

            try
            {
                await Task.Delay(TimeSpan.FromSeconds(5)); //delay 5 seconds to avoid more than 30 requests in 60 seconds
                _logger.LogInformation($"Fetching lineup for team {teamAbbr} from {url}.");

                var response = await _httpClient.GetStringAsync(url);
                var doc = new HtmlDocument();
                doc.LoadHtml(response);

                // Use a more generalized XPath query to locate the table
                var table = doc.DocumentNode.SelectSingleNode("//table[contains(@id, 'grid') and contains(@class, 'sortable')]");
                if (table == null)
                {
                    _logger.LogWarning($"Lineup table not found for team {teamAbbr}.");
                    return;
                }

                // Get the last row (last lineup)
                var lastRow = table.SelectNodes(".//tbody/tr").LastOrDefault();
                if (lastRow == null)
                {
                    _logger.LogWarning($"No lineup data found for team {teamAbbr}.");
                    return;
                }

                // Add logging to capture raw HTML of the last row
                _logger.LogInformation($"Last row HTML: {lastRow.InnerHtml}");

                // Parse the data from the last row
                string gameNumberText = lastRow.SelectSingleNode(".//th")?.InnerText;
                _logger.LogInformation($"Raw game number text: {gameNumberText}");
                var gameNumber = int.Parse(gameNumberText?.Split('.')[0] ?? "0");

                string opponentAbbr = lastRow.SelectSingleNode(".//th//a[last()]")?.InnerText;
                _logger.LogInformation($"Raw opponent abbreviation: {opponentAbbr}");
                var opponent = GetTeamFullName(opponentAbbr);

                string dateString = lastRow.SelectSingleNode(".//th")?.InnerText.Split(' ')[1].Split(',')[1];
                _logger.LogInformation($"Raw date string: {dateString}");
                var date = DateTime.ParseExact($"2024-{dateString}", "yyyy-M/d", null);  // Convert to DateTime format

                string resultScoreText = lastRow.SelectSingleNode(".//th")?.InnerText;
                _logger.LogInformation($"Raw result and score text: {resultScoreText}");
                var resultScore = resultScoreText?.Split('(');
                var result = resultScore.Length > 1 ? resultScore[0].Trim().Split().Last() : "N/A";
                var score = resultScore.Length > 1 ? resultScore[1].Trim(')', '#') : "N/A";

                bool lhp = lastRow.SelectSingleNode(".//th")?.InnerText.Contains("#") ?? false;
                _logger.LogInformation($"LHP status: {lhp}");

                var playerTds = lastRow.SelectNodes(".//td[starts-with(@class, 'left')]");
                _logger.LogInformation($"Found playerTds: {playerTds?.Count ?? 0}");

                if (playerTds != null)
                {
                    var battingOrder = new Dictionary<string, string>
            {
                { "1st", null },
                { "2nd", null },
                { "3rd", null },
                { "4th", null },
                { "5th", null },
                { "6th", null },
                { "7th", null },
                { "8th", null },
                { "9th", null }
            };

                    foreach (var td in playerTds)
                    {
                        string positionInOrder = td.GetAttributeValue("data-stat", ""); // Get the batting order position (e.g., "1st", "2nd")
                        string playerId = td.SelectSingleNode(".//a")?.GetAttributeValue("data-entry-id", ""); // Get the player ID from data-entry-id

                        _logger.LogInformation($"Mapping position {positionInOrder} to player {playerId}");

                        if (battingOrder.ContainsKey(positionInOrder) && !string.IsNullOrEmpty(playerId))
                        {
                            battingOrder[positionInOrder] = playerId;
                        }
                    }

                    // Extract and match opposing pitcher
                    string opposingSP = lastRow.SelectSingleNode(".//th/a[@title]")?.GetAttributeValue("title", "").Replace("facing: ", "");
                    opposingSP = await GetBbrefIdForPitcher(opposingSP, opponent);
                    _logger.LogInformation($"Opposing pitcher: {opposingSP}");

                    var lineupData = new
                    {
                        team = teamAbbr,
                        gameNumber,
                        date = date.ToString("yyyy-MM-dd"),  // Ensure date format is correct
                        opponent,
                        opposingSP,
                        lhp,
                        result,
                        score,
                        batting1st = battingOrder["1st"],
                        batting2nd = battingOrder["2nd"],
                        batting3rd = battingOrder["3rd"],
                        batting4th = battingOrder["4th"],
                        batting5th = battingOrder["5th"],
                        batting6th = battingOrder["6th"],
                        batting7th = battingOrder["7th"],
                        batting8th = battingOrder["8th"],
                        batting9th = battingOrder["9th"]
                    };

                    _logger.LogInformation($"Successfully parsed lineup data for team {teamAbbr} for game {gameNumber}: {JsonConvert.SerializeObject(lineupData)}");
                    await PostLineupAsync(lineupData);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error fetching lineup for {teamAbbr}: {ex.Message}");
            }
        }

        private async Task<string> GetBbrefIdForPitcher(string fullName, string teamAbbr)
        {
            try
            {
                var response = await _httpClient.GetAsync($"https://localhost:44346/api/MLBPlayer/search?fullName={Uri.EscapeDataString(fullName)}&team={GetTeamAbbreviation(teamAbbr)}");
                if (response.IsSuccessStatusCode)
                {
                    var jsonString = await response.Content.ReadAsStringAsync();
                    var players = JsonConvert.DeserializeObject<List<MLBplayer>>(jsonString);

                    // Assuming the first player is the correct one or apply any other logic here
                    var player = players?.FirstOrDefault();
                    return player?.bbrefId ?? fullName;  // Return bbrefId if found, otherwise return full name
                }
                _logger.LogWarning($"Failed to fetch bbrefId for {fullName} on team {teamAbbr}. Status code: {response.StatusCode}");
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error fetching bbrefId for {fullName} on team {teamAbbr}: {ex.Message}");
            }

            return fullName;  // If fetching fails, return full name
        }

        private async Task PostLineupAsync(object lineupData)
        {
            try
            {
                var content = new StringContent(JsonConvert.SerializeObject(lineupData), System.Text.Encoding.UTF8, "application/json");
                var response = await _httpClient.PostAsync("https://localhost:44346/api/Lineups", content);

                dynamic dynamicLineupData = lineupData;
                var gameNumber = dynamicLineupData.gameNumber;

                if (response.IsSuccessStatusCode)
                {
                    _logger.LogInformation($"Successfully posted lineup for game {gameNumber}.");
                }
                else
                {
                    _logger.LogWarning($"Failed to post lineup for game {gameNumber}. Status code: {response.StatusCode}. Response: {await response.Content.ReadAsStringAsync()}");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error posting lineup: {ex.Message}");
            }
        }

        private string GetOpposingPitcherBbrefId(string opposingSP, string opponent)
        {
            // Convert the opposingSP name to the bbrefId format
            string bbrefId = ConvertNameToBbrefId(opposingSP);

            // Find matching pitchers from the last 7 days
            var matchingPitchers = _startingPitchers
                .Where(p =>
                    (p.HomePitcher != null && p.HomePitcher.StartsWith(bbrefId)) ||
                    (p.AwayPitcher != null && p.AwayPitcher.StartsWith(bbrefId)))
                .ToList();

            // If there is exactly one match, return it
            if (matchingPitchers.Count == 1)
            {
                var match = matchingPitchers.First();
                return match.HomePitcher.StartsWith(bbrefId) ? match.HomePitcher : match.AwayPitcher;
            }
            // If multiple matches are found, check for unique entries
            else if (matchingPitchers.Count > 1)
            {
                var uniqueMatches = matchingPitchers.DistinctBy(p => p.HomePitcher == bbrefId ? p.HomePitcher : p.AwayPitcher).ToList();

                // If there is still exactly one unique match, return it
                if (uniqueMatches.Count == 1)
                {
                    var match = uniqueMatches.First();
                    return match.HomePitcher.StartsWith(bbrefId) ? match.HomePitcher : match.AwayPitcher;
                }
                // If multiple unique matches exist, filter by opponent
                else if (uniqueMatches.Count > 1)
                {
                    var teamFilteredMatch = uniqueMatches.FirstOrDefault(p =>
                        GetTeamFullName(p.HomePitcher) == opponent ||
                        GetTeamFullName(p.AwayPitcher) == opponent);

                    if (teamFilteredMatch != null)
                    {
                        return teamFilteredMatch.HomePitcher.StartsWith(bbrefId) ? teamFilteredMatch.HomePitcher : teamFilteredMatch.AwayPitcher;
                    }
                }
            }

            // If no match or filtering fails, return the original name
            _logger.LogInformation($"No match found for {bbrefId}.");
            return opposingSP;
        }


        private async Task FetchAndPostLineupForTeamWithDelayAsync(string teamAbbr)
        {
            await FetchAndPostLineupForTeamAsync(teamAbbr);

            // Introduce a 5-second delay between requests
            _logger.LogInformation($"Waiting for 5 seconds before making the next request...");
            await Task.Delay(TimeSpan.FromSeconds(5));
        }


        private string ConvertNameToBbrefId(string fullName)
{
    var nameParts = fullName.Split(' ');
    if (nameParts.Length < 2) return fullName;

    var lastName = nameParts[1];
    var firstName = nameParts[0];

    return lastName.Substring(0, Math.Min(lastName.Length, 5)).ToLower() + firstName.Substring(0, Math.Min(firstName.Length, 2)).ToLower();
}


        private string ConvertMonthToNumber(string month)
        {
            var monthMap = new Dictionary<string, string>
    {
        { "January", "01" }, { "Jan", "01" },
        { "February", "02" }, { "Feb", "02" },
        { "March", "03" }, { "Mar", "03" },
        { "April", "04" }, { "Apr", "04" },
        { "May", "05" },
        { "June", "06" }, { "Jun", "06" },
        { "July", "07" }, { "Jul", "07" },
        { "August", "08" }, { "Aug", "08" },
        { "September", "09" }, { "Sep", "09" },
        { "October", "10" }, { "Oct", "10" },
        { "November", "11" }, { "Nov", "11" },
        { "December", "12" }, { "Dec", "12" }
    };

            return monthMap.ContainsKey(month) ? monthMap[month] : null;
        }
        private string CleanAndFormatDate(string rawDateString)
        {
            // Split the date string into components (Month Day, Year)
            var dateParts = rawDateString.Split(' ');

            if (dateParts.Length != 3)
            {
                return null;  // Unexpected format
            }

            var month = dateParts[0];  // "August"
            var day = RemoveDaySuffix(dateParts[1]);  // "21st" -> "21"
            var year = dateParts[2];  // "2024"

            // Convert the month to a number
            var monthNumber = ConvertMonthToNumber(month);
            if (monthNumber == null)
            {
                return null;  // Invalid month
            }

            // Ensure the day is two digits
            var dayNumber = day.PadLeft(2, '0');

            // Return the formatted date in "yyyy-MM-dd" format
            return $"{year}-{monthNumber}-{dayNumber}";
        }

        private string RemoveDaySuffix(string day)
        {
            // Remove common suffixes from the day part of the date string
            return day.Replace("st", "").Replace("nd", "").Replace("rd", "").Replace("th", "");
        }
        public async Task FetchAndPostActualLineupsAsync()
        {
            _logger.LogInformation($"Starting to fetch and post actual lineups.");

            string url = "https://www.mlb.com/starting-lineups";

            try
            {
                var response = await _httpClient.GetStringAsync(url);
                var doc = new HtmlDocument();
                doc.LoadHtml(response);

                var dateNode = doc.DocumentNode.SelectSingleNode("//h2[@class='starting-lineups__date-title--current']");
                if (dateNode == null)
                {
                    _logger.LogWarning("Date element not found on the lineup page.");
                    return;
                }

                var rawDateString = dateNode.InnerText.Trim();
                _logger.LogInformation($"Raw date string: {rawDateString}");

                var formattedDate = CleanAndFormatDate(rawDateString);
                if (formattedDate == null)
                {
                    _logger.LogWarning($"Failed to format date string: {rawDateString}");
                    return;
                }

                _logger.LogInformation($"Formatted date string: {formattedDate}");

                var lineupsSection = doc.DocumentNode.SelectSingleNode("//section[contains(@class, 'starting-lineups')]");
                if (lineupsSection == null)
                {
                    _logger.LogWarning("Starting lineups section not found.");
                    return;
                }

                foreach (var matchup in lineupsSection.SelectNodes(".//div[contains(@class, 'starting-lineups__matchup')]"))
                {
                    var awayTeam = matchup.SelectSingleNode(".//span[contains(@class, 'starting-lineups__team-name--away')]").InnerText.Trim();
                    var homeTeam = matchup.SelectSingleNode(".//span[contains(@class, 'starting-lineups__team-name--home')]").InnerText.Trim();

                    var gamePreview = await _context.GamePreviews.FirstOrDefaultAsync(gp => gp.HomeTeam == homeTeam && gp.AwayTeam == awayTeam && gp.Date == DateTime.Parse(formattedDate));
                    if (gamePreview == null)
                    {
                        _logger.LogWarning($"No game preview found for matchup {awayTeam} @ {homeTeam} on {formattedDate}.");
                        continue;
                    }

                    // Fetch or update the away team's lineup
                    var awayLineup = ExtractLineupFromMatchup(matchup, "away");
                    await StoreOrUpdateActualLineupAsync(awayTeam, homeTeam, awayLineup, gamePreview.Id);

                    // Fetch or update the home team's lineup
                    var homeLineup = ExtractLineupFromMatchup(matchup, "home");
                    await StoreOrUpdateActualLineupAsync(homeTeam, awayTeam, homeLineup, gamePreview.Id);
                }

                _logger.LogInformation($"Finished fetching and posting actual lineups.");
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error fetching actual lineups: {ex.Message}");
            }
        }

        private async Task StoreOrUpdateActualLineupAsync(string teamFullName, string opponentFullName, List<(string playerName, string position)> lineup, int gamePreviewId)
        {
            try
            {
                // Retrieve the game preview from the database
                var gamePreview = await _context.GamePreviews.FirstOrDefaultAsync(gp => gp.Id == gamePreviewId);
                if (gamePreview == null)
                {
                    _logger.LogWarning($"Game preview with ID {gamePreviewId} not found.");
                    return;
                }

                // Check if an actual lineup for this team and game preview ID already exists
                var existingLineup = await _context.ActualLineups.FirstOrDefaultAsync(al => al.Team == teamFullName && al.GamePreviewId == gamePreviewId);
                if (existingLineup != null)
                {
                    _logger.LogInformation($"Lineup already exists for team {teamFullName} and game preview ID {gamePreviewId}. Skipping posting.");
                    return; // Exit if the lineup already exists
                }

                // Determine the opponent and opposingSP based on the teamFullName
                string opponent;
                string opposingSP;

                if (gamePreview.HomeTeam == teamFullName)
                {
                    opponent = gamePreview.AwayTeam;
                    opposingSP = gamePreview.AwayPitcher;  // Pull OpposingSP from gamePreview
                }
                else if (gamePreview.AwayTeam == teamFullName)
                {
                    opponent = gamePreview.HomeTeam;
                    opposingSP = gamePreview.HomePitcher;  // Pull OpposingSP from gamePreview
                }
                else
                {
                    _logger.LogWarning($"Team {teamFullName} not found in game preview with ID {gamePreviewId}.");
                    return;
                }

                // Fetch pitcher information to determine if the opposingSP is an LHP or RHP
                bool isLHP = false;
                if (!string.IsNullOrEmpty(opposingSP))
                {
                    var pitcherResponse = await _httpClient.GetAsync($"https://localhost:44346/api/Pitchers/{opposingSP}");
                    if (pitcherResponse.IsSuccessStatusCode)
                    {
                        var pitcherJson = await pitcherResponse.Content.ReadAsStringAsync();
                        var pitcher = JsonConvert.DeserializeObject<Pitcher>(pitcherJson);
                        isLHP = pitcher.Throws == "LHP";
                    }
                }

                // Translate player names to bbrefId using the GetBbrefIdForPlayer method
                var actualLineup = new ActualLineup
                {
                    Team = teamFullName,
                    GameNumber = gamePreviewId, // Use gamePreviewId as the game reference
                    Date = gamePreview.Date, // Use the date from GamePreview
                    Opponent = opponent,
                    OpposingSP = opposingSP,  // Set from gamePreview, not lineup data
                    LHP = isLHP,
                    Batting1st = await GetBbrefIdForPlayer(lineup.ElementAtOrDefault(0).playerName?.Trim(), teamFullName),
                    Batting2nd = await GetBbrefIdForPlayer(lineup.ElementAtOrDefault(1).playerName?.Trim(), teamFullName),
                    Batting3rd = await GetBbrefIdForPlayer(lineup.ElementAtOrDefault(2).playerName?.Trim(), teamFullName),
                    Batting4th = await GetBbrefIdForPlayer(lineup.ElementAtOrDefault(3).playerName?.Trim(), teamFullName),
                    Batting5th = await GetBbrefIdForPlayer(lineup.ElementAtOrDefault(4).playerName?.Trim(), teamFullName),
                    Batting6th = await GetBbrefIdForPlayer(lineup.ElementAtOrDefault(5).playerName?.Trim(), teamFullName),
                    Batting7th = await GetBbrefIdForPlayer(lineup.ElementAtOrDefault(6).playerName?.Trim(), teamFullName),
                    Batting8th = await GetBbrefIdForPlayer(lineup.ElementAtOrDefault(7).playerName?.Trim(), teamFullName),
                    Batting9th = await GetBbrefIdForPlayer(lineup.ElementAtOrDefault(8).playerName?.Trim(), teamFullName),
                    GamePreviewId = gamePreviewId // Link to the GamePreview table
                };

                // Log each batting position to debug any unexpected values
                _logger.LogInformation($"Checking lineup for {teamFullName}: Batting1st={actualLineup.Batting1st}, Batting2nd={actualLineup.Batting2nd}, Batting3rd={actualLineup.Batting3rd}, Batting4th={actualLineup.Batting4th}, Batting5th={actualLineup.Batting5th}, Batting6th={actualLineup.Batting6th}, Batting7th={actualLineup.Batting7th}, Batting8th={actualLineup.Batting8th}, Batting9th={actualLineup.Batting9th}");

                // Check if any of the batting positions are null or contain only whitespace
                if (string.IsNullOrWhiteSpace(actualLineup.Batting1st) ||
                    string.IsNullOrWhiteSpace(actualLineup.Batting2nd) ||
                    string.IsNullOrWhiteSpace(actualLineup.Batting3rd) ||
                    string.IsNullOrWhiteSpace(actualLineup.Batting4th) ||
                    string.IsNullOrWhiteSpace(actualLineup.Batting5th) ||
                    string.IsNullOrWhiteSpace(actualLineup.Batting6th) ||
                    string.IsNullOrWhiteSpace(actualLineup.Batting7th) ||
                    string.IsNullOrWhiteSpace(actualLineup.Batting8th) ||
                    string.IsNullOrWhiteSpace(actualLineup.Batting9th))
                {
                    _logger.LogWarning($"Incomplete or invalid lineup for team {teamFullName} for game preview ID {gamePreviewId}. Skipping posting lineup.");
                    return; // Exit the method if any batting position is null or whitespace
                }

                // Store the lineup if it's valid
                _context.ActualLineups.Add(actualLineup);
                await _context.SaveChangesAsync();

                _logger.LogInformation($"Stored actual lineup for team {teamFullName} for game preview ID {gamePreviewId}.");
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error storing actual lineup for team {teamFullName}: {ex.Message}");
            }
        }





        private List<(string playerName, string position)> ExtractLineupFromMatchup(HtmlNode matchup, string teamType)
        {
            var lineup = new List<(string playerName, string position)>();
            var lineupNode = matchup.SelectSingleNode($".//ol[contains(@class, 'starting-lineups__team--{teamType}')]");

            if (lineupNode != null)
            {
                foreach (var playerNode in lineupNode.SelectNodes(".//li[contains(@class, 'starting-lineups__player')]"))
                {
                    var playerName = playerNode.SelectSingleNode(".//a")?.InnerText.Trim();
                    var playerPosition = playerNode.SelectSingleNode(".//span[contains(@class, 'starting-lineups__player--position')]")?.InnerText.Trim();

                    if (!string.IsNullOrEmpty(playerName) && !string.IsNullOrEmpty(playerPosition))
                    {
                        lineup.Add((playerName, playerPosition));
                    }
                }
            }
            return lineup;
        }

        private async Task StoreActualLineupAsync(string teamFullName, string opponentFullName, List<(string playerName, string position)> lineup, int gamePreviewId)
        {
            try
            {
                // Retrieve the game preview from the database
                var gamePreview = await _context.GamePreviews.FirstOrDefaultAsync(gp => gp.Id == gamePreviewId);
                if (gamePreview == null)
                {
                    _logger.LogWarning($"Game preview with ID {gamePreviewId} not found.");
                    return;
                }

                // Determine the opponent and opposingSP based on the teamFullName
                string opponent;
                string opposingSP;

                if (gamePreview.HomeTeam == teamFullName)
                {
                    opponent = gamePreview.AwayTeam;
                    opposingSP = gamePreview.AwayPitcher;  // Pull OpposingSP from gamePreview
                }
                else if (gamePreview.AwayTeam == teamFullName)
                {
                    opponent = gamePreview.HomeTeam;
                    opposingSP = gamePreview.HomePitcher;  // Pull OpposingSP from gamePreview
                }
                else
                {
                    _logger.LogWarning($"Team {teamFullName} not found in game preview with ID {gamePreviewId}.");
                    return;
                }

                // Fetch pitcher information to determine if the opposingSP is an LHP or RHP
                bool isLHP = false;
                if (!string.IsNullOrEmpty(opposingSP))
                {
                    var pitcherResponse = await _httpClient.GetAsync($"https://localhost:44346/api/Pitchers/{opposingSP}");
                    if (pitcherResponse.IsSuccessStatusCode)
                    {
                        var pitcherJson = await pitcherResponse.Content.ReadAsStringAsync();
                        var pitcher = JsonConvert.DeserializeObject<Pitcher>(pitcherJson);
                        isLHP = pitcher.Throws == "LHP";
                    }
                }

                // Translate player names to bbrefId using the GetBbrefIdForPlayer method
                var actualLineup = new ActualLineup
                {
                    Team = teamFullName,
                    GameNumber = gamePreviewId, // Use gamePreviewId as the game reference
                    Date = gamePreview.Date, // Use the date from GamePreview
                    Opponent = opponent,
                    OpposingSP = opposingSP,  // Set from gamePreview, not lineup data
                    LHP = isLHP,
                    Batting1st = await GetBbrefIdForPlayer(lineup.ElementAtOrDefault(0).playerName, teamFullName),
                    Batting2nd = await GetBbrefIdForPlayer(lineup.ElementAtOrDefault(1).playerName, teamFullName),
                    Batting3rd = await GetBbrefIdForPlayer(lineup.ElementAtOrDefault(2).playerName, teamFullName),
                    Batting4th = await GetBbrefIdForPlayer(lineup.ElementAtOrDefault(3).playerName, teamFullName),
                    Batting5th = await GetBbrefIdForPlayer(lineup.ElementAtOrDefault(4).playerName, teamFullName),
                    Batting6th = await GetBbrefIdForPlayer(lineup.ElementAtOrDefault(5).playerName, teamFullName),
                    Batting7th = await GetBbrefIdForPlayer(lineup.ElementAtOrDefault(6).playerName, teamFullName),
                    Batting8th = await GetBbrefIdForPlayer(lineup.ElementAtOrDefault(7).playerName, teamFullName),
                    Batting9th = await GetBbrefIdForPlayer(lineup.ElementAtOrDefault(8).playerName, teamFullName),
                    GamePreviewId = gamePreviewId // Link to the GamePreview table
                };

                // Check if any of the batting positions are null
                if (string.IsNullOrEmpty(actualLineup.Batting1st) ||
                    string.IsNullOrEmpty(actualLineup.Batting2nd) ||
                    string.IsNullOrEmpty(actualLineup.Batting3rd) ||
                    string.IsNullOrEmpty(actualLineup.Batting4th) ||
                    string.IsNullOrEmpty(actualLineup.Batting5th) ||
                    string.IsNullOrEmpty(actualLineup.Batting6th) ||
                    string.IsNullOrEmpty(actualLineup.Batting7th) ||
                    string.IsNullOrEmpty(actualLineup.Batting8th) ||
                    string.IsNullOrEmpty(actualLineup.Batting9th))
                {
                    _logger.LogWarning($"Incomplete lineup for team {teamFullName} for game preview ID {gamePreviewId}. Skipping posting lineup.");
                    return; // Exit the method if any batting position is null
                }

                // Store the lineup if it's valid
                _context.ActualLineups.Add(actualLineup);
                await _context.SaveChangesAsync();

                _logger.LogInformation($"Stored actual lineup for team {teamFullName} for game preview ID {gamePreviewId}.");
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error storing actual lineup for team {teamFullName}: {ex.Message}");
            }
        }



        private async Task<string> GetBbrefIdForPlayer(string playerName, string team)
        {
            if (playerName != null)
            {
            

            try
            {
                var response = await _httpClient.GetAsync($"https://localhost:44346/api/MLBPlayer/search?fullName={Uri.EscapeDataString(playerName)}&team={GetTeamAbbreviation(team)}");
                if (response.IsSuccessStatusCode)
                {
                    var jsonString = await response.Content.ReadAsStringAsync();
                    var players = JsonConvert.DeserializeObject<List<MLBplayer>>(jsonString);

                    // Assuming the first player is the correct one or apply any other logic here
                    var player = players?.FirstOrDefault();
                    return player?.bbrefId ?? playerName;  // Return bbrefId if found, otherwise return full name
                }
                _logger.LogWarning($"Failed to fetch bbrefId for {playerName} on team {team}. Status code: {response.StatusCode}");
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error fetching bbrefId for {playerName} on team {team}: {ex.Message}");
            } }

            return playerName;  // If fetching fails, return full name
        }
         
        


        private string GetTeamAbbreviation(string fullName)
        {
            var fullNameToAbbrMap = new Dictionary<string, string>
            {
                { "Diamondbacks", "ARI" },
                { "Braves", "ATL" },
                { "Orioles", "BAL" },
                { "Red Sox", "BOS" },
                { "Cubs", "CHC" },
                { "White Sox", "CHW" },
                { "Reds", "CIN" },
                { "Guardians", "CLE" },
                { "Rockies", "COL" },
                { "Tigers", "DET" },
                { "Astros", "HOU" },
                { "Royals", "KCR" },
                { "Angels", "LAA" },
                { "Dodgers", "LAD" },
                { "Marlins", "MIA" },
                { "Brewers", "MIL" },
                { "Twins", "MIN" },
                { "Mets", "NYM" },
                { "Yankees", "NYY" },
                { "Athletics", "OAK" },
                { "Phillies", "PHI" },
                { "Pirates", "PIT" },
                { "Padres", "SDP" },
                { "Mariners", "SEA" },
                { "Giants", "SFG" },
                { "Cardinals", "STL" },
                { "Rays", "TBR" },
                { "Rangers", "TEX" },
                { "Blue Jays", "TOR" },
                { "Nationals", "WSN" }
            };

            return fullNameToAbbrMap.TryGetValue(fullName, out var abbr) ? abbr : "Unknown";
        }

        private string GetTeamFullName(string teamAbbr)
        {
            var teamNameMap = new Dictionary<string, string>
            {
                { "ARI", "Diamondbacks" },
                { "ATL", "Braves" },
                { "BAL", "Orioles" },
                { "BOS", "Red Sox" },
                { "CHC", "Cubs" },
                { "CHW", "White Sox" },
                { "CIN", "Reds" },
                { "CLE", "Guardians" },
                { "COL", "Rockies" },
                { "DET", "Tigers" },
                { "HOU", "Astros" },
                { "KCR", "Royals" },
                { "LAA", "Angels" },
                { "LAD", "Dodgers" },
                { "MIA", "Marlins" },
                { "MIL", "Brewers" },
                { "MIN", "Twins" },
                { "NYM", "Mets" },
                { "NYY", "Yankees" },
                { "OAK", "Athletics" },
                { "PHI", "Phillies" },
                { "PIT", "Pirates" },
                { "SDP", "Padres" },
                { "SEA", "Mariners" },
                { "SFG", "Giants" },
                { "STL", "Cardinals" },
                { "TBR", "Rays" },
                { "TEX", "Rangers" },
                { "TOR", "Blue Jays" },
                { "WSN", "Nationals" }
            };
            return teamNameMap.TryGetValue(teamAbbr, out var teamName) ? teamName : "Unknown Team";
        }
    }
    public class StartingPitcher
    {
        public string HomePitcher { get; set; }
        public string AwayPitcher { get; set; }
    }

}
