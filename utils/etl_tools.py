import os
import requests
import pandas as pd

class ETL_Tools:

    def __init__(self) -> None:
        pass


    # Extracts data from the source (API[url]) and loads it into the target or desired location (output_folder).
    def extract_load(self, url: str, output_folder: str, format: str) -> str:
        """
        Extracts data from the source (API[url]) 
        and loads it into the target or desired location (output_folder).

        Args:
            url (str): The URL of the source from which data needs to be extracted.
            output_folder (str): The folder path where the extracted data will be loaded.

        Returns:
            str: A message indicating the success or failure of the operation.
        """

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) # Get the project root directory
        output_folder = os.path.join(project_root, output_folder) # Get the absolute path of the output folder

        try:
            # Ensure the output folder exists
            os.makedirs(output_folder, exist_ok=True)

            # Extract data from the source (API)
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for bad responses
            data = response.json()  # Assuming the API returns JSON data

            # Load the extracted data into the target location (output_folder)
            filename = os.path.join(output_folder, f"extracted_data.{format}")

            df = pd.json_normalize(data['results'])  # Convert JSON data to a DataFrame
            if format.lower() == 'csv':
                df.to_csv(filename, index=False)
                return f"Data successfully extracted from {url} and loaded into {filename} in CSV format."
            elif format.lower() == 'json':
                df.to_json(filename, orient='records', lines=True)
                return f"Data successfully extracted from {url} and loaded into {filename} in JSON format."
            elif format.lower() == 'parquet':
                df.to_parquet(filename, index=False)
                return f"Data successfully extracted from {url} and loaded into {filename} in Parquet format."
            else:
                return f"Error: Unsupported format '{format}'. Please use 'csv', 'json', or 'parquet'."

        except requests.exceptions.RequestException as e:
            return f"Error: Failed to extract and load data. {str(e)}"


    # Transforms the extracted data from the specified file and loads it into the desired location (output_folder).
    def transform_load(self, input_file_path: str, n: int) -> str:
        """
        Transforms the extracted data from the specified file 
        and loads it into the desired location (output_folder).

        Args:
            input_file (str): The path to the file containing the extracted data.
            n (int): The number of rows to display from the transformed data.

        Returns:
            str: A message indicating the success or failure of the operation.
        """

        file_extension = os.path.splitext(input_file_path)[1].lower()  # Get the file extension of the input file

        if file_extension == '.csv':
            df = pd.read_csv(input_file_path)
        elif file_extension == '.json':
            df = pd.read_json(input_file_path)
        elif file_extension == '.parquet':
            df = pd.read_parquet(input_file_path)
        else:
            return f"Error: Unsupported input file format '{file_extension}'. Please use 'csv', 'json', or 'parquet'."

        top_n_rows = df.head(n).to_string()  # Get the top n rows of the DataFrame as a string for display

        return f"Data successfully transformed from {input_file_path}. Here are the top {n} rows:\n{top_n_rows}"


    # Executes the provided code.
    def execute_code(self, code: str):
        """
        Executes the provided code.

        Args:
            code (str): The code to be executed.

        Returns:
            str: A message indicating the success or failure of the operation.
        """
        try:
            exec(code)
            return "Code executed successfully."
        except Exception as e:
            return f"Error executing code: {str(e)}"

if __name__ == "__main__":
    obj = ETL_Tools()
    path = "D:\\Codes\\DATA_AGENT\\data\\extractions\\extracted_data.csv"
    print(obj.transform_load(path, 5))