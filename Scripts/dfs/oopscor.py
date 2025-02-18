import pandas as pd
import numpy as np
from scipy import stats
import time
import warnings
warnings.filterwarnings('ignore')

class BaseballData:
    def __init__(self, start_year: int, end_year: int):
        self.start_year = start_year
        self.end_year = end_year
        self.raw_data = []
        self.fetch_all_data()
        
    def fetch_all_data(self) -> None:
        """Fetch data for all years once."""
        print("Fetching baseball data...")
        for year in range(self.start_year, self.end_year + 1):
            try:
                tables = pd.read_html(f"https://www.baseball-reference.com/leagues/majors/{year}.shtml", 
                                    attrs={'id': 'teams_standard_batting'})
                if not tables:
                    continue
                    
                df = tables[0]
                
                for _, row in df.iterrows():
                    if 'League Average' in str(row['Tm']) or pd.isna(row['Tm']):
                        continue
                        
                    try:
                        team_data = {
                            'Team': row['Tm'],
                            'Year': year,
                            'R/G': float(row['R/G']),
                            'OBP': float(row['OBP']),
                            'SLG': float(row['SLG'])
                        }
                        self.raw_data.append(team_data)
                        
                    except (ValueError, KeyError):
                        continue
                        
            except Exception as e:
                print(f"Error processing {year}: {e}")
                
            time.sleep(2)  # Be respectful to the server
            
        print(f"Data collection complete. Found {len(self.raw_data)} team seasons.")

def analyze_yearly_correlations(data: list) -> pd.DataFrame:
    """Analyze correlations for each individual year."""
    df = pd.DataFrame(data)
    years = sorted(df['Year'].unique())
    
    yearly_results = []
    print("\nYear-by-Year Analysis:")
    print("----------------------------------------")
    
    for year in years:
        year_data = df[df['Year'] == year]
        year_data['OPS'] = year_data['OBP'] + year_data['SLG']
        
        # Test each multiplier for this year
        best_mult = None
        best_corr = -1
        best_diff = 0
        
        # Calculate baseline OPS correlation
        ops_corr, ops_p = stats.pearsonr(year_data['R/G'], year_data['OPS'])
        
        # Test multipliers with expanded range
        for mult in np.arange(1.4, 2.01, 0.01):
            year_data['oOPS'] = (mult * year_data['OBP']) + year_data['SLG']
            oops_corr, oops_p = stats.pearsonr(year_data['R/G'], year_data['oOPS'])
            
            if oops_corr > best_corr:
                best_corr = oops_corr
                best_mult = mult
                best_diff = oops_corr - ops_corr
        
        yearly_results.append({
            'Year': year,
            'Sample_Size': len(year_data),
            'OPS_Correlation': ops_corr,
            'Best_Multiplier': best_mult,
            'Best_oOPS_Correlation': best_corr,
            'Improvement': best_diff
        })
        
        print(f"\n{year} Results:")
        print(f"Sample size: {len(year_data)}")
        print(f"OPS Correlation:  {ops_corr:.8f}")
        print(f"Best Multiplier:  {best_mult:.2f}")
        print(f"oOPS Correlation: {best_corr:.8f}")
        print(f"Improvement:      {best_diff:.8f}")
    
    return pd.DataFrame(yearly_results)

def calculate_rg_formula(data: list, best_multiplier: float) -> tuple:
    """Calculate the formula to convert oOPS to R/G using linear regression."""
    df = pd.DataFrame(data)
    
    # Calculate oOPS using best multiplier
    df['oOPS'] = (best_multiplier * df['OBP']) + df['SLG']
    
    # Perform linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(df['oOPS'], df['R/G'])
    
    # Calculate R-squared
    r_squared = r_value ** 2
    
    # Calculate mean absolute error
    df['predicted_rg'] = slope * df['oOPS'] + intercept
    mae = np.mean(np.abs(df['R/G'] - df['predicted_rg']))
    
    return slope, intercept, r_squared, mae

def test_multiplier_range(data: list, start_mult: float = 1.0, 
                         end_mult: float = 3.0, 
                         step: float = 0.01) -> pd.DataFrame:
    """Test different multiplier values using the same dataset."""
    print("\nOverall Analysis (All Years Combined):")
    print("----------------------------------------")
    
    results = []
    multipliers = np.arange(start_mult, end_mult + step, step)
    
    # First calculate baseline OPS correlation
    df = pd.DataFrame(data)
    df['OPS'] = df['OBP'] + df['SLG']
    baseline_corr, baseline_p = stats.pearsonr(df['R/G'], df['OPS'])
    
    print(f"\nBaseline OPS Correlation: {baseline_corr:.8f}")
    print(f"Sample size: {len(data)}")
    
    for mult in multipliers:
        df['oOPS'] = (mult * df['OBP']) + df['SLG']
        oops_corr, oops_p = stats.pearsonr(df['R/G'], df['oOPS'])
        
        results.append({
            'multiplier': mult,
            'oOPS_correlation': oops_corr,
            'OPS_correlation': baseline_corr,
            'correlation_diff': oops_corr - baseline_corr,
            'oOPS_p_value': oops_p
        })
    
    results_df = pd.DataFrame(results)
    best_result = results_df.loc[results_df['oOPS_correlation'].idxmax()]
    
    print(f"\nBest Overall Multiplier: {best_result['multiplier']:.2f}")
    print(f"Best oOPS Correlation: {best_result['oOPS_correlation']:.8f}")
    print(f"OPS Correlation:       {best_result['OPS_correlation']:.8f}")
    print(f"Improvement:           {best_result['correlation_diff']:.8f}")
    
    # Calculate and print the R/G prediction formula
    slope, intercept, r_squared, mae = calculate_rg_formula(data, best_result['multiplier'])
    print("\nR/G Prediction Formula:")
    print("----------------------------------------")
    print(f"R/G = {slope:.4f} × oOPS + {intercept:.4f}")
    print(f"R² = {r_squared:.4f}")
    print(f"Mean Absolute Error: {mae:.4f} runs per game")
    print(f"\nTo use this formula:")
    print(f"1. Calculate oOPS = ({best_result['multiplier']:.2f} × OBP) + SLG")
    print(f"2. Then calculate R/G = {slope:.4f} × oOPS + {intercept:.4f}")
    
    print("\nAll Multiplier Results:")
    print("----------------------------------------")
    pd.set_option('display.float_format', lambda x: '{:.8f}'.format(x))
    print(results_df.to_string())
    
    return results_df

if __name__ == "__main__":
    # Fetch data once
    baseball_data = BaseballData(2023, 2024)
    
    # First do year-by-year analysis
    yearly_results = analyze_yearly_correlations(baseball_data.raw_data)
    
    # Then do overall analysis
    results = test_multiplier_range(baseball_data.raw_data)
    
    # Print summary
    print("\nSummary of Findings:")
    print("----------------------------------------")
    print(f"Total seasons analyzed: {len(baseball_data.raw_data)}")
    print(f"Years covered: {baseball_data.start_year}-{baseball_data.end_year}")
    print("\nYearly Results Summary:")
    pd.set_option('display.float_format', lambda x: '{:.8f}'.format(x))
    print(yearly_results.to_string(index=False))