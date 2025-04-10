import pandas as pd
import numpy as np
import statsmodels.api as sm
import os
import glob
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

def load_latest_data(directory="output"):
    """
    Load the most recent Baseball Savant stats CSV file from the output directory
    
    Args:
        directory (str): Directory to search for CSV files
        
    Returns:
        pandas.DataFrame: Loaded data or None if no files found
    """
    # Find all CSV files in the directory
    csv_files = glob.glob(os.path.join(directory, "baseball_savant_stats_*.csv"))
    
    if not csv_files:
        print(f"No CSV files found in {directory}. Please run the scraper first.")
        return None
    
    # Sort files by creation time (most recent first)
    csv_files.sort(key=os.path.getmtime, reverse=True)
    
    # Load the most recent file
    latest_file = csv_files[0]
    print(f"Loading data from {latest_file}")
    
    # Load the CSV file
    df = pd.read_csv(latest_file)
    return df

def prepare_data(df):
    """
    Prepare the data for regression analysis
    
    Args:
        df (pandas.DataFrame): Raw Baseball Savant data
        
    Returns:
        pandas.DataFrame: Prepared data for analysis
    """
    # Convert percentage strings to float values
    for col in ['HR%', 'K%', 'BB%', 'HardHit%']:
        if col in df.columns:
            df[col] = df[col].str.rstrip('%').astype('float') / 100.0
    
    # Calculate Barrel% (Brls / PA)
    if 'Brls' in df.columns and 'PA' in df.columns:
        df['Barrel%'] = df['Brls'].astype(float) / df['PA'].astype(float)
    
    # For demonstration purposes, we'll use a simple formula to estimate actual_xwOBA
    # In a real scenario, you'd have this data from another source
    # A very simplified formula: xwOBA ≈ xBA + 1.3*HR% - 0.7*K% + 0.3*BB%
    df['actual_xwOBA'] = (
        df['xBA'].astype(float) + 
        1.3 * df['HR%'].astype(float) - 
        0.7 * df['K%'].astype(float) + 
        0.3 * df.get('BB%', 0).astype(float)
    )
    
    return df

def run_regression(df):
    """
    Run OLS regression on the data
    
    Args:
        df (pandas.DataFrame): Prepared data
        
    Returns:
        statsmodels.regression.linear_model.RegressionResultsWrapper: Regression results
    """
    # Define features and target
    features = ["EV (MPH)", "LA (°)", "Barrel%", "HardHit%", "xBA", "HR%", "K%"]
    
    # Check if all features exist in the dataframe
    missing_features = [feature for feature in features if feature not in df.columns]
    if missing_features:
        print(f"Warning: Missing features: {missing_features}")
        features = [feature for feature in features if feature in df.columns]
    
    if not features:
        print("Error: No valid features available for regression")
        return None
    
    X = df[features]
    X = sm.add_constant(X)  # Add intercept term
    y = df["actual_xwOBA"]
    
    # Run regression
    model = sm.OLS(y, X).fit()
    
    return model, X, y, features

