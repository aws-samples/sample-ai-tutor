import os
import json

def delete_file(file_path) -> bool:
    """
    Deletes a file locally if it exists.
    Returns True if the file was deleted successfully, False otherwise.
    """
    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
            print(f"File '{file_path}' has been deleted.")
            return True
        
        else:
            print(f"File '{file_path}' does not exist.")
            return False
        
    except Exception as e:
        print(f"\nERROR in delete_file: {e}")
        return False
    

def create_directory(directory_path: str):
    """
    Creates a local directory if it doesn't already exist.
    Returns True if the folder already exists or was created successfully, False otherwise.
    """

    # Check if the directory exists
    if not os.path.exists(directory_path):

        # If the directory doesn't exist, create it
        try:
            os.makedirs(directory_path)
            print(f"Directory '{directory_path}' created successfully.")
            return True
        
        except OSError as e:
            print(f"Error creating directory '{directory_path}': {e}")
            return False
        
    else:
        print(f"Directory '{directory_path}' already exists.")
        return True


def read_json_as_dict(json_filepath: str) -> dict:
    '''
    Reads a local JSON file and returns a dictionary.
    '''

    try:
        with open(json_filepath, 'r', encoding='utf-8') as file:
            data = json.load(file)

        return data
    
    except Exception as e:
        print(f"\nERROR in read_json_as_dict: {e}")
