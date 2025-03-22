
import os
import re
import ast
import sys
import json
import shutil
import pandas as pd
from glob import glob
from datetime import datetime, timedelta

from config import original_logfile_path, SEASONS, EXTRACT_COLUMNS

def system_prompt_msg(prompt):
    system_prompt = [{"role": "system", "content": prompt}]
    # logger(system_prompt)

    return system_prompt

def user_prompt_msg(prompt):
    user_prompt = [{"role": "user", "content": prompt}]
    # logger(user_prompt)
    
    return user_prompt

def assistent_prompt_msg(prompt):
    guidePrompt = [{"role": "assistant", "content": prompt}]
    # logger(guidePrompt)

    return guidePrompt

def logger_print(msg, file_name=original_logfile_path):
    log_file = open(file_name, 'a')
    sys.stdout = log_file
    print(msg);

    # Restore the default stdout
    sys.stdout = sys.__stdout__

    log_file.close()

def logger(msg, file_name=original_logfile_path):
    log_file = open(file_name, 'a')
    if isinstance(msg, list):
        msg = "\n".join([str(item) for item in msg])  # Convert each item to string and join with newline
    log_file.write(msg + "\n")
    log_file.close()

def copy_log_file(original_file_path, new_file_path, clear_original=False):
    new_file_path = f"{new_file_path}.txt"

    try:        
        # Copy the contents of the original file to the new file
        shutil.copyfile(original_file_path, new_file_path)
        print(f"Copied contents from {original_file_path} to {new_file_path}.")

        if clear_original:
            # Clear the original file
            with open(original_file_path, 'w') as original_file:
                original_file.truncate(0)  # Clears the file by setting its size to 0
            print(f"Cleared contents of {original_file_path}.")
    except Exception as e:
        print(f"An error occurred: {e}")

def string_stats(content):
    print(f"Number of characters {len(content)}", end=", ")
    line_count = content.count("\n")
    print(f"Number of lines {line_count}", end=", ")
    print(f"Number of words {len(content.split())}", end=", ")
    print(f"Total size of the object {sys.getsizeof(content)}")
    print()

def read_text_file(file_path):
    with open(file_path, "r") as file:
        content = file.read()
        print(f"Readings [{file_path}]")
        string_stats(content)

    return content

# :////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
def extract_final_message(content):
    # Find all sequences with double $$ markers
    matches = list(re.finditer(r"\$\$MESSAGE_START\$\$(.*?)\$\$MESSAGE_END\$\$", content, re.DOTALL))
    
    if matches:
        # Extract the last match
        final_message = matches[-1].group(1).strip()
        
        # Normalize the final message: remove unnecessary escape characters and whitespace
        final_message = final_message.replace("\\n", "\n").replace("\\t", "\t").strip()
        final_message = final_message.replace("\n", "")
        final_message = re.sub(r"\s+", " ", final_message)
        
        return final_message

    # If no valid message sequence is found, return None
    return None
# :///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

