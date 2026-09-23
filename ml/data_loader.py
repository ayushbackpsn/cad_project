"""
Data Loader for Bitbrains Dataset (fastStorage / GWA-T-12)
Loads and explores cloud workload datasets
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path


class BitbrainsDataLoader:
    """Loads and handles Bitbrains fastStorage & GWA-T-12 dataset"""
    
    def __init__(self, data_path='data/fastStorage'):
        # Check fallback if fastStorage doesn't exist
        primary_path = Path(data_path)
        if not primary_path.exists() and Path('data/bitbrains').exists():
            self.data_path = Path('data/bitbrains')
        else:
            self.data_path = primary_path
            
        self.data = None
        
    def load_data(self, filename=None, max_files=10):
        """
        Load Bitbrains dataset (from fastStorage or bitbrains folder)
        
        Args:
            filename: Specific filename to load (e.g. '1.csv' or 'RND_5k.csv').
                      If None, loads up to `max_files` CSV files from data_path.
            max_files: Max number of CSV files to concatenate if filename is None.
        
        Expected columns:
        - Timestamp [ms]
        - CPU cores
        - CPU capacity provisioned [MHZ]
        - CPU usage [MHZ]
        - CPU usage [%]
        - Memory capacity provisioned [KB]
        - Memory usage [KB]
        - Disk read throughput [KB/s]
        - Disk write throughput [KB/s]
        - Network received throughput [KB/s]
        - Network transmitted throughput [KB/s]
        """
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data directory not found: {self.data_path}")
            
        csv_files = []
        if filename:
            target_file = self.data_path / filename
            if target_file.exists():
                csv_files = [target_file]
            else:
                raise FileNotFoundError(f"File not found: {target_file}")
        else:
            # Find available CSV files in directory
            all_csvs = sorted(list(self.data_path.glob("*.csv")), key=lambda p: (len(p.name), p.name))
            if not all_csvs:
                raise FileNotFoundError(f"No CSV files found in {self.data_path}")
            csv_files = all_csvs[:max_files]
            
        dfs = []
        for file_path in csv_files:
            try:
                # Try semicolon/tab delimiter first (fastStorage format)
                df = pd.read_csv(file_path, sep=r';\s*', engine='python')
                if len(df.columns) <= 1:
                    df = pd.read_csv(file_path)
                
                # Strip whitespace/tabs from column names
                df.columns = [c.strip() for c in df.columns]
                dfs.append(df)
            except Exception as e:
                print(f"Warning: Could not read {file_path}: {e}")
                
        if not dfs:
            raise ValueError(f"Failed to load any data from {self.data_path}")
            
        self.data = pd.concat(dfs, ignore_index=True)
        
        # Standardize column names
        self._standardize_columns()
        
        print(f"Loaded {len(self.data)} records from {len(csv_files)} file(s) in {self.data_path.name}")
        return self.data
    
    def _standardize_columns(self):
        """Standardize column names for easier access"""
        if self.data is None:
            return
            
        # Strip all whitespace/tabs from column names
        self.data.columns = [str(col).strip() for col in self.data.columns]
        
        # Map common column name variations
        column_mapping = {
            'Timestamp [ms]': 'timestamp',
            'CPU cores': 'cpu_cores',
            'CPU capacity provisioned [MHZ]': 'cpu_capacity_mhz',
            'CPU usage [MHZ]': 'cpu_usage_mhz',
            'CPU usage [%]': 'cpu_usage_percent',
            'Memory capacity provisioned [KB]': 'memory_capacity_kb',
            'Memory usage [KB]': 'memory_usage_kb',
            'Disk read throughput [KB/s]': 'disk_read_kb_s',
            'Disk write throughput [KB/s]': 'disk_write_kb_s',
            'Network received throughput [KB/s]': 'network_received_kb_s',
            'Network transmitted throughput [KB/s]': 'network_transmitted_kb_s'
        }
        
        # Rename matched columns
        for old_name, new_name in column_mapping.items():
            if old_name in self.data.columns:
                self.data = self.data.rename(columns={old_name: new_name})
                
        # Also check lowercase variations if not renamed
        for col in list(self.data.columns):
            col_clean = col.lower()
            if 'timestamp' in col_clean and 'timestamp' not in self.data.columns:
                self.data = self.data.rename(columns={col: 'timestamp'})
            elif 'cpu usage [%]' in col_clean or ('cpu' in col_clean and '%' in col_clean):
                self.data = self.data.rename(columns={col: 'cpu_usage_percent'})
            elif 'memory usage [kb]' in col_clean or ('memory' in col_clean and 'usage' in col_clean and 'kb' in col_clean):
                self.data = self.data.rename(columns={col: 'memory_usage_kb'})
            elif 'memory capacity' in col_clean:
                self.data = self.data.rename(columns={col: 'memory_capacity_kb'})
            elif 'disk read' in col_clean:
                self.data = self.data.rename(columns={col: 'disk_read_kb_s'})
            elif 'disk write' in col_clean:
                self.data = self.data.rename(columns={col: 'disk_write_kb_s'})
            elif 'network received' in col_clean:
                self.data = self.data.rename(columns={col: 'network_received_kb_s'})
            elif 'network transmitted' in col_clean:
                self.data = self.data.rename(columns={col: 'network_transmitted_kb_s'})

        # Convert timestamp to datetime if numeric
        if 'timestamp' in self.data.columns:
            try:
                self.data['timestamp'] = pd.to_datetime(self.data['timestamp'], unit='ms', errors='coerce')
            except Exception:
                pass
    
    def get_summary(self):
        """Get dataset summary statistics"""
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        summary = {
            'num_records': len(self.data),
            'num_columns': len(self.data.columns),
            'time_range': {
                'start': self.data['timestamp'].min() if 'timestamp' in self.data.columns else None,
                'end': self.data['timestamp'].max() if 'timestamp' in self.data.columns else None
            },
            'columns': list(self.data.columns),
            'statistics': self.data.describe()
        }
        
        return summary
    
    def get_feature_info(self):
        """Get information about available features"""
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        features = {
            'cpu_features': [col for col in self.data.columns if 'cpu' in col.lower()],
            'memory_features': [col for col in self.data.columns if 'memory' in col.lower()],
            'disk_features': [col for col in self.data.columns if 'disk' in col.lower()],
            'network_features': [col for col in self.data.columns if 'network' in col.lower()]
        }
        
        return features
    
    def check_missing_values(self):
        """Check for missing values in the dataset"""
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        missing = self.data.isnull().sum()
        missing_percent = (missing / len(self.data)) * 100
        
        return pd.DataFrame({
            'missing_count': missing,
            'missing_percent': missing_percent
        })
    
    def sample_data(self, n=5):
        """Return a sample of the data"""
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        return self.data.head(n)


def main():
    """Test the data loader"""
    loader = BitbrainsDataLoader()
    
    try:
        data = loader.load_data()
        print("\n=== Dataset Summary ===")
        summary = loader.get_summary()
        print(f"Records: {summary['num_records']}")
        print(f"Columns: {summary['num_columns']}")
        
        print("\n=== Columns ===")
        print(summary['columns'])
        
        print("\n=== Feature Info ===")
        features = loader.get_feature_info()
        for category, cols in features.items():
            print(f"{category}: {cols}")
        
        print("\n=== Sample Data ===")
        print(loader.sample_data(5))
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

