@echo off
REM Get today's date in yy-mm-dd format
for /f "tokens=2 delims==" %%i in ('wmic os get localdatetime /value') do set datetime=%%i
set date1=%datetime:~2,2%-%datetime:~4,2%-%datetime:~6,2%

REM Create date2 as '20+date1'
set date2=20%date1%

REM Display the dates (for debugging purposes)
echo Date1: %date1%
echo Date2: %date2%

REM Run the scripts
REM Adjust the paths to where your Python scripts are stored

echo Running rundataPut.py...
python rundataPut.py

echo Running getTeamrecsplitPUT.py...
python getTeamrecsplitPUT.py

echo Running injuryscrape.py...
python injuryscrape.py

echo Running yesterdaysresults.py with params %date2% %date2%...
python yesterdaysresults.py %date2% %date2%

echo Running getgamessendtodb.py...
python getgamessendtodb.py

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
python fetchgameodds.py %date1%

echo Running scrapeteams.py...
python scrapeteams.py

echo Running pitchersbulksplits.py with param %date1%...
python pitchersbulksplits.py %date1%

echo Running hittervsPitcher.py...
python hittervsPitcher.py

REM echo Running hittersLast7.py...
REM python hittersLast7.py
echo Running hittersLast7.py with date %date1% and playoff flag set to true...
python hittersLast7.py --date %date1% --playoff True

echo All scripts completed.
pause