# ### Log Parser
def log_parser(file_path, output_dir, metadata_type):
    file_path = f'{file_path}.txt'

    # Read the file
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Extract all assistant and metadata lines in sequence
    assistant_lines = [(i, line.strip()) for i, line in enumerate(lines) 
                       if line.startswith("{'role': 'assistant'")]
    
    metadata_lines = [(i, line.strip()) for i, line in enumerate(lines) 
                      if line.startswith("{'role': 'metadata'")]

    if not metadata_lines or not assistant_lines:
        print("No metadata or assistant lines found.")
        return

    print(f"Extracted {len(metadata_lines)} metadata lines.")
    print(f"Extracted {len(assistant_lines)} assistant lines.")

    # Ensure the output directory exists
    # output_dir = f"{output_dir}/raw_csv"
    os.makedirs(output_dir, exist_ok=True)

    # Process assistant and metadata pairs
    processed_indices = set()
    for metadata_index, metadata_line in metadata_lines:
        # Find the nearest assistant(s) before the metadata
        assistant_candidates = [
            (idx, line) for idx, line in assistant_lines if idx < metadata_index and idx not in processed_indices
        ]

        print(f"\n------------------ Processing assistant and metadata pair...")
        if len(assistant_candidates) == 0:
            print(f"No assistant found for metadata at index {metadata_index}.")
            continue

        if len(assistant_candidates) == 1:
            assistant_index, assistant_line = assistant_candidates[0]
            print(f"Having single assistant at index {assistant_index}")
        else:
            assistant_index, assistant_line = assistant_candidates[-1]
            print(f"Having double assistant at indices {assistant_candidates[-2][0]} and {assistant_candidates[-1][0]}")

        # Mark this assistant as processed
        processed_indices.add(assistant_index)

        try:
            # Process metadata
            metadata_dict = ast.literal_eval(metadata_line)
            metadata_content = metadata_dict.get("content", "")

            # Handle metadata based on type
            metadata_parts = [part.strip() for part in metadata_content.split(",")]

            if metadata_type == "family_consumption":
                if len(metadata_parts) < 10:
                    print(f"Skipping metadata at index {metadata_index}: insufficient metadata parts.")
                    continue

                metadata = {
                    "Country": metadata_parts[1].strip(),
                    "Family Type": metadata_parts[3].strip(),
                    "Members": metadata_parts[5].strip("[]").split("|"),
                    "Season": metadata_parts[7].strip(),
                    "Pattern": metadata_parts[9].strip(),
                }
            elif metadata_type == "weather":
                if len(metadata_parts) < 4:
                    print(f"Skipping metadata at index {metadata_index}: insufficient metadata parts.")
                    continue

                metadata = {
                    "Country": metadata_parts[1].strip(),
                    "Season": metadata_parts[3].strip(),
                }
            elif metadata_type == "weather_range":
                if len(metadata_parts) < 2:
                    print(f"Skipping metadata at index {metadata_index}: insufficient metadata parts.")
                    continue

                metadata = {
                    "Country": metadata_parts[1].strip(),
                }
            else:
                raise ValueError(f"Unknown metadata type: {metadata_type}")

            # print(f"Processing metadata: {metadata}")

            # Process assistant line
            assistant_line = assistant_line.replace("\n", "").strip()
            assistant_dict = ast.literal_eval(assistant_line)
            content = assistant_dict.get("content", "").strip()
            
            # Remove message delimiters
            # content = content.replace("$$MESSAGE_START$$", "").replace("$$MESSAGE_END$$", "").strip()
            # match = re.search(r"\$\$MESSAGE_START\$\$(.*?)\$\$MESSAGE_END\$\$", assistant_line, re.DOTALL)
            # if match:
            #     content = match.group(1).strip()  # Extract the content inside

            content = extract_final_message(assistant_line)
            if not content:
                print("No valid message sequence found!")
            # else:
            #     print("Extracted Final Message:")
            #     print(content)
                
            # Preprocess the content based on metadata_type
            if metadata_type == "family_consumption":
                # Add quotes around the second parameter in the tuples
                content = re.sub(r"\(\s*(\d+)\s*,\s*([^,()]+)\s*,", r"(\1,'\2',", content)  # ***

            elif metadata_type == "weather":
                # Add quotes around the second parameter in tuples
                content = re.sub(r"\(\s*(\d+)\s*,\s*([^,']+)\s*,", r"(\1, '\2',", content)  # ***

            elif metadata_type == "weather_range":
                # Add quotes around the first parameter in tuples
                content = re.sub(r"\(\s*([^,']+)\s*,", r"('\1',", content)  # ***

            # print(f"Processed content: {content}")  # Debugging

            # Extract parameter data and raw data using regex
            parameter_data = re.findall(r"#([^#]+)#\[(.+?)\]", content, flags=re.DOTALL)
            if not parameter_data:
                raise ValueError("No valid parameter data found in the message.")

            if metadata_type == "family_consumption":
                # Dictionary to track occurrences of each member
                member_count = {}

                updated_parameter_data = []
                
                for parameter, raw_data in parameter_data:
                    if parameter in member_count:
                        member_count[parameter] += 1
                        new_parameter = f"{parameter}_{member_count[parameter]:02d}"  # Append _01, _02, etc.
                    else:
                        member_count[parameter] = 0  # First occurrence keeps original name
                        new_parameter = parameter  # Keep first occurrence unchanged
                    
                    updated_parameter_data.append((new_parameter, raw_data))

                # Use updated parameter data with unique names
                parameter_data = updated_parameter_data
                
            # Parse the data for each parameter
            parsed_data = []
            for parameter, raw_data in parameter_data:
                try:
                    parameter_safe = parameter.replace(" ", "-")  # Replace spaces with dashes for column names

                    # Safely parse the list of tuples
                    if metadata_type == "family_consumption":
                        columns = ["Hour", f"{parameter_safe}_Action", f"{parameter_safe}_Consumption"]
                    elif metadata_type == "weather":
                        columns = ["Hour", f"{parameter_safe}_Description", f"{parameter_safe}_Value"]
                    elif metadata_type == "weather_range":
                        columns = ["Season", f"{parameter_safe}_Min", f"{parameter_safe}_Max"]

                    # print(f"Raw data for {parameter}: {raw_data}")  # Debugging
                    tuples = ast.literal_eval(f"[{raw_data}]")
                    df = pd.DataFrame(tuples, columns=columns)
                    
                    if metadata_type in ["family_consumption", "weather"]:
                        df.set_index("Hour", inplace=True)

                    parsed_data.append(df)

                except Exception as e:
                    print(f"Error parsing data for member {parameter}: {e}")
                    print(f"Raw data for debugging: {raw_data}")

            # Combine parsed DataFrames into a single DataFrame
            if parsed_data:
                
                if metadata_type == "family_consumption":
                    scenario_df = pd.concat(parsed_data, axis=1)
                    scenario_df.rename(columns=lambda x: x.replace("'s", "").replace("-s ", " ").replace("-s-", "-"), inplace=True)

                    scenario_df["Country"] = metadata["Country"]
                    scenario_df["Season"] = metadata["Season"]
                    scenario_df["Family_Type"] = metadata["Family Type"]
                    scenario_df["Pattern"] = metadata["Pattern"]
                    scenario_df['Total_Electricity_Usage'] = scenario_df.filter(like='_Consumption').sum(axis=1).round(2)

                    metadata_columns = ["Country", "Family_Type", "Season", "Pattern", "Hour", "Total_Electricity_Usage"]
                
                elif metadata_type == "weather":
                    scenario_df = pd.concat(parsed_data, axis=1)
                    scenario_df["Country"] = metadata["Country"]
                    scenario_df["Season"] = metadata["Season"]

                    metadata_columns = ["Country", "Season", "Hour"]
                
                elif metadata_type == "weather_range":
                    scenario_df = parsed_data[0]
                    for df in parsed_data[1:]:
                        scenario_df = scenario_df.merge(df, on="Season", how="outer")
                    scenario_df["Country"] = metadata["Country"]

                    metadata_columns = ["Country", "Season"]

                scenario_df = scenario_df.reset_index()

                data_columns = [col for col in scenario_df.columns if col not in metadata_columns]

                # print(f"Data columns: {data_columns}")
                data_columns = [k.replace("'s", "").replace("-s ", " ").replace("-s-", "-") for k in data_columns]
                # print(f"Data columns: {data_columns}")

                scenario_df = scenario_df[metadata_columns + data_columns]

                # Generate a unique filename based on metadata
                if metadata_type == "family_consumption":
                    file_name = f"{metadata['Country'].replace(' ', '-')}_{metadata['Family Type'].replace(' ', '-')}_{metadata['Season']}_{metadata['Pattern']}.csv"
                elif metadata_type == "weather":
                    file_name = f"{metadata['Country'].replace(' ', '-')}_{metadata['Season']}.csv"
                elif metadata_type == "weather_range":
                    file_name = f"{metadata['Country'].replace(' ', '-')}_weather_min_max.csv"

                output_file_path = os.path.join(output_dir, file_name)

                # Save the DataFrame to a CSV file
                scenario_df.to_csv(output_file_path, index=False)
                print(f"  Data saved to {output_file_path}")

            else:
                print(f"No valid data parsed for this assistant line.")

        except Exception as e:
            print(f"Error processing assistant and metadata pair: {e}")
        # break

