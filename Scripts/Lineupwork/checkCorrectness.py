import requests

# Define your API base URL
API_BASE_URL = "https://localhost:44346/api"

# Define teams (or retrieve dynamically if you have that option)
teams = [
    "Diamondbacks", "Braves", "Orioles", "Red Sox", "White Sox", "Cubs", "Reds", "Guardians",
    "Rockies", "Tigers", "Astros", "Royals", "Angels", "Dodgers", "Marlins", "Brewers", 
    "Twins", "Yankees", "Mets", "Athletics", "Phillies", "Pirates", "Padres", "Giants", 
    "Mariners", "Cardinals", "Rays", "Rangers", "Jays", "Nationals"
]

# Actual lineups for today
actual_lineups = {
    "Nationals": ['callal01', 'abramcj01', 'yepezju01', 'woodja02', 'chapran01', 'vargail01', 'adamsri03', 'garcilo02', 'youngja03'],
    "Phillies": ['schwaky01', 'turnetr01', 'harpebr03', 'bohmal01', 'casteni01', 'realmjt01', 'wilsowe01', 'sosaed01', 'rojasjo02'],
    "Royals": ['garcima02', 'wittbo02', 'pasquvi01', 'perezsa02', 'renfrohu01', 'fermifr01', 'hampg01', 'dejonpa01', 'blancda01'],
    "Reds": ['indiajo01', 'delacel01', 'stephty01', 'friedtj01', 'steersp01', 'candeje01', 'franty01', 'fraleja01', 'martenoe01'],
    "Twins": ['castrwi01', 'larnatr01', 'lewisro01', 'wallnma01', 'santaca01', 'keplema01', 'julieed01', 'vazquch01', 'martaau01'],
    "Rangers": ['semiema01', 'seageco01', 'lownana01', 'garcia01', 'langfwy01', 'jungjo01', 'heimjo01', 'kellca01', 'taverle01'],
    "Giants": ['fitzgty01', 'wadela01', 'ramoshe02', 'confomi01', 'chapmma01', 'yastrmi01', 'bailepa01', 'wisely01', 'mccragr01'],
    "Athletics": ['butlelaw01', 'rooke02', 'bledajj01', 'andujmi01', 'langesh01', 'browns01', 'gelofza01', 'hernad01', 'schuema01'],
    "White Sox": ['lopezni02', 'roberlu02', 'beninan01', 'vaughan01', 'sheetga01', 'sosale01', 'fletcdo01', 'robich01', 'baldwbr01'],
    "Astros": ['altuvjo01', 'alvaryo01', 'diazyai01', 'penaje01', 'singljo02', 'caratvi01', 'meyerja01', 'whitcsh01', 'dubonma01'],
    "Dodgers": ['ohtansh01', 'bettmo01', 'freemfr01', 'smithwi05', 'luxga01', 'rohasmi02', 'pagesan01', 'kiermke01', 'hernaen02'],
    "Cardinals": ['winnma01', 'burleal01', 'contrwi01', 'donovbr01', 'arenano01', 'nootbla01', 'goldspa01', 'gormano01', 'scottvi01'],
    "Guardians": ['kwanst01', 'brennwi01', 'ramirjo01', 'naylojo02', 'thomala01', 'gimenan01', 'freemty01', 'naylobo01', 'roccibr01'],
    "Brewers": ['turanbr01', 'chourja01', 'sanchga01', 'contrwi01', 'adamewi01', 'bauerja01', 'frelick01', 'mitchga01', 'ortizjo01'],
    "Red Sox": ['duranja01', 'refsiro01', 'oneilty01', 'deverra01', 'janseda01', 'gonzar01', 'casastr01', 'wongco01', 'raface01'],
    "Orioles": ['cowseco01', 'santaant01', 'hendegu01', 'ohearry01', 'mount00', 'hollija01', 'mullxce01', 'uriasra01', 'mccanja02'],
    "Padres": ['profar01', 'solando01', 'bogax01', 'machama01', 'croneja01', 'kimha01', 'peralda01', 'campulu01', 'johnsb01'],
    "Rockies": ['blackch01', 'tovare01', 'doylbr01', 'mcmahry01', 'rodger01', 'toglimi01', 'caveja01', 'beckjo01', 'romodr01'],
    "Braves": ['harismi02', 'rileyau01', 'ozunama01', 'olsonma01', 'daraut01', 'laure00', 'kelenja01', 'arciaor01', 'merriw01'],
    "Angels": ['wardta01', 'netoza01', 'schan01', 'pillar01', 'ohopplo01', 'drurybr01', 'adeljo01', 'stefami01', 'lopezja01'],
    "Mariners": ['roblevi01', 'arozara01', 'rodriju01', 'polanjo01', 'turneju01', 'mooredy01', 'hanigmi01', 'garvemi01', 'rivasle01'],
    "Pirates": ['kineris01', 'cruzon01', 'bartjo01', 'telrro01', 'delacr01', 'hayeske01', 'taylomi01', 'baejih01', 'triolja01'],
    "Yankees": ['torreg01', 'sotoju01', 'judgeaa01', 'wellsa01', 'stantgi01', 'verdual01', 'volpean01', 'ricebe01', 'cabreos01'],
    "Tigers": ['vierlma01', 'ibanera01', 'malloju01', 'keithco01', 'dingldi01', 'torkesp01', 'jungja01', 'baezja01', 'mckinza01'],
    "Blue Jays": [
        "sprige01", "varshda01", "guerrvl02", "kirkaa01", "clemeer01", 
        "wagnwi01", "schneda01", "jimenle01", "bargera01"
    ],
    "Cubs": ['happia01', 'buschmi01', 'suzukse01', 'belling01', 'pareisa01', 'hoernni01', 'swansda01', 'crowpe01', 'amayami01'],
    "Diamondbacks": ['marteke01', 'mccarja01', 'gurri01', 'belljo01', 'grichra01', 'suareeu01', 'newmake01', 'perdoge01', 'herrejo01'],
    "Rays": ['diazya01', 'lowebr01', 'morelch01', 'lowejo01', 'caminju01', 'carldy01', 'delucjo01', 'wallsta01', 'jacksal01'],
    "Marlins": ['edwarxi01', 'burgeja01', 'sanchje01', 'bridejo01', 'hillde01', 'stoweka01', 'lopezot01', 'brujavi01', 'forteni01'],
    "Mets": ['lindofr01', 'vientma01', 'nimmobr01', 'martija02', 'alonspe01', 'winkeje01', 'alvarfr01', 'mcneije01', 'baderha01']
}
def get_predicted_lineup(team):
    # API call to get predicted lineup
    response = requests.get(f"{API_BASE_URL}/Lineups/predictLineup/{team}?recentGames=10&weightRecent=3", verify=False)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def calculate_correctness(predicted, actual):
    correct_count = sum([1 for i in range(9) if predicted.get(f'batting{i+1}') == actual[i]])
    return correct_count / 9 * 100  # Return percentage of correctness

