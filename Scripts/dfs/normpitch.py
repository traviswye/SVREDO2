import requests
import json

# Disable warnings for self-signed SSL (if applicable)
requests.packages.urllib3.disable_warnings()

# List of teams to process
teams = [
    "LAD", "BAL", "MIL", "TOR", "CHC", "SEA", "NYM", "PIT", "NYY", "HOU",
    "DET", "ARI", "BOS", "SF", "CIN", "TEX", "ATH", "PHI", "KC", "CLE",
    "MIN", "ATL", "SD", "STL", "WSH", "TB", "LAA", "MIA", "FA", "CWS", "COL"
]

# Set your target thresholds
TARGET_MIN = 1440.0
TARGET_MAX = 1460.0

def fetch_team(team):
    """
    Fetch the team roster from the API endpoint.
    Expects a JSON list of pitcher records.
    """
    url = f"https://localhost:44346/api/ProjectedPitcherStats/team/{team}"
    try:
        response = requests.get(url, verify=False)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching team {team}: {response.status_code}")
            return []
    except Exception as e:
        print(f"Exception while fetching team {team}: {e}")
        return []

def adjust_team(roster):
    """
    Adjust the team roster based on IP thresholds and business rules.
    Returns a tuple of (selected roster, total IP).
    Uses the following logic:
      1. Core players (miLB == 'no') are added first.
      2. If total IP from core is below TARGET_MIN, add bench players (miLB == 'yes')
         in descending order of ip as long as total does not exceed TARGET_MAX.
      3. If core total is above TARGET_MIN, eliminate players who meet criteria:
            - bbrefId contains an underscore,
            - OR position is 'SP' and ip < 30.
         If still over TARGET_MIN, remove the lowest ip contributors until near TARGET_MIN.
    """
    # Use lower-case keys as in the API response
    core = [p for p in roster if p.get("miLB", "").lower() == "no"]
    bench = [p for p in roster if p.get("miLB", "").lower() == "yes"]

    total_ip = sum(float(p.get("ip", 0)) for p in core)
    selected = core.copy()

    print(f"  Core total IP: {total_ip:.1f} (from {len(core)} players)")
    print(f"  Bench candidates: {len(bench)}")

    # If core total is below target, add bench players (sorted by highest ip first)
    if total_ip < TARGET_MIN:
        bench_sorted = sorted(bench, key=lambda p: float(p.get("ip", 0)), reverse=True)
        for p in bench_sorted:
            candidate_ip = float(p.get("ip", 0))
            if total_ip < TARGET_MIN and (total_ip + candidate_ip) <= TARGET_MAX:
                selected.append(p)
                total_ip += candidate_ip
                print(f"    Adding bench player {p.get('name')} with ip={candidate_ip:.1f} | New total: {total_ip:.1f}")
    else:
        # If core total is over the threshold, remove players meeting elimination criteria:
        #    - bbrefId contains an underscore
        #    - OR (position is 'SP' and ip < 30)
        filtered = [
            p for p in core 
            if ('_' not in p.get("bbrefId", "")) and not (p.get("position") == "SP" and float(p.get("ip", 0)) < 30)
        ]
        total_ip = sum(float(p.get("ip", 0)) for p in filtered)
        selected = filtered.copy()
        print(f"  After elimination, core total IP: {total_ip:.1f} (from {len(filtered)} players)")
        # If still above TARGET_MIN, remove the smallest ip contributors until near TARGET_MIN.
        if total_ip > TARGET_MIN:
            selected_sorted = sorted(selected, key=lambda p: float(p.get("ip", 0)))
            for p in selected_sorted:
                if total_ip > TARGET_MIN:
                    removed_ip = float(p.get("ip", 0))
                    total_ip -= removed_ip
                    selected.remove(p)
                    print(f"    Removing {p.get('name')} with ip={removed_ip:.1f} | New total: {total_ip:.1f}")
                else:
                    break

    return selected, total_ip

def main():
    team_totals = []  # List to store (team, total_ip, total_ER, total_W, total_L, team_ERA)
    for team in teams:
        print(f"\nProcessing team: {team}")
        roster = fetch_team(team)
        if not roster:
            print(f"  No data returned for team {team}")
            continue

        selected, total_ip = adjust_team(roster)
        # Sum additional stats over the selected roster
        total_ER = sum(float(p.get("er", 0)) for p in selected)
        total_W = sum(int(p.get("w", 0)) for p in selected)
        total_L = sum(int(p.get("l", 0)) for p in selected)
        # Compute team ERA from aggregated ER and IP (if total_ip > 0)
        team_ERA = (total_ER * 9) / total_ip if total_ip > 0 else 0

        print(f"Team: {team} | Adjusted Total IP: {total_ip:.1f} | Number of Pitchers: {len(selected)}")
        print(f"           Total ER: {total_ER:.1f} | Total W: {total_W} | Total L: {total_L} | Team ERA: {team_ERA:.2f}")
        # Optionally, print selected pitchers' details:
        for p in selected:
            name = p.get("name", "Unknown")
            ip = p.get("ip", "0")
            milb = p.get("miLB", "N/A")
            bbrefid = p.get("bbrefId", "")
            pos = p.get("position", "N/A")
            print(f"  - {name}: ip={ip}, miLB={milb}, bbrefId={bbrefid}, position={pos}")
        team_totals.append((team, total_ip, total_ER, total_W, total_L, team_ERA))
    
    # Sort team totals in descending order by total_ip and print them out.
    print("\nAdjusted Team Totals (Descending Order):")
    print("Team     IP       ER       W   L   ERA")
    for team, total, er, w, l, era in sorted(team_totals, key=lambda x: x[1], reverse=True):
        print(f"{team:<8} {total:7.1f}   {er:7.1f}  {w:3d} {l:3d} {era:6.2f}")

if __name__ == "__main__":
    main()