def log_parser_json_org(file_path, output_dir, output_file_name):
    # Read the file
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Extract all assistant and metadata lines in sequence
    assistant_lines = [(i, line.strip()) for i, line in enumerate(lines) 
                       if line.startswith("{'role': 'assistant'")]
    
    metadata_lines = [(i, line.strip()) for i, line in enumerate(lines) 
                      if line.startswith("{'role': 'metadata'")]

    if not metadata_lines or not assistant_lines:
        print("No metadata or assistant lines found.")
        return

    print(f"Extracted {len(metadata_lines)} metadata lines.")
    print(f"Extracted {len(assistant_lines)} assistant lines.")

    # Ensure the output directory exists
    # output_dir = f"{output_dir}/raw_csv"
    os.makedirs(output_dir, exist_ok=True)

    # Process assistant and metadata pairs
    processed_indices = set()
    for metadata_index, metadata_line in metadata_lines:
        # Find the nearest assistant(s) before the metadata
        assistant_candidates = [
            (idx, line) for idx, line in assistant_lines if idx < metadata_index and idx not in processed_indices
        ]

        print(f"\n------------------ Processing assistant and metadata pair...")
        if len(assistant_candidates) == 0:
            print(f"No assistant found for metadata at index {metadata_index}.")
            continue

        if len(assistant_candidates) == 1:
            assistant_index, assistant_line = assistant_candidates[0]
            print(f"Having single assistant at index {assistant_index}")
        else:
            assistant_index, assistant_line = assistant_candidates[-1]
            print(f"Having double assistant at indices {assistant_candidates[-2][0]} and {assistant_candidates[-1][0]}")

        # Mark this assistant as processed
        processed_indices.add(assistant_index)

        try:
            # Process metadata
            metadata_dict = ast.literal_eval(metadata_line)
            metadata_content = metadata_dict.get("content", "")

            # Handle metadata based on type
            metadata_parts = [part.strip() for part in metadata_content.split(",")]

            print(f"Processing metadata...")

            # Process assistant line
            assistant_dict = ast.literal_eval(assistant_line)
            content = assistant_dict.get("content", "").strip()
            content = content.replace("```", "")

            # Use regex to extract the JSON content between MESSAGE_START and MESSAGE_END
            match = re.search(r"\$\$MESSAGE_START\$\$(.*?)\$\$MESSAGE_END\$\$", content, re.DOTALL)

            if match:
                content_between = match.group(1).strip()  # Extract the content inside
                # print("Extracted Content:")
                # print(content_between)

                # Parse the extracted content as JSON
                try:
                    content_parsed = json.loads(content_between)

                    # Combine output directory and output file name
                    output_file_path = os.path.join(output_dir, output_file_name)
                    
                    # Save to a JSON file
                    with open(output_file_path, "w") as file:
                        json.dump(content_parsed, file, indent=2)
                        print(f"  Data saved to {output_file_path}")

                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON: {e}")

            else:
                print("MESSAGE_START and MESSAGE_END markers not found!")

        except Exception as e:
            print(f"Error processing assistant and metadata pair: {e}")

