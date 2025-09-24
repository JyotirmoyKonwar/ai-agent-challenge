import pandas as pd
import importlib

def run_tests(target_bank: str) -> str:
    """
    Runs the generated parser against the sample data and asserts its correctness.
    It dynamically imports the parser and compares its output DataFrame with the expected CSV.
    """
    module_name = f"custom_parsers.{target_bank}_parser"
    sample_pdf_path = f"data/{target_bank}/{target_bank} sample.pdf"
    expected_csv_path = f"data/{target_bank}/result.csv"

    try:
        # Invalidate caches to ensure the latest code is imported
        importlib.invalidate_caches()
        
        # Reload the module if it has been imported before
        if module_name in importlib.sys.modules:
            parser_module = importlib.reload(importlib.sys.modules[module_name])
        else:
            parser_module = importlib.import_module(module_name)

        parse_function = getattr(parser_module, 'parse')
        result_df = parse_function(sample_pdf_path)
        expected_df = pd.read_csv(expected_csv_path)

        # Compare the DataFrames
        pd.testing.assert_frame_equal(result_df, expected_df)
        return "All tests passed successfully!"
    except ImportError:
        return f"Error: Could not import `parse` from {module_name}."
    except FileNotFoundError as e:
        return f"Error: File not found during testing. Details: {e}"
    except AssertionError as e:
        return f"Error: Test assertion failed. DataFrame mismatch. Details: {e}"
    except Exception as e:
        return f"An unexpected error occurred during testing: {e}"
