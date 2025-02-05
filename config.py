# Description: This file contains the configuration for the experiment.
import os
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

# Load the environment variables
load_dotenv()

# ---------------------------------------------------------------------------------------------------------------------------------
# Configuration
print()
print(110*"=")
print("Configuration: ")
print(110*"=")

model_dict = {
    0: "meta-llama/Meta-Llama-3.1-405B-Instruct",   # https://deepinfra.com/meta-llama/Meta-Llama-3.1-405B-Instruct
    1: "meta-llama/Llama-3.3-70B-Instruct",         # https://deepinfra.com/meta-llama/Llama-3.3-70B-Instruct
    2: "microsoft/phi-4",                           # https://deepinfra.com/microsoft/phi-4
    3: "Qwen/QwQ-32B-Preview",                      # https://deepinfra.com/Qwen/QwQ-32B-Preview
    4: "deepseek-ai/DeepSeek-R1"                    # https://deepinfra.com/deepseek-ai/DeepSeek-R1
}

FOLDER_PATH = "demo"
LLM_MODEL_IDX = 2
LLM_GENERATION = True   # For 4 stages, given the USE_TMY is False. If USE_TMY is True, this will generate Stage 1 and 4 only.
USE_TMY = False         # When set to True, the TMY data will be used for the weather data skipping Stage 2 and 3.
SAVE_PLOTS = True

# COUNTRIES = ["USA", "Japan", "India", "Sweden", "United Arab Emirates", "Brazil"]
# COUNTRIES = ["USA", "Brazil"]       # For testing purposes
COUNTRIES = ["USA"]                 # For testing purposes

NUMBER_FAMILIES_PER_COUNTRY = 5     # Number of families to generate per country (passed to prompts.py file)

# ---------------------------------------------------------------------------------------------------------------------------------
LLM_MODEL = model_dict[int(LLM_MODEL_IDX)]
LLM_MODEL_SUBNAME = LLM_MODEL.split("/")[1].replace(".", "p")
print(f"LLM Model: {LLM_MODEL}")

if LLM_GENERATION:
    print(f'LLM Generation: {LLM_GENERATION}')

    # Get the API key from the environment variable
    api_key = os.getenv("DEEPINFRA_TOKEN")

    # Validate that the API key exists
    if not api_key:
        raise ValueError("API key not found! Please set DEEPINFRA_TOKEN as an environment variable.")
    else:
        print("API key found!")

    CLIENT = OpenAI(
        api_key=api_key,
        base_url="https://api.deepinfra.com/v1/openai"
    )
else:
    CLIENT = None

# ---------------------------------------------------------------------------------------------------------------------------------
# Paths
EXP_PATH = os.path.join(FOLDER_PATH, LLM_MODEL_SUBNAME)

TYPE = "TMY" if USE_TMY else "LLM"
SUB_EXP_PATH = f'{EXP_PATH}/{TYPE}'

print(f"Folder Path: {FOLDER_PATH}")
print(f"Experiment Path: {EXP_PATH}")
print(f"Sub Experiment Path: {SUB_EXP_PATH}")

original_logfile_path = f"{EXP_PATH}/logfile.txt"

l1_logfile_path = f"{EXP_PATH}/logfile_l1"
l2_logfile_path = f"{EXP_PATH}/logfile_l2"
l3_logfile_path = f"{EXP_PATH}/logfile_l3"
l4_logfile_path = f"{EXP_PATH}/logfile_l4"

l1_output_dir = f"{EXP_PATH}/data_l1_family_types"
l2_output_dir = f"{EXP_PATH}/data_l2_weather_range"
l3_output_dir = f"{EXP_PATH}/data_l3_weather_by_season"
l4_output_dir = f"{EXP_PATH}/data_l4_family_consumption"

JSON_FILE_PATH = f"{l1_output_dir}/family_types_$COUNTRY$.json"
JSON_MASTER_FILE_PATH = f'{l1_output_dir}/selected_family_types.json'

def generate_paths(base_path):
    return {
        "raw": f"{base_path}/raw_csv",
        "combined": f"{base_path}/combined_csv",
        "plots": f"{base_path}/plots",
    }

COMBINE_AND_PLOT_PATHS = {
    "weather": generate_paths(f'{l3_output_dir}/{TYPE}'),
    "family": generate_paths(f'{l4_output_dir}/{TYPE}'),
}

EXP_YEARLY_PATH = f'{EXP_PATH}/csv_yearly_profiles'

EXP_PROFILES_EXPAND_PATH = f'{SUB_EXP_PATH}/csv_expanded_profile'
EXP_WEATHER_EXPAND_PATH = f'{SUB_EXP_PATH}/csv_expanded_weather'

CSV_FINAL_PROFILES_WEATHER = f"{SUB_EXP_PATH}/csv_profile_with_weather"

WEATHER_RAW_PATH = COMBINE_AND_PLOT_PATHS["weather"]["raw"]
WEATHER_COMBINED_PATH = COMBINE_AND_PLOT_PATHS["weather"]["combined"]
WEATHER_PLOT_PATH = COMBINE_AND_PLOT_PATHS["weather"]["plots"]