def log_parser_json(file_path, output_dir, output_file_name_template):
    """
    Parses a log file containing responses for multiple countries and saves each response as a separate JSON file.

    Args:
        file_path (str): Path to the log file.
        output_dir (str): Directory where the individual JSON files will be saved.
        output_file_name_template (str): Template for output file names, e.g., "family_types_$COUNTRY$.json".

    Returns:
        List of file paths for the saved JSON files.
    """
    file_path = f'{file_path}.txt'

    # Read the file
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Extract all assistant lines
    assistant_lines = [(i, line.strip()) for i, line in enumerate(lines) 
                       if line.startswith("{'role': 'assistant'")]

    if not assistant_lines:
        print("No assistant lines found.")
        return []

    print(f"Extracted {len(assistant_lines)} assistant lines.")

    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    output_files = []

    # Process each assistant line
    for index, assistant_line in assistant_lines:
        try:
            # Parse the assistant line
            assistant_dict = ast.literal_eval(assistant_line)
            content = assistant_dict.get("content", "").strip()
            content = content.replace("```", "")

            # Use regex to extract the JSON content between MESSAGE_START and MESSAGE_END
            match = re.search(r"\$\$MESSAGE_START\$\$(.*?)\$\$MESSAGE_END\$\$", content, re.DOTALL)

            if match:
                content_between = match.group(1).strip()  # Extract the content inside

                # Parse the extracted content as JSON
                content_parsed = json.loads(content_between)

                # Extract country name for the file name
                country_name = content_parsed[0].get("Country", "Unknown").replace(" ", "-")

                # Generate country-specific file name
                output_file_name = output_file_name_template.replace("$COUNTRY$", country_name)
                # print(f"Processing data for {output_file_name}...")
                # output_file_path = os.path.join(output_dir, output_file_name)
                # print(f"Output file path: {output_file_path}")

                # Save to a JSON file
                with open(output_file_name, "w") as file:
                    json.dump(content_parsed, file, indent=2)
                    print(f"  Data saved to {output_file_name}")

                output_files.append(output_file_name)

            else:
                print(f"MESSAGE_START and MESSAGE_END markers not found in assistant line at index {index}!")

        except Exception as e:
            print(f"Error processing assistant line at index {index}: {e}")

    return output_files

