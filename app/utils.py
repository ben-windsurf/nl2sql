import pandas as pd
import re
from typing import List, Any

def format_currency_usd(value: Any) -> str:
    """Format a numeric value as USD currency."""
    if pd.isna(value) or value is None:
        return "$0.00"
    
    try:
        # Convert to float if it's not already
        num_value = float(value)
        # Format with commas and 2 decimal places
        return f"${num_value:,.2f}"
    except (ValueError, TypeError):
        return str(value)

def identify_financial_columns(df: pd.DataFrame) -> List[str]:
    """Identify columns that likely contain financial data based on column names and content."""
    financial_keywords = [
        'price', 'cost', 'revenue', 'sales', 'total', 'amount', 'value', 
        'spent', 'income', 'profit', 'loss', 'fee', 'charge', 'payment',
        'avg_order_value', 'aov', 'unit_price', 'total_spent'
    ]
    
    financial_columns = []
    
    for col in df.columns:
        col_lower = col.lower()
        
        # Check if column name contains financial keywords
        if any(keyword in col_lower for keyword in financial_keywords):
            financial_columns.append(col)
            continue
            
        # Check if column contains numeric data that looks like currency
        if df[col].dtype in ['float64', 'int64', 'float32', 'int32']:
            # Sample a few non-null values to see if they look like currency
            sample_values = df[col].dropna().head(10)
            if len(sample_values) > 0:
                # If values are generally > 0 and have reasonable currency-like ranges
                if sample_values.min() >= 0 and sample_values.max() < 1000000:
                    # Additional heuristic: if most values have decimal places or are whole dollars
                    has_decimals = any(val != int(val) for val in sample_values if isinstance(val, (int, float)))
                    if has_decimals or col_lower in ['total', 'amount', 'value']:
                        financial_columns.append(col)
    
    return financial_columns

def format_dataframe_currency(df: pd.DataFrame) -> pd.DataFrame:
    """Format financial columns in a DataFrame as USD currency."""
    if df.empty:
        return df
    
    # Create a copy to avoid modifying the original
    formatted_df = df.copy()
    
    # Identify financial columns
    financial_cols = identify_financial_columns(formatted_df)
    
    # Format each financial column
    for col in financial_cols:
        formatted_df[col] = formatted_df[col].apply(format_currency_usd)
    
    return formatted_df
