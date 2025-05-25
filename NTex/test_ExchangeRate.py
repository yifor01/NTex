import unittest
import pandas as pd
import numpy as np
from datetime import datetime
# Ensure NTex is a package by having NTex/__init__.py
# This allows the following import when running tests from the project root
from NTex.ExchangeRate import NTex

class TestSuggestBuyingRate(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures, including a NTex instance and sample data."""
        self.nt = NTex() # Default currency USD, not relevant for suggest_buying_rate
        self.sample_df = pd.DataFrame({
            '日期': pd.to_datetime([
                '2023-01-01', '2023-01-02', '2023-01-03', 
                '2023-01-04', '2023-01-05', '2023-01-06'
            ]),
            '即期賣出': [28.5, 28.6, 28.4, 28.7, 28.3, 28.2]
            # Add other columns if your method strictly requires them, though suggest_buying_rate
            # primarily focuses on '日期' and '即期賣出'.
        })

    def test_calculation_logic(self):
        """Test the core calculation logic of the suggestion model."""
        # Using a copy to avoid modifications to self.sample_df affecting other tests
        test_data = self.sample_df.copy()
        window = 3
        std_mult = 1.0
        
        result_df = self.nt.suggest_buying_rate(test_data, window_size=window, std_multiplier=std_mult)
        self.assertIsNotNone(result_df)
        
        # Expected values - calculated manually or from a trusted source
        # Rolling Mean (window=3, min_periods=1)
        # 28.5
        # (28.5 + 28.6) / 2 = 28.55
        # (28.5 + 28.6 + 28.4) / 3 = 28.5
        # (28.6 + 28.4 + 28.7) / 3 = 28.5666...
        # (28.4 + 28.7 + 28.3) / 3 = 28.4666...
        # (28.7 + 28.3 + 28.2) / 3 = 28.4

        # Rolling Std (window=3, min_periods=1, ddof=1 for pandas default)
        # NaN (or 0 if min_periods=1 and only 1 value, pandas std with 1 value is NaN)
        # np.std([28.5, 28.6], ddof=1) = 0.07071
        # np.std([28.5, 28.6, 28.4], ddof=1) = 0.1
        # np.std([28.6, 28.4, 28.7], ddof=1) = 0.15275
        # np.std([28.4, 28.7, 28.3], ddof=1) = 0.20816
        # np.std([28.7, 28.3, 28.2], ddof=1) = 0.26457

        expected_ma = [
            28.5, 
            28.55, 
            28.5, 
            28.566666666666666, 
            28.466666666666665, 
            28.4
        ]
        expected_sd = [
            np.nan,  # Pandas default for std with 1 element is NaN
            0.07071067811865477,
            0.1,
            0.15275252316519466,
            0.20816659994661326,
            0.26457513110645905
        ]

        expected_threshold = []
        for ma, sd in zip(expected_ma, expected_sd):
            if pd.isna(sd): # if sd is NaN, threshold is also NaN
                expected_threshold.append(np.nan)
            else:
                expected_threshold.append(ma - std_mult * sd)
        
        # Expected Signals (Buy if '即期賣出' < Threshold)
        # Original '即期賣出': [28.5, 28.6, 28.4, 28.7, 28.3, 28.2]
        # Thresholds (approx): [NaN, 28.479, 28.4, 28.413, 28.258, 28.135]
        # Signals:
        # 28.5 < NaN -> F (0) (NaN in threshold means no signal)
        # 28.6 < 28.479 -> F (0)
        # 28.4 < 28.4 -> F (0) (strictly less)
        # 28.7 < 28.413 -> F (0)
        # 28.3 < 28.258 -> F (0)
        # 28.2 < 28.135 -> F (0)
        # Let's adjust one value to trigger a signal for better testing:
        # If sample_df['即期賣出'][5] was 28.1, then 28.1 < 28.135 -> T (1)
        # For current data, all signals should be 0 for rows where threshold is not NaN.
        # For rows where threshold is NaN, signal should also be NaN (or 0 based on implementation)
        # The implementation sets signal to NaN if threshold is NaN.
        expected_signals = [np.nan, 0, 0, 0, 0, 0]


        for i in range(len(test_data)):
            self.assertAlmostEqual(result_df['移動平均'].iloc[i], expected_ma[i], places=5, msg=f"Row {i} MA mismatch")
            if pd.isna(expected_sd[i]):
                self.assertTrue(pd.isna(result_df['標準差'].iloc[i]), msg=f"Row {i} SD should be NaN")
                self.assertTrue(pd.isna(result_df['買入建議閾值'].iloc[i]), msg=f"Row {i} Threshold should be NaN")
                self.assertTrue(pd.isna(result_df['買入訊號'].iloc[i]), msg=f"Row {i} Signal should be NaN for NaN threshold")
            else:
                self.assertAlmostEqual(result_df['標準差'].iloc[i], expected_sd[i], places=5, msg=f"Row {i} SD mismatch")
                self.assertAlmostEqual(result_df['買入建議閾值'].iloc[i], expected_threshold[i], places=5, msg=f"Row {i} Threshold mismatch")
                self.assertEqual(result_df['買入訊號'].iloc[i], expected_signals[i], msg=f"Row {i} Signal mismatch")
    
    def test_input_validation_invalid_data(self):
        """Test with None, empty DataFrame, and DataFrame missing required columns."""
        self.assertIsNone(self.nt.suggest_buying_rate(None), "Failed for None input")
        self.assertIsNone(self.nt.suggest_buying_rate(pd.DataFrame()), "Failed for empty DataFrame")
        self.assertIsNone(
            self.nt.suggest_buying_rate(pd.DataFrame({'A': [1, 2], 'B': [3, 4]})), 
            "Failed for DataFrame with missing columns"
        )

    def test_input_validation_invalid_window_size(self):
        """Test with zero, negative, and too large window_size."""
        self.assertIsNone(self.nt.suggest_buying_rate(self.sample_df.copy(), window_size=0), "Failed for window_size=0")
        self.assertIsNone(self.nt.suggest_buying_rate(self.sample_df.copy(), window_size=-1), "Failed for window_size=-1")
        # Test with window_size > len(self.sample_df)
        self.assertIsNone(
            self.nt.suggest_buying_rate(self.sample_df.copy(), window_size=len(self.sample_df) + 1),
            "Failed for window_size > data length"
        )

    def test_input_validation_invalid_std_multiplier(self):
        """Test with zero and negative std_multiplier."""
        self.assertIsNone(self.nt.suggest_buying_rate(self.sample_df.copy(), std_multiplier=0), "Failed for std_multiplier=0")
        self.assertIsNone(self.nt.suggest_buying_rate(self.sample_df.copy(), std_multiplier=-1.0), "Failed for std_multiplier=-1.0")

    def test_edge_case_insufficient_data_for_window(self):
        """Test with data shorter than window_size (but window_size is positive)."""
        # This case is slightly different from invalid_window_size where window_size itself is invalid.
        # Here, window_size is valid, but data is too short.
        small_df = self.sample_df.head(2).copy() # 2 rows
        self.assertIsNone(
            self.nt.suggest_buying_rate(small_df, window_size=3), 
            "Failed for data length < window_size"
        )

    def test_non_numeric_selling_price_some_convertible(self):
        """Test '即期賣出' with mixed numeric strings and non-numeric strings."""
        df = pd.DataFrame({
            '日期': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04']),
            '即期賣出': ["28.5", "abc", "28.4", "def"]
        })
        result_df = self.nt.suggest_buying_rate(df.copy(), window_size=2) # Use a small window
        self.assertIsNotNone(result_df, "Result should not be None for mixed convertible data")
        
        # Expected '即期賣出' after coercion: [28.5, NaN, 28.4, NaN]
        self.assertTrue(pd.isna(result_df['即期賣出'].iloc[1]), "Second '即期賣出' should be NaN")
        self.assertTrue(pd.isna(result_df['即期賣出'].iloc[3]), "Fourth '即期賣出' should be NaN")
        self.assertEqual(result_df['即期賣出'].iloc[0], 28.5)
        self.assertEqual(result_df['即期賣出'].iloc[2], 28.4)

        # Check MA calculation (example for index 2)
        # MA for index 2 (window 2): mean of '即期賣出'[1] (NaN) and '即期賣出'[2] (28.4)
        # Pandas rolling mean should skip NaN by default if not all values in window are NaN
        # Expected MA at index 2: (NaN + 28.4) -> if skipna=True (default), this depends on how many non-NaNs.
        # min_periods=1: result_df['移動平均'].iloc[2] should be 28.4
        self.assertAlmostEqual(result_df['移動平均'].iloc[2], 28.4, places=5) 
        # SD for index 2 (window 2): std of [NaN, 28.4] -> NaN (as only one non-NaN point)
        self.assertTrue(pd.isna(result_df['標準差'].iloc[2]))
        self.assertTrue(pd.isna(result_df['買入建議閾值'].iloc[2]))
        self.assertTrue(pd.isna(result_df['買入訊號'].iloc[2]))


    def test_non_numeric_selling_price_all_non_convertible(self):
        """Test '即期賣出' with all non-convertible strings."""
        df = pd.DataFrame({
            '日期': pd.to_datetime(['2023-01-01', '2023-01-02']),
            '即期賣出': ["abc", "def"]
        })
        self.assertIsNone(
            self.nt.suggest_buying_rate(df.copy()), 
            "Failed for all non-convertible '即期賣出'"
        )

    def test_all_nan_selling_price_input(self):
        """Test '即期賣出' with all np.nan values."""
        df = pd.DataFrame({
            '日期': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03']),
            '即期賣出': [np.nan, np.nan, np.nan]
        })
        self.assertIsNone(
            self.nt.suggest_buying_rate(df.copy()), 
            "Failed for all NaN '即期賣出' input"
        )

# This allows running the tests from the command line
if __name__ == '__main__':
    unittest.main()