def log_metadata(country, family_type, members, season, day_pattern, usage_prompt_tokens, usage_completion_tokens, logger):
    metadata_final = (
        f"{{'role': 'metadata', 'content': '"
        f"Country, {country}, "
        f"Family Type, {family_type}, "
        f"Members, [{'|'.join(members)}], "
        f"Season, {season}, "
        f"Pattern, {day_pattern},"
        f"Usage_Prompt_Tokens, {usage_prompt_tokens}, "
        f"Usage_Completion_Tokens, {usage_completion_tokens}"
        f"'}}"
    )
    logger(metadata_final)

def log_metadata_weather(country, season, usage_prompt_tokens, usage_completion_tokens, logger):
    metadata_final = (
        f"{{'role': 'metadata', 'content': '"
        f"Country, {country}, "
        f"Season, {season}, "
        f"Usage_Prompt_Tokens, {usage_prompt_tokens}, "
        f"Usage_Completion_Tokens, {usage_completion_tokens}"
        f"'}}"
    )
    logger(metadata_final)

def log_metadata_weather_range(country, usage_prompt_tokens, usage_completion_tokens, logger):
    metadata_final = (
        f"{{'role': 'metadata', 'content': '"
        f"Country, {country}, "
        f"Usage_Prompt_Tokens, {usage_prompt_tokens}, "
        f"Usage_Completion_Tokens, {usage_completion_tokens}"
        f"'}}"
    )
    logger(metadata_final)

# def log_metadata_family_types(output_file, usage_prompt_tokens, usage_completion_tokens, logger):
def log_metadata_family_types(country, usage_prompt_tokens, usage_completion_tokens, logger):
    metadata_final = (
        f"{{'role': 'metadata', 'content': '"
        # f"output, {output_file}, "
        f"Country, {country}, "
        f"Usage_Prompt_Tokens, {usage_prompt_tokens}, "
        f"Usage_Completion_Tokens, {usage_completion_tokens}"
        f"'}}"
    )
    logger(metadata_final)

