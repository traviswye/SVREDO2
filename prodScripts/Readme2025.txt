Readme for 2025

----------------------------------------------SCRAPPING FLOW----------------------------------------------
BAT FILE CONTROLS FLOW = dailyScrapes.bat


(tested - mods needed) runDataPut.py - site is still active... need to verify data once we run this but year is considered 
	- 3/21/25 site updated and changed the table. Need to rework this script...

(tested - modifications needed) injuryScrape.py - site is still active... year is considered in our script and controller
	- might need to add year to the PK for this table.

(tested working after changes) - getTeamrecsplitPUT.py - site is active.
	- YEAR IS NOT CONSIDERED... we maintain an achieve table where 2024 was copied over to... script will overwrite the data left in prod table.

(this is a bbref will need selenium version) leagueCountingStats.py - was set to only post it once which i did after season... tried to update controllers and script to potentially put data daily so we can track team offenses and pitching over course of year. needs testing.

*MOST IMPORTANT DRIVER SCRIPT*
(selenium version is working) getGamesSendtoDB.py - need to test for 2025 to see if bbref has changed anything.

(tested working) fetchgameodds.py - endpoint still works... currently returns [] as there are no odds for games yet for 3/27.. Will still need testing

*SUPER IMPORTANT PLAYER DATA*
scrapeteams.py - updated payloads to 2025... Needs testing first few days of season. Was potentially broken due to bbref off season changes.

bullpenTracking.py - updated script to hit 2025 data... will need testing - maybe currently set to get full season every time... we will only need to do that once then convert to only get the final game (bottom rows of table)

*CRUCIAL PITCHER DATA SCRIPT*
pitchersbulksplits.py - updated for 2025... need to test

hittervsPitcher.py - ***chromedriver***daily hitters vs starting pitchers data... year should not matter here. testing and correct version of chrome driver super important.
	- hope to add Bill James expected stat line here still

***SUPER IMPORTANT HITTER SCRIPT***
grabLast7bbref.py - this does not currently have a year date. THIS IS A PROBLEM. Fixed in prodscripts version but need to test.
	- need to add hook into controller to have service run https://localhost:44346/api/HitterTempTracking/updateTemps?targetDate={date} or add a request to bat file for this endpoint

getall9.py - updated for 2025 but we need to possibly put a timer on games logic as if there is a full slate plus Double header we could lose the 31-32nd request. Date needs fixing so its passed from cmd line for bat file.... we might have sunsetted this script tbh...

check_pitchers.py - not a scraper but it does check that we have no unannounced and if we do it causes a pause to our bat file.

---------------------------------------------------BAT FILE FLOW AND CHANGES NEEDED----------------------------------------------------
what is actually triggered in bat file... sudo...likely need to add some of the above scripts into flow still
Get today's date in yy-mm-dd format -> create a yyyy-mm-dd format as well

echo Date1: %date1%
echo Date2: %date2%


echo Running rundataPut.py...
echo Running getTeamrecsplitPUT.py...
echo Running injuryscrape.py...
echo Running yesterdaysresults.py with params %date2% %date2%...
echo Running getgamessendtodb.py...

REM Check if there are any unannounced pitchers
echo Checking for unannounced pitchers...
python check_pitchers.py %date1%

REM Check the error level (exit code) from check_pitchers.py
if %errorlevel% neq 0 (
    echo Unannounced pitchers found, please update them manually.
    pause
)

REM Continue with the rest of the scripts
echo Running fetchgameodds.py with param %date1%...
echo Running scrapeteams.py...
echo Running pitchersbulksplits.py with param %date1%...
echo Running hittervsPitcher.py...

-- playoff version
echo Running hittersLast7.py with date %date1% and playoff flag set to true/false...
python hittersLast7.py --date %date1% --playoff True

REM echo Running hittersLast7.py...(this got replaced with above due to playoff changes)
REM python hittersLast7.py

echo All scripts completed.


Proposed changes.... need to do something about unannounced pitchers... maybe another source or two rather than just bbref. When this is scheduled job on the server we cannot be logging in every time... maybe email notification and handle email reply to populate this...

Need to replace hittersLast7.py for getLast7bbref.py or potentially keep both. 

Need to add leagueCountingStats.py

Need to add getcontestpools.py - dfs dk player pools and contests for the day.

---------SUNSETTTED? SCRAPPING---------
scrapehitters.py -- update all hitter batting stats playing today - SUNSET FOR SCRAPETEAMS DELETE IF SCRAPE TEAMS WORKS 

pitcherbulk.py - dont think this is needed any longer (pitchersbulksplits.py) but here for reference incase anything is not updated. 

hittersLast7.py - this should still work however believe we have replaced this with grablast7bbref.py



--------------------------------------SUMMARY SCRIPTS/TESTING (MIGHT HAVE ALREADY INTEGRATED INTO API SERVICE)----------------------------
------------------------HAVE NOT TOUCHED ANY OF BELOW SINCE LAST YEAR (this is somewhat manual game analysis---------------------------------


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






