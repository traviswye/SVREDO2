Readme:

Update weekly stats such as 

runDataPUT.py ----Need to take another look at this... Seems to be working but some errors yet db does get updated - betmgm site
	-https://sports.betmgm.com/en/blog/mlb/nrfi-yrfi-stats-records-no-runs-first-inning-yes-runs-first-inning-runs-mlb-teams-bm03/
----------------------------------------------------------------------------------------------------------------------------------------
//DAILYTODOS - No issues on webtraffic for next three immediately....
InjuryScrape.py
getTeamrecsplitPUT.py
leagueCountingStats.py
yesterdaysresults.py

//gets injury report for day - third party...covers.com -- THIS NEEDS WORK
 - mlb.com standings
getGamesSendtoDB.py // scrape gamePreview - gets games for day. Gets lineups - baseball-reference.com
	-NEED TO ADD MANUAL GAME OPTION

fetchgameodds.py
	- after gamepreviews go get major odd sites for ML
	- Need to add nrfi odds/o/u odds, f5odds

//NEED TO WAIT AFTER GETGAMES BEFORE SCRAPETEAMS

scrapeteams.py 	baseball-reference.com
	- This should be working now. Scrapes all teams playing today and updates all hitters and pitchers stats on that team.
	-- POTENTIALLY BROKEN stat tags seem to be changed when hitting 2024 teams. Possibly due to 2024 teams being finalized and now referencing a different bbref db..

bullpenTracking.py
	- tracks every pitcher in every game *****NEED TO SET THIS TO ONLY TAKE FINAL ROW OF TABLE. CURRETNLY SET TO FULL SEASON.
-----------------------------------------------------------------------------------------------------------------------
Figure out when to schedule Lineups. Can hit Post method multiple times for desired behavior of only posting teams with full lineups ready to use. STILL PUTTING IN NULL LINEUPS

currently its triggered from https://localhost:44346/api/Lineups/fetchActualLineups
-----------------------------------------------------------------------------------------------------------------------
SUNSETTTED---------scrapehitters.py -- update all hitter batting stats playing today - SUNSET FOR SCRAPETEAMS

pitcherbulk.py //updates daily starting pitchers stats - SUNSET FOR SCRAPETEAMS --- Dont believe this is needed anymore.
	- must update the date in script SHOULD FIX THIS
-----------------------------------------------------------------------------------------------------------------------

//this is on a timer to avoid traffic violations
pitchersbulksplits.py - must change the date in script SHOULD FIX THIS
	- replaced pitcher1stbulkapi.py // updates days starting pitchers 1st inning stats
	- grabs pitcher 1st inning and home/away splits LHB/RHB splits season total/last7/last14/last28 days splits

------------------------------------------------------------------------------------------------------------------	
hittersLast7.py - FantasyPros.com
	-Hitters last 7 days stats
	- Have to update mlbplayers table for new additions or team changes manually currently.
	*****need to look at transitioning this to bbrefidgamelogs script***** potentially adding this into team scrape though....

hittervsPitcher.py
- days career matchups
-Bill James method can be done here still. 

grabLast7bbref.py
- game logs scrape. gets last 7 days aggregates them. also captures season. This is to replace hittersLast7 from fantasy pros. 

Once grabLast7bbref has ran....
HIT ENDPOINT TO UPDATE HITTER TEMPS....
https://localhost:44346/api/HitterTempTracking/updateTemps?targetDate={date}

---------------------------------------------------------------------------------------------------------------------------
//baseball-reference.com need likely to wait 1-3 minutes after Pitcherbulk- This should be added to pitchers bulk
getall9.py - it is getting all pitchers starting todays By Innings table, gets all 9 innings back. 
	- need to create a service to calculate totals. This will give us exact comparison between 1st inning stats and full season stats in order to blend pitcher data from if hes just good in the first inning but overall is not great pitcher or visa versa
	- we are actually getting the total numbers in the 2024 totals split in our [PitcherPlatoonAndTrackRecord] table I think
	- No sleep timer on this... 8/30/2024 rare occasion there is 16 games. Pretty sure some results were cut offexpru

-----------------------------------------------------------------------------------------------------------------------

//should update this now we have more info
cheapnrfi.py - runs basic info summary on days games

//goes through first 6 in lineup adding HittersRunexpValue... takes home and away and calcs probability one of them will score home+away - (home*away)
expruns.py // evaluates diff scenarios for first 6 hitters vs the starting pitcher
	- Currently is Hitters season stats vs Pitchers 1st inning stats blended with LHB or RHB
	- try to build out season vs season... Season vs 1st inning (done)... can we populate hitters last 10 games stats? Hitters career numbers vs pitcher?
	- 

Simulation based - probability of each team scoring in 1st inning when games are simulated 1000x each
	- api/evaluation/evaluatewithbasestate/{date}
	-Also need to continue to experiment with expected runs. Currently using linear values and if runners are on base/how many outs... Lets try to lock this down more



hotsum.py - (hotsum2.py includes some betting model.) FIX WHEN ODDS ARE NULL  - THERE  IS BUG IN HOTSUM2 on final sort 
	- DFS STUFF
	-//Blended Hitter comparison - DFS values based on last 7 days vs season stats - Only compiles list of players playing today... Possibly integrate into dfs salaries
/api/hitterLast7/outperformers
	- api blendedPitchers last 28 days vs season for pitchers hot/cold ratings

Bettingmodel.py - basically split out version of hotsum2.py
	- Rule based betting model.
	-NEED TO FIX LINEUP SCORES - ADD API ENDPOINT TO LINEUPBLENDINGSCORES
litebet.py (param).
	- work on this one. Try to only have this script interpreting api responses. Move bet picks and models into api service.

- SB prop
- K prop - assumes pitcher pitches 6 innings...


pitchergamelvl.py
-Summary of pitching matchups



BACKTESTING for picking algo
gameswithoddsTraining.py - POPULATE THE TABLE that has history of results and odds


backtest.py - 100 dollar better - pool of teams, only sp adv rn
	- back tests teams with the weights we provide

backtestweightOPt.py
- attempt to optimize weights per team