# Function to process a CSV file and extract the required data
def process_csv(file_path):
    try:
        # Load the CSV file
        df = pd.read_csv(file_path)

        # Check if all required columns exist
        missing_columns = [col for col in EXTRACT_COLUMNS if col not in df.columns]
        if missing_columns:
            print(f"Missing columns in file {file_path}: {missing_columns}")
            return None

        # Extract data
        extracted_data = df[EXTRACT_COLUMNS]
        
        # Group by hour to ensure data is consistent over 24 hours
        hourly_data = {col: extracted_data[col].tolist() for col in EXTRACT_COLUMNS if col != "Hour"}
        hourly_data["Hour"] = list(range(24))  # Ensure hours are sequential

        return hourly_data

    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return None

# Function to process all CSV files in the folder
def process_all_csv_files(folder_path, country_names):
    data_by_country_and_season = {}

    # Iterate over country names and seasons to find matching files
    for country in country_names:
        data_by_country_and_season[country] = {}

        for season in SEASONS:
            # Construct file name pattern
            file_pattern = os.path.join(folder_path, f"{country.replace(' ', '-')}_{season}.csv")
            matching_files = glob(file_pattern)

            if not matching_files:
                print(f"No matching files for {country} in {season}.")
                continue

            # Process the file
            for file_path in matching_files:
                hourly_data = process_csv(file_path)
                if hourly_data:
                    data_by_country_and_season[country][season] = hourly_data

    return data_by_country_and_season

def process_log_timestamps(log_file):
    """
    Process a log file to compute the duration between consecutive timestamps,
    the total duration, and the average duration.

    Parameters:
    - log_file (str): Path to the log file.

    Returns:
    - durations (list): List of durations between consecutive timestamps.
    - total_duration (timedelta): Total duration between the first and last timestamps.
    - avg_duration (timedelta): Average duration between consecutive timestamps.
    """
    # Read the log file
    with open(log_file, 'r') as file:
        lines = file.readlines()

    # Extract timestamps
    timestamp_pattern = r"\[(\d{4}-\d{2}-\d{2}_T\d{2}-\d{2}-\d{2})\]"
    timestamps = []
    for line in lines:
        match = re.search(timestamp_pattern, line)
        if match:
            timestamps.append(datetime.strptime(match.group(1), "%Y-%m-%d_T%H-%M-%S"))

    # Ensure at least two timestamps
    if len(timestamps) < 2:
        print("Not enough timestamps to calculate durations.")
        return None, None, None

    # Calculate durations
    durations = [(timestamps[i+1] - timestamps[i]) for i in range(len(timestamps) - 1)]

    # Calculate total and average durations
    total_duration = sum(durations, timedelta())
    avg_duration = total_duration / len(durations)

    return durations, total_duration, avg_duration

def process_log_tokens(log_file):
    """
    Process a log file to compute the number of tokens for each call,
    and the total number of tokens.

    Parameters:
    - log_file (str): Path to the log file.

    Examples:
    {'role': 'metadata', 'content': 'Country, USA, Usage_Prompt_Tokens, 489, Usage_Completion_Tokens, 185'}

    Returns:
    - Total_Usage_Prompt_Tokens (int): Total number of tokens in the usage prompt.
    - Total_Usage_Completion_Tokens (int): Total number of tokens in the usage completion.
    """
    # Read the log file
    with open(log_file, 'r') as file:
        lines = file.readlines()

    # Extract tokens
    # search for lines that start with {'role': 'metadata',
    token_pattern = r"Usage_Prompt_Tokens, (\d+), Usage_Completion_Tokens, (\d+)"
    tokens = []    
    for line in lines:
        match = re.search(token_pattern, line)
        if match:
            tokens.append((int(match.group(1)), int(match.group(2))))

    # Ensure at least one token pair
    if not tokens:
        print("No token pairs found.")
        return None, None
    
    # Calculate total tokens
    total_prompt_tokens = sum([pair[0] for pair in tokens])
    total_completion_tokens = sum([pair[1] for pair in tokens])

    return total_prompt_tokens, total_completion_tokens