FAMILY_RAW_PATH = COMBINE_AND_PLOT_PATHS["family"]["raw"]
FAMILY_COMBINED_PATH = COMBINE_AND_PLOT_PATHS["family"]["combined"]
FAMILY_PLOT_PATH = COMBINE_AND_PLOT_PATHS["family"]["plots"]

l3_output_dir = WEATHER_RAW_PATH
l4_output_dir = FAMILY_RAW_PATH

# ---------------------------------------------------------------------------------------------------------------------------------
# create a folder to save the generated prompts
if not os.path.exists(FOLDER_PATH):
    os.makedirs(FOLDER_PATH)

if not os.path.exists(EXP_PATH):
    os.makedirs(EXP_PATH)

if not os.path.exists(SUB_EXP_PATH):
    os.makedirs(SUB_EXP_PATH)

# Make sure the paths exist
for key, value in COMBINE_AND_PLOT_PATHS.items():
    for path in value.values():
        if not os.path.exists(path):
            os.makedirs(path)

# ---------------------------------------------------------------------------------------------------------------------------------
# Constants
YEAR = 2025
SEASONS = ["Winter", "Spring", "Summer", "Autumn"]
PATTERNS = ["Weekday", "Weekend"]

COUNTRY_CODE = ['US', 'JP', 'IN', 'SE', 'AE', 'BR']
COUNTRY_CODE_TO_NAME = {
    'AE': 'United Arab Emirates',
    'US': 'USA',
    'JP': 'Japan',
    'IN': 'India',
    'SE': 'Sweden',
    'BR': 'Brazil'
}

# Latitude and longitude of the capital of the following countries: USA, UAE, Japan, Sweden, Brazil, India
CAPITALS = {
    'USA': (38.8951, -77.0364),
    'United Arab Emirates': (24.4667, 54.3667),
    'Japan': (35.6895, 139.6917),
    'Sweden': (59.3293, 18.0686),
    'Brazil': (-15.7833, -47.8667),
    'India': (28.6139, 77.2090)
}

# Define weekend rules
WEEKEND_BY_COUNTRY = {
    'AE': [
        {'start': pd.Timestamp('1970-01-01'), 'end': pd.Timestamp('2021-12-31'), 'weekend': ['FRI', 'SAT']},
        {'start': pd.Timestamp('2022-01-01'), 'end': pd.Timestamp('2100-01-01'), 'weekend': ['SAT', 'SUN']}
    ],
    'US': [
        {'start': pd.Timestamp('1970-01-01'), 'end': pd.Timestamp('2100-01-01'), 'weekend': ['SAT', 'SUN']}
    ],
    'JP': [
        {'start': pd.Timestamp('1970-01-01'), 'end': pd.Timestamp('2100-01-01'), 'weekend': ['SAT', 'SUN']}
    ],
    'IN': [
        {'start': pd.Timestamp('1970-01-01'), 'end': pd.Timestamp('2100-01-01'), 'weekend': ['SAT', 'SUN']}
    ],
    'SE': [
        {'start': pd.Timestamp('1970-01-01'), 'end': pd.Timestamp('2100-01-01'), 'weekend': ['SAT', 'SUN']}
    ],
    'BR': [
        {'start': pd.Timestamp('1970-01-01'), 'end': pd.Timestamp('2100-01-01'), 'weekend': ['SAT', 'SUN']}
    ]
}

EXTRACT_COLUMNS = [
    "Hour",
    "Temperature_Value",
    "Humidity_Value",
    "SolRad-Diffuse_Value",
    "SolRad-Direct_Value",
    "Wind-Speed_Value"]
# ---------------------------------------------------------------------------------------------------------------------------------
# Paths from 02_plot_llm_...
COMBINE_WEATHER_PLOTS = True

# Dictionary for proper labels with units
LABELS_DICT = {
    "Temperature_Value": "Temperature (°C)",
    "Humidity_Value": "Humidity (%)",
    "SolRad-Diffuse_Value": "Diffuse Solar Radiation (W/m²)",
    "SolRad-Direct_Value": "Direct Solar Radiation (W/m²)",
    "Wind-Speed_Value": "Wind Speed (m/s)"}
# ---------------------------------------------------------------------------------------------------------------------------------
# Constants for file 03_create_base_dataframes.ipynb
TIME_STEP  = '1h'
START_TIME = f"{YEAR}-01-01 00:00:00"
END_TIME   = f"{YEAR}-12-31 23:59:59"
YEARLY_FILE_TEMPLATE = f'{EXP_YEARLY_PATH}/time_data_{TIME_STEP}_{YEAR}'
# ---------------------------------------------------------------------------------------------------------------------------------
# Constants for file 04_expand_to_yearly_dataframes.ipynb
WEATHER_NOISE_FACTOR = 2
FAMILY_NOISE_FACTOR = 2
# ---------------------------------------------------------------------------------------------------------------------------------
# Constants for file 05_generate_synthetic_data.ipynb

AGGREGATE_BY = 'daily'   # None, 'daily', 'weekly', 'monthly', 'seasonal'. If None, the data will not be aggregated (stays hourly).

if AGGREGATE_BY not in ['weekly', 'monthly']:
    SEASON_COLORS = {'Spring': 'green', 'Summer': 'orange', 'Autumn': 'brown', 'Winter': 'blue'}
else:
    SEASON_COLORS = None
