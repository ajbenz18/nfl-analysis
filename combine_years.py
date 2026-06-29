import pandas as pd
import numpy as np

def combine_weighted_csvs(csv_paths: list, primary_key: str, weight_col: str, output_csv: str) -> pd.DataFrame:
    """
    Combines CSVs via weighted average while preserving multi-row category headers.
    """
    
    # ==========================================
    # STEP 1: Map the Multi-Row Headers
    # ==========================================
    # Read just 0 rows of data from the first file using header=[0,1] to capture the structure
    header_df = pd.read_csv(csv_paths[0], header=[0, 1], nrows=0)
    
    # Create a dictionary mapping the bottom column to the top category
    # Example: {'Tm': 'BASIC', 'ATT': 'BASE', 'EPA': 'ANALYTICS'}
    header_mapping = {}
    for top_col, sub_col in header_df.columns:
        # Clean up any blank top-level headers pandas might have labeled as "Unnamed"
        if "Unnamed" in top_col:
            top_col = ""
        header_mapping[sub_col] = top_col

    # ==========================================
    # STEP 2: Process the Data (Standard Logic)
    # ==========================================
    dfs = []
    for path in csv_paths:
        # Read normally, skipping the category row for the math
        df = pd.read_csv(path, header=1, thousands=',')
        dfs.append(df)
        
    combined_df = pd.concat(dfs, ignore_index=True)
    combined_df[weight_col] = pd.to_numeric(combined_df[weight_col], errors='coerce')
    combined_df = combined_df.dropna(subset=[primary_key, weight_col])
    
    numeric_cols = combined_df.select_dtypes(include=[np.number]).columns.tolist()
    if primary_key in numeric_cols: numeric_cols.remove(primary_key)
    if weight_col in numeric_cols: numeric_cols.remove(weight_col)
        
    for col in numeric_cols:
        combined_df[f'{col}_weighted'] = combined_df[col] * combined_df[weight_col]
        
    agg_funcs = {weight_col: 'sum'} 
    for col in numeric_cols:
        agg_funcs[f'{col}_weighted'] = 'sum'
        
    grouped = combined_df.groupby(primary_key).agg(agg_funcs)
    
    result_df = pd.DataFrame(index=grouped.index)
    for col in numeric_cols:
        result_df[col] = grouped[f'{col}_weighted'] / grouped[weight_col]
        
    result_df[f'Total_{weight_col}'] = grouped[weight_col]
    result_df = result_df.reset_index()
    
    # ==========================================
    # STEP 3: Reattach the Top Headers
    # ==========================================
    multi_index_tuples = []
    
    for col in result_df.columns:
        if col == f'Total_{weight_col}':
            # Put the new Total column in the same category as the original weight column
            top_level = header_mapping.get(weight_col, 'CALCULATED')
        else:
            # Look up the top-level category from our dictionary
            top_level = header_mapping.get(col, '')
            
        multi_index_tuples.append((top_level, col))
        
    # Apply the two-tier structure back to the dataframe columns
    result_df.columns = pd.MultiIndex.from_tuples(multi_index_tuples)
    
    # ==========================================
    # STEP 4: Save
    # ==========================================
    # index=False correctly writes both header rows without adding row numbers
    result_df.to_csv(output_csv, index=False)
    print(f"Success! Weighted data with dual headers saved to: {output_csv}")
    
    return result_df