def calculate_first_6_correctness(predicted, actual):
    correct_count = sum([1 for i in range(6) if predicted.get(f'batting{i+1}') == actual[i]])
    return correct_count / 6 * 100  # Return percentage of correctness for the first 6 positions

def calculate_first_6_correctness_without_order(predicted, actual):
    predicted_first_6 = {predicted.get(f'batting{i+1}') for i in range(6)}
    actual_first_6 = set(actual[:6])
    correct_count = len(predicted_first_6.intersection(actual_first_6))
    return correct_count / 6 * 100  # Return percentage of correctness for the first 6 players regardless of order

def main():
    for team in teams:
        print(f"Processing {team}...")
        
        # Get predicted lineup
        predicted_lineups = get_predicted_lineup(team)
        
        if predicted_lineups:
            # Check both vsLHP and vsRHP lineups
            for matchup_type in ['vsLHP', 'vsRHP']:
                predicted_lineup = predicted_lineups.get(matchup_type)
                if predicted_lineup:
                    actual_lineup = actual_lineups.get(team)
                    if actual_lineup:
                        # Calculate overall correctness
                        correctness = calculate_correctness(predicted_lineup, actual_lineup)
                        first_6_correctness = calculate_first_6_correctness(predicted_lineup, actual_lineup)
                        first_6_no_order_correctness = calculate_first_6_correctness_without_order(predicted_lineup, actual_lineup)
                        
                        print(f"{team} {matchup_type} Correctness: {correctness:.2f}%")
                        print(f"{team} {matchup_type} First 6 Positions Correctness (with order): {first_6_correctness:.2f}%")
                        print(f"{team} {matchup_type} First 6 Positions Correctness (without order): {first_6_no_order_correctness:.2f}%")
                        print(f"Predicted ({matchup_type}): {predicted_lineup}")
                        print(f"Actual: {actual_lineup}")
                    else:
                        print(f"No actual lineup found for {team}")
                else:
                    print(f"No {matchup_type} lineup found for {team}")
        else:
            print(f"Failed to retrieve predicted lineup for {team}")

if __name__ == "__main__":
    main()