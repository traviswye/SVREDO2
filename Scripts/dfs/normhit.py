import requests
import json

# Disable warnings for self-signed SSL certificates (if applicable)
requests.packages.urllib3.disable_warnings()

teams = [
    "LAD", "BAL", "MIL", "TOR", "CHC", "SEA", "NYM", "PIT", "NYY", "HOU",
    "DET", "ARI", "BOS", "SF", "CIN", "TEX", "ATH", "PHI", "KC", "CLE",
    "MIN", "ATL", "SD", "STL", "WSH", "TB", "LAA", "MIA", "FA", "CWS", "COL"
]

def fetch_team_hitters(team):
    """
    Fetch the hitter stats for a given team from the API endpoint.
    Expects a JSON list of hitter records.
    """
    url = f"https://localhost:44346/api/ProjectedHitterStats/team/{team}"
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

def compute_team_totals(hitters):
    """
    Aggregate team totals from the list of hitter records.
    Returns a dictionary with totals for AB, H, doubles, triples, HR, BB.
    """
    totals = {
        'ab': 0,
        'h': 0,
        'doubles': 0,
        'triples': 0,
        'hr': 0,
        'bb': 0
    }
    for hit in hitters:
        totals['ab'] += int(hit.get("ab", 0))
        totals['h']  += int(hit.get("h", 0))
        # Use the key "doubles" if available; otherwise try "2B"
        totals['doubles'] += int(hit.get("doubles", hit.get("2B", 0)))
        totals['triples'] += int(hit.get("triples", 0))
        totals['hr'] += int(hit.get("hr", 0))
        totals['bb'] += int(hit.get("bb", 0))
    return totals

def compute_team_stats(totals):
    """
    Given aggregated totals, compute BA, OBP, SLG, and OPS.
    """
    ab = totals['ab']
    h = totals['h']
    doubles = totals['doubles']
    triples = totals['triples']
    hr = totals['hr']
    bb = totals['bb']
    
    ba = h / ab if ab > 0 else 0
    
    # For OBP, assuming HBP=0 and SF=0
    obp = (h + bb) / (ab + bb) if (ab + bb) > 0 else 0
    
    singles = h - doubles - triples - hr
    total_bases = singles + (2 * doubles) + (3 * triples) + (4 * hr)
    slg = total_bases / ab if ab > 0 else 0
    
    ops = obp + slg
    
    return ba, obp, slg, ops

def main():
    team_stats = []  # list to store (team, total_ab, total_R, BA, OBP, SLG, OPS)
    
    for team in teams:
        hitters = fetch_team_hitters(team)
        if not hitters:
            print(f"No data returned for team {team}")
            continue
        
        totals = compute_team_totals(hitters)
        # Also sum R's from the records
        total_r = sum(int(hit.get("r", 0)) for hit in hitters)
        ba, obp, slg, ops = compute_team_stats(totals)
        
        team_stats.append({
            'team': team,
            'ab': totals['ab'],
            'r': total_r,
            'ba': ba,
            'obp': obp,
            'slg': slg,
            'ops': ops
        })
        print(f"{team}: AB = {totals['ab']}, R = {total_r}, BA = {ba:.3f}, OBP = {obp:.3f}, SLG = {slg:.3f}, OPS = {ops:.3f}")
    
    print("\nAggregated Hitter Stats by Team (sorted by AB descending):")
    print("Team     AB    R     BA     OBP    SLG    OPS")
    for ts in sorted(team_stats, key=lambda x: x['ab'], reverse=True):
        print(f"{ts['team']:<8} {ts['ab']:5d}  {ts['r']:4d}  {ts['ba']:.3f}  {ts['obp']:.3f}  {ts['slg']:.3f}  {ts['ops']:.3f}")

if __name__ == "__main__":
    main()
