import requests
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.calibration import CalibratedClassifierCV

# Define the endpoints
evaluation_endpoint = 'https://localhost:44346/api/Evaluation/evaluateNRFI/2024-08-12'
pitching_average_endpoint = 'https://localhost:44346/api/PitchingAverage/2024'

# Fetch data from the evaluation endpoint
response = requests.get(evaluation_endpoint, verify=False)  # verify=False to ignore SSL certs
if response.status_code == 200:
    games_data = response.json()
else:
    print(f"Failed to fetch data from evaluation endpoint: {response.status_code}")
    exit()

# Fetch data from the pitching average endpoint
response = requests.get(pitching_average_endpoint, verify=False)
if response.status_code == 200:
    pitching_average_data = response.json()
else:
    print(f"Failed to fetch data from pitching average endpoint: {response.status_code}")
    exit()

# Convert the fetched data to pandas DataFrames for easier manipulation
games_df = pd.json_normalize(games_data)
pitching_average_df = pd.DataFrame(pitching_average_data)

# Now using the correct column names
games_df['home_pitcher_above_avg_era'] = games_df['homePitcher.stats.era'] < pitching_average_df['era'].mean()
games_df['away_pitcher_above_avg_era'] = games_df['awayPitcher.stats.era'] < pitching_average_df['era'].mean()

games_df['home_pitcher_above_avg_so9'] = games_df['homePitcher.stats.sO9'] > pitching_average_df['sO9'].mean()
games_df['away_pitcher_above_avg_so9'] = games_df['awayPitcher.stats.sO9'] > pitching_average_df['sO9'].mean()

# Select features to train the model
features = ['homeTeamNRFI.runsPerFirst', 'awayTeamNRFI.runsPerFirst',
            'venueDetails.parkFactorRating', 'home_pitcher_above_avg_era',
            'away_pitcher_above_avg_era', 'home_pitcher_above_avg_so9',
            'away_pitcher_above_avg_so9']

X = games_df[features]
y = (games_df['homePitcher.firstInningStats.er'] + games_df['awayPitcher.firstInningStats.er'] > 0).astype(int)  # Target: 1 if any run is scored in the first inning

# Manual oversampling of the minority class
df_majority = games_df[y == 1]
df_minority = games_df[y == 0]

df_minority_oversampled = df_minority.sample(len(df_majority), replace=True, random_state=42)
games_df_balanced = pd.concat([df_majority, df_minority_oversampled])

X_balanced = games_df_balanced[features]
y_balanced = (games_df_balanced['homePitcher.firstInningStats.er'] + games_df_balanced['awayPitcher.firstInningStats.er'] > 0).astype(int)

# Prepare the data
scaler = StandardScaler()
X_rescaled = scaler.fit_transform(X_balanced)

# Train a RandomForestClassifier model with calibration
X_train, X_test, y_train, y_test = train_test_split(X_rescaled, y_balanced, test_size=0.2, random_state=42)
model = RandomForestClassifier(random_state=42)
calibrated_model = CalibratedClassifierCV(model, method='sigmoid')
calibrated_model.fit(X_train, y_train)

# Make predictions for today's games with probabilities
X_scaled = scaler.transform(X)
predictions_proba = calibrated_model.predict_proba(X_scaled)
games_df['probability_nrfi'] = predictions_proba[:, 1]  # Probability of NRFI (class 1)

# Rank the games by the probability of NRFI and output the top 50%
games_df_sorted = games_df.sort_values(by='probability_nrfi', ascending=False)
top_50_percent = games_df_sorted.head(int(len(games_df_sorted) ))

# Output the predictions with confidence
for i, row in top_50_percent.iterrows():
    print(f"Game: {row['homeTeam']} vs {row['awayTeam']} at {row['venue']}")
    print(f"Prediction: NRFI, Confidence: {row['probability_nrfi']:.2f}\n")