def generate_visualizations(df, model, X, y, features):
    """
    Generate visualizations for the regression analysis
    
    Args:
        df (pandas.DataFrame): Data
        model: Fitted regression model
        X: Feature matrix
        y: Target variable
        features: List of feature names
    """
    # Create output directory for visualizations
    viz_dir = "output/visualizations"
    os.makedirs(viz_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Actual vs Predicted plot
    plt.figure(figsize=(10, 6))
    plt.scatter(y, model.predict(X), alpha=0.7)
    
    # Add perfect prediction line
    min_val = min(y.min(), model.predict(X).min())
    max_val = max(y.max(), model.predict(X).max())
    plt.plot([min_val, max_val], [min_val, max_val], 'r--')
    
    plt.xlabel('Actual xwOBA')
    plt.ylabel('Predicted xwOBA')
    plt.title('Actual vs Predicted xwOBA')
    
    # Add player names as annotations for the top 5 and bottom 5 differences
    df['predicted_xwOBA'] = model.predict(X)
    df['xwOBA_diff'] = abs(df['actual_xwOBA'] - df['predicted_xwOBA'])
    
    # Top 5 differences
    top_diff = df.nlargest(5, 'xwOBA_diff')
    for _, row in top_diff.iterrows():
        plt.annotate(row['Name'], 
                     (row['actual_xwOBA'], row['predicted_xwOBA']),
                     xytext=(5, 5), textcoords='offset points')
    
    plt.tight_layout()
    plt.savefig(f"{viz_dir}/actual_vs_predicted_{timestamp}.png")
    
    # 2. Feature importance plot
    plt.figure(figsize=(12, 6))
    
    # Get feature importance (absolute t-statistic values)
    importance = abs(model.tvalues[1:])  # Skip the constant
    
    # Create a horizontal bar chart
    plt.barh(features, importance)
    plt.xlabel('|t-statistic|')
    plt.ylabel('Feature')
    plt.title('Feature Importance')
    plt.tight_layout()
    plt.savefig(f"{viz_dir}/feature_importance_{timestamp}.png")
    
    # 3. Correlation matrix
    plt.figure(figsize=(10, 8))
    correlation_matrix = df[features + ['actual_xwOBA']].corr()
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt=".2f")
    plt.title('Feature Correlation Matrix')
    plt.tight_layout()
    plt.savefig(f"{viz_dir}/correlation_matrix_{timestamp}.png")
    
    # 4. Individual feature vs xwOBA plots
    for feature in features:
        plt.figure(figsize=(8, 6))
        plt.scatter(df[feature], df['actual_xwOBA'], alpha=0.7)
        
        # Add trend line
        x = df[feature]
        z = np.polyfit(x, df['actual_xwOBA'], 1)
        p = np.poly1d(z)
        plt.plot(x, p(x), "r--")
        
        plt.xlabel(feature)
        plt.ylabel('actual_xwOBA')
        plt.title(f'{feature} vs xwOBA')
        plt.tight_layout()
        plt.savefig(f"{viz_dir}/{feature.replace(' ', '_')}_{timestamp}.png")
        plt.close()

def save_results(df, model, timestamp):
    """
    Save regression results and predictions to CSV
    
    Args:
        df (pandas.DataFrame): Data with predictions
        model: Fitted regression model
        timestamp (str): Timestamp for file naming
    """
    # Create results directory
    results_dir = "output/results"
    os.makedirs(results_dir, exist_ok=True)
    
    # Save the model summary to a text file
    with open(f"{results_dir}/regression_summary_{timestamp}.txt", "w") as f:
        f.write(str(model.summary()))
    
    # Save predictions to CSV
    results_df = df[['BBRefID', 'Name', 'Team', 'actual_xwOBA', 'predicted_xwOBA', 'xwOBA_diff']]
    results_df = results_df.sort_values('xwOBA_diff', ascending=False)
    results_df.to_csv(f"{results_dir}/xwOBA_predictions_{timestamp}.csv", index=False)
    
    # Also save a CSV with overperformers and underperformers
    df['performance'] = df['actual_xwOBA'] - df['predicted_xwOBA']
    
    # Top 10 overperformers (actual > predicted)
    overperformers = df.nlargest(10, 'performance')
    overperformers.to_csv(f"{results_dir}/overperformers_{timestamp}.csv", index=False)
    
    # Top 10 underperformers (actual < predicted)
    underperformers = df.nsmallest(10, 'performance')
    underperformers.to_csv(f"{results_dir}/underperformers_{timestamp}.csv", index=False)

def main():
    # Load the data
    df = load_latest_data()
    
    if df is None:
        return
    
    # Check if we have at least a few data points
    if len(df) < 5:
        print(f"Not enough data points for regression analysis. Found only {len(df)} rows.")
        return
    
    print(f"Loaded {len(df)} player records. First few rows:")
    print(df.head())
    
    # Prepare the data
    df = prepare_data(df)
    
    # Run regression
    result = run_regression(df)
    if result is None:
        return
    
    model, X, y, features = result
    
    # Create timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Print regression summary
    print("\nRegression Summary:")
    print(model.summary())
    
    # Generate predicted xwOBA
    df['predicted_xwOBA'] = model.predict(X)
    df['xwOBA_diff'] = abs(df['actual_xwOBA'] - df['predicted_xwOBA'])
    
    # Print actual vs predicted for a few examples
    print("\nSample of Actual vs Predicted xwOBA:")
    sample = df[['Name', 'Team', 'actual_xwOBA', 'predicted_xwOBA']].head(10)
    print(sample)
    
    # Generate visualizations
    try:
        import matplotlib
        import seaborn
        print("\nGenerating visualizations...")
        generate_visualizations(df, model, X, y, features)
    except ImportError:
        print("Matplotlib or Seaborn not available. Skipping visualizations.")
    
    # Save results
    save_results(df, model, timestamp)
    
    print("\nAnalysis complete. Results saved to output/results directory.")

if __name__ == "__main__":
    main()