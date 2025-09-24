import os

def write_code_to_file(target_bank: str, code: str) -> str:
    """
    Writes the generated Python code to a file.
    The file will be created in a 'custom_parsers' directory.
    """
    try:
        os.makedirs("custom_parsers", exist_ok=True)
        file_path = f"custom_parsers/{target_bank}_parser.py"
        with open(file_path, "w") as f:
            f.write(code)
        return f"Successfully wrote code to {file_path}"
    except Exception as e:
        return f"Error writing code to file: {e}"
