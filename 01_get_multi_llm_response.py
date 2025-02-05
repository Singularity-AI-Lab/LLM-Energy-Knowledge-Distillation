# #### Libs & Constants

import os
import pvlib
import pandas as pd

from utils import *

from prompts import system_prompt_l1, user_prompt_family_types_l1, \
                    system_prompt_l2, user_prompt_l2, \
                    system_prompt_l3, user_prompt_daily_l3, \
                    system_prompt_l4, user_prompt_daily_l4

from config import LLM_MODEL, CLIENT, USE_TMY
from config import JSON_FILE_PATH, LLM_GENERATION
from config import COUNTRIES, YEAR, CAPITALS, SEASONS, PATTERNS
from config import l1_logfile_path, l2_logfile_path, l3_logfile_path, l4_logfile_path, original_logfile_path
from config import l1_output_dir, l2_output_dir, l3_output_dir, l4_output_dir

# ---------------------------------------------------------------------------------------------------------------------------------
# #### LLM
class LLM:
  def __init__(self, modeltype, model, client):
    self.modeltype = modeltype
    self.model = model
    self.client = client

  def getResponse(self, messages, temperature=0.2, max_tokens = 4096*10, seed=None):
    response = self.client.chat.completions.create(
      model=self.model,
      messages=messages,
      max_tokens=max_tokens,
      temperature=temperature,  # Adjusted to add some variability in responses
    #   seed=seed
    )
    answer = response.choices[0].message.content.strip()
    # print(answer)
    usage_prompt_tokens = response.usage.prompt_tokens
    usage_completion_tokens = response.usage.completion_tokens
    # print(f"Prompt Tokens: {usage_prompt_tokens}, Completion Tokens: {usage_completion_tokens}")

    return answer, str(usage_prompt_tokens), str(usage_completion_tokens)

# Define the model and client
llm = LLM("chat", LLM_MODEL, CLIENT)

def combined_prompt_msg(system_prompt, user_prompt, messages=None, loop_idx=0):
    system_prompt = system_prompt_msg(system_prompt)
    user_prompt = user_prompt_msg(user_prompt)
    # 
    if (loop_idx == 0) or True:
        time_now = pd.Timestamp.now().strftime("%Y-%m-%d_T%H-%M-%S")
        logger(f"[{time_now}]")
        logger(100*"-")
        logger(system_prompt)
        logger(user_prompt)
    #
    if messages is None:
        messages = system_prompt + user_prompt
    else:
        assistant_prompt = assistent_prompt_msg(messages)
        logger(assistant_prompt)
        messages = system_prompt + assistant_prompt + user_prompt
    #
    guidePrompt, usage_prompt_tokens, usage_completion_tokens = llm.getResponse(messages)
    guidePrompt = assistent_prompt_msg(guidePrompt)
    logger(guidePrompt)

    return guidePrompt, usage_prompt_tokens, usage_completion_tokens

# Calculate the number of family members per family per country
def get_number_of_family_members(family_types_json):
    results = {}

    for country_data in family_types_json:
        country = country_data["Country"]
        results[country] = {}
        
        for family in country_data["Families"]:
            family_type = family["Family Type"]
            member_count = len(family["Members"])
            
            # Store the results
            results[country][family_type] = member_count

    # Display the results
    for country, families in results.items():
        print(f"Country: {country}")
        for family_type, member_count in families.items():
            print(f"  {family_type}: {member_count} members")


def get_season(day, month, hemisphere='northern'):
    if (month == 12 and day >= 21) or (month in [1, 2]) or (month == 3 and day < 20):
        return 'Winter' if hemisphere == 'northern' else 'Summer'
    elif (month == 3 and day >= 20) or (month in [4, 5]) or (month == 6 and day < 21):
        return 'Spring' if hemisphere == 'northern' else 'Autumn'
    elif (month == 6 and day >= 21) or (month in [7, 8]) or (month == 9 and day < 23):
        return 'Summer' if hemisphere == 'northern' else 'Winter'
    elif (month == 9 and day >= 23) or (month in [10, 11]) or (month == 12 and day < 21):
        return 'Autumn' if hemisphere == 'northern' else 'Spring'
    else:
        raise ValueError("Invalid date or hemisphere. Ensure 'day' and 'month' are valid.")


def generate_tmy_weather(country, lat, lon, output_dir):
    data, _, _, _ = pvlib.iotools.get_pvgis_tmy(lat, lon, outputformat='json', 
                                                usehorizon=True, userhorizon=None, startyear=2013, endyear=2023,
                                                map_variables=True, timeout=30, roll_utc_offset=None, coerce_year=YEAR
                                                )
    data['country'] = country

    data.reset_index(inplace=True)
    data['hour'] = data['time(UTC)'].dt.hour
    data['day'] = data['time(UTC)'].dt.day
    data['month'] = data['time(UTC)'].dt.month

    # Apply the function to determine the season
    if country not in ['Brazil']:
        data['season'] = data.apply(lambda row: get_season(row['day'], row['month'],'northern'), axis=1)
    else:
        data['season'] = data.apply(lambda row: get_season(row['day'], row['month'],'southern'), axis=1)

    seasonal_data = data.groupby(['season', 'hour', 'country']).mean(numeric_only=True).reset_index()
    seasonal_data.drop(columns=['day', 'month'], inplace=True)

    # Rename the columns
    seasonal_data.rename(columns={
        'country': 'Country',
        'season': 'Season',
        'hour': 'Hour',
        'temp_air': 'Temperature_Value',
        'relative_humidity': 'Humidity_Value',
        'ghi': 'SolRad-Diffuse_Value',
        'dni': 'SolRad-Direct_Value',
        'wind_speed': 'Wind-Speed_Value'
    }, inplace=True)
    
    # Add description columns
    seasonal_data['Temperature_Description'] = ''
    seasonal_data['Humidity_Description'] = ''
    seasonal_data['SolRad-Diffuse_Description'] = ''
    seasonal_data['SolRad-Direct_Description'] = ''
    seasonal_data['Wind-Speed_Description'] = ''
    
    # Reorder columns
    seasonal_data = seasonal_data[[
        'Country', 'Season', 'Hour', 'Temperature_Description', 'Temperature_Value',
        'Humidity_Description', 'Humidity_Value', 'SolRad-Diffuse_Description', 'SolRad-Diffuse_Value',
        'SolRad-Direct_Description', 'SolRad-Direct_Value', 'Wind-Speed_Description', 'Wind-Speed_Value'
    ]]

    # Loop through each unique combination of Country and Season
    for (season), group in seasonal_data.groupby(['Season']):
        season = str(season)  # Convert to a string
        season = season.strip("(),'")  # Remove unwanted characters from the tuple format

        # Round the values to 2 decimal places
        group = group.round(2)
        # Define the file name
        file_name = f"{country.replace(' ', '-')}_{season}.csv"
        # Save the group to a CSV file
        group.to_csv(output_dir + '/' + file_name, index=False)

# ---------------------------------------------------------------------------------------------------------------------------------
# ### Level 1: Family types for different countries
print()
print(110*"=")
print("Level 1: Family types for different countries")
print(110*"=")

if LLM_GENERATION:
    system_prompt = system_prompt_l1

    for country in COUNTRIES:
        print(f"Country: {country}")
        user_prompt = user_prompt_family_types_l1.replace("$COUNTRY$", country)
        # print(user_prompt)
        family_types, usage_prompt_tokens, usage_completion_tokens  = combined_prompt_msg(system_prompt, user_prompt)
        family_types = family_types[0]['content']
        log_metadata_family_types(country, usage_prompt_tokens, usage_completion_tokens, logger)
        # break

    time_now = pd.Timestamp.now().strftime("%Y-%m-%d_T%H-%M-%S")
    logger(f"[{time_now}]")

    if os.path.exists(f'{l1_logfile_path}.txt'):
        print("Logfile 1 exists and will be used!")
        with open(original_logfile_path, 'w') as original_file:
            original_file.truncate(0)
            print(f"Cleared contents of {original_logfile_path}")
    else:
        copy_log_file(original_logfile_path, l1_logfile_path, clear_original=True)

log_parser_json(file_path=l1_logfile_path, output_dir=l1_output_dir, output_file_name_template=JSON_FILE_PATH)


# ---------------------------------------------------------------------------------------------------------------------------------
# ### Level 2: Typical min-max ranges for the weather parameters for all seasons
print()
print(110*"=")
print("Level 2: Typical min-max ranges for the weather parameters for all seasons")
print(110*"=")

if LLM_GENERATION and not USE_TMY:
    system_prompt = system_prompt_l2

    for country in COUNTRIES:
        # if country == "USA":
            print(f"Country: {country}")
            user_prompt = user_prompt_l2.replace("$Country$", country)
            user_prompt = user_prompt.replace("[$Year$]", str(YEAR))
            # print(user_prompt)
            guide_prompt, usage_prompt_tokens, usage_completion_tokens = combined_prompt_msg(system_prompt, user_prompt)
            guide_prompt = guide_prompt[0]['content']
            log_metadata_weather_range(country, usage_prompt_tokens, usage_completion_tokens, logger)
            # break

    time_now = pd.Timestamp.now().strftime("%Y-%m-%d_T%H-%M-%S")
    logger(f"[{time_now}]")

    if os.path.exists(f'{l2_logfile_path}.txt'):
        print("Logfile 2 exists!")
        l2_logfile_path = f'{l2_logfile_path}_{time_now}'

    copy_log_file(original_logfile_path, l2_logfile_path, clear_original=True)

if not USE_TMY:
    log_parser(file_path=l2_logfile_path, output_dir=l2_output_dir, metadata_type="weather_range")


# ---------------------------------------------------------------------------------------------------------------------------------
# ### Level 3: Daily weather data for different countries, considering their seasonal, and geographical contexts
print()
print(110*"=")
print("Level 3: Daily weather data for different countries, considering their seasonal, and geographical contexts")
print(110*"=")

if LLM_GENERATION and not USE_TMY:
    system_prompt = system_prompt_l3

    # Get list of json files in folder
    family_json_files = [f for f in os.listdir(l1_output_dir) if f.endswith(".json")]

    for output_file in family_json_files:
        full_file_path = os.path.join(l1_output_dir, output_file)  # Combine directory and file name

        # Load the JSON file for further processing
        with open(full_file_path, "r") as file:
            family_types_json = json.load(file)
            # get_number_of_family_members(family_types_json)

            for country_data in family_types_json:
                print(f"Country: {country_data['Country']}")

                idx = 0
                guide_prompt = ""
                for season in SEASONS:
                    print(f"    Season: {season}")

                    # Read the corresponding weather data
                    weather_file = f"{l2_output_dir}/{country_data['Country'].replace(' ', '-')}_weather_min_max.csv"
                    weather_data = pd.read_csv(weather_file)

                    user_prompt_indexed = user_prompt_daily_l3
                    user_prompt_indexed = user_prompt_indexed.replace("[$Country$]", country_data['Country'])
                    user_prompt_indexed = user_prompt_indexed.replace("[$Season$]", season)
                    user_prompt_indexed = user_prompt_indexed.replace("[$Year$]", str(YEAR))
                    user_prompt_indexed = user_prompt_indexed.replace("[$Temperature_Min$]", str(weather_data.loc[weather_data["Season"] == season, "Temperature_Min"].values[0]))
                    user_prompt_indexed = user_prompt_indexed.replace("[$Temperature_Max$]", str(weather_data.loc[weather_data["Season"] == season, "Temperature_Max"].values[0]))
                    user_prompt_indexed = user_prompt_indexed.replace("[$Humidity_Min$]", str(weather_data.loc[weather_data["Season"] == season, "Humidity_Min"].values[0]))
                    user_prompt_indexed = user_prompt_indexed.replace("[$Humidity_Max$]", str(weather_data.loc[weather_data["Season"] == season, "Humidity_Max"].values[0]))
                    user_prompt_indexed = user_prompt_indexed.replace("[$SolRad-Diffuse_Min$]", str(weather_data.loc[weather_data["Season"] == season, "SolRad-Diffuse_Min"].values[0]))
                    user_prompt_indexed = user_prompt_indexed.replace("[$SolRad-Diffuse_Max$]", str(weather_data.loc[weather_data["Season"] == season, "SolRad-Diffuse_Max"].values[0]))
                    user_prompt_indexed = user_prompt_indexed.replace("[$SolRad-Direct_Min$]", str(weather_data.loc[weather_data["Season"] == season, "SolRad-Direct_Min"].values[0]))
                    user_prompt_indexed = user_prompt_indexed.replace("[$SolRad-Direct_Max$]", str(weather_data.loc[weather_data["Season"] == season, "SolRad-Direct_Max"].values[0]))
                    user_prompt_indexed = user_prompt_indexed.replace("[$Wind-Speed_Min$]", str(weather_data.loc[weather_data["Season"] == season, "Wind-Speed_Min"].values[0]))
                    user_prompt_indexed = user_prompt_indexed.replace("[$Wind-Speed_Max$]", str(weather_data.loc[weather_data["Season"] == season, "Wind-Speed_Max"].values[0]))

                    if idx == 0:
                        guide_prompt, usage_prompt_tokens, usage_completion_tokens = combined_prompt_msg(system_prompt, user_prompt_indexed)
                    else:
                        guide_prompt, usage_prompt_tokens, usage_completion_tokens = combined_prompt_msg(system_prompt, user_prompt_indexed, guide_prompt)

                    guide_prompt = guide_prompt[0]['content']
                    
                    log_metadata_weather(country_data["Country"], season, usage_prompt_tokens, usage_completion_tokens, logger)
                    idx += 1

        #             break
        #         break
        #     break
        # break

    time_now = pd.Timestamp.now().strftime("%Y-%m-%d_T%H-%M-%S")
    logger(f"[{time_now}]")

    if os.path.exists(f'{l3_logfile_path}.txt'):
        print("Logfile 3 exists!")
        l3_logfile_path = f'{l3_logfile_path}_{time_now}'

    copy_log_file(original_logfile_path, l3_logfile_path, clear_original=True)

if not USE_TMY:
    log_parser(file_path=l3_logfile_path, output_dir=l3_output_dir, metadata_type="weather")


# ---------------------------------------------------------------------------------------------------------------------------------
# This part can replace Stage 2 and Stage 3 LLM Outputs if USE_TMY is set to True
# 
if USE_TMY:
    print()
    print("Generating TMY data for all countries based on defined capitals long and lat")
    
    # Check if the output folder is empty
    # tmy_output_folder = COMBINE_AND_PLOT_PATHS['weather']['raw_tmy']

    if not os.listdir(l3_output_dir):
        # Create a folder to save the CSV files
        os.makedirs(l3_output_dir, exist_ok=True)

        # Loop through each capital and get the TMY data
        for country, (lat, lon) in CAPITALS.items():
            if country in COUNTRIES:
                print(f"Country: {country}")
                generate_tmy_weather(country, lat, lon, l3_output_dir)
    else:
        print(f"The folder {l3_output_dir} is not empty. Skipping TMY data generation.\n")


    l4_logfile_path = f"{l4_logfile_path}_tmy"

# ---------------------------------------------------------------------------------------------------------------------------------
# ### Level 4: Daily profile based on weather and family type
# 
print()
print(110*"=")
print("Level 4: Daily profile based on weather and family type")
print(110*"=")

if LLM_GENERATION:

    print(f"Processing weather data from folder: {l3_output_dir}")
    weather_data = process_all_csv_files(l3_output_dir, COUNTRIES)

    system_prompt = system_prompt_l4
    guide_prompt = ""

    # Get list of json files in folder
    family_json_files = [f for f in os.listdir(l1_output_dir) if f.endswith(".json")]

    print(family_json_files)

    for output_file in family_json_files:
        full_file_path = os.path.join(l1_output_dir, output_file)  # Combine directory and file name

        # Load the JSON file for further processing
        with open(full_file_path, "r") as file:
            family_types_json = json.load(file)
            # get_number_of_family_members(family_types_json)

            for country_data in family_types_json:                    
                print(f"Country: {country_data['Country']}")

                for family in country_data['Families']:                            
                    print(f"  Family Type: {family['Family Type']}")
                    print(f"  Members: {', '.join(family['Members'])}")
                    idx = 0
                    for season in SEASONS:
                        print(f"    Season: {season}")

                        for day_pattern in PATTERNS:
                            print(f"      Pattern: {day_pattern}")

                            user_prompt_indexed = user_prompt_daily_l4
                            user_prompt_indexed = user_prompt_indexed.replace("[$Country$]", country_data['Country'])
                            user_prompt_indexed = user_prompt_indexed.replace("[$Year$]", str(YEAR))
                            user_prompt_indexed = user_prompt_indexed.replace("[$FamilyType$]", family['Family Type'])
                            user_prompt_indexed = user_prompt_indexed.replace("[$Members$]", ", ".join(family['Members']))
                            user_prompt_indexed = user_prompt_indexed.replace("[$MembersNum$]", str(len(family['Members'])))
                            user_prompt_indexed = user_prompt_indexed.replace("[$Pattern$]", day_pattern)
                            user_prompt_indexed = user_prompt_indexed.replace("[$Season$]", season)
                            user_prompt_indexed = user_prompt_indexed.replace("[$Hour$]", str(weather_data[country_data['Country']][season]["Hour"]))
                            user_prompt_indexed = user_prompt_indexed.replace("[$Temperature$]", str(weather_data[country_data['Country']][season]["Temperature_Value"]))
                            user_prompt_indexed = user_prompt_indexed.replace("[$Humidity$]", str(weather_data[country_data['Country']][season]["Humidity_Value"]))
                            user_prompt_indexed = user_prompt_indexed.replace("[$SolarRadiationDirect$]", str(weather_data[country_data['Country']][season]["SolRad-Direct_Value"]))
                            user_prompt_indexed = user_prompt_indexed.replace("[$SolarRadiationDiffuse$]", str(weather_data[country_data['Country']][season]["SolRad-Diffuse_Value"]))
                            user_prompt_indexed = user_prompt_indexed.replace("[$WindSpeed$]", str(weather_data[country_data['Country']][season]["Wind-Speed_Value"]))

                            guide_prompt, usage_prompt_tokens, usage_completion_tokens = combined_prompt_msg(system_prompt, user_prompt_indexed)
                            guide_prompt=guide_prompt[0]['content']
                            # usage_prompt_tokens, usage_completion_tokens = None, None

                            family_type_clean = family["Family Type"].replace("'","-")
                            family_members_clean = [member.replace("'", "-") for member in family["Members"]]
                            log_metadata(country_data["Country"], family_type_clean, family_members_clean, season, day_pattern, usage_prompt_tokens, usage_completion_tokens, logger)
                            idx += 1

                            # break   # 1 Day Pattern
                        # break       # 1 Season
                    # break           # 1 Family
            break                   # 1 Country

    time_now = pd.Timestamp.now().strftime("%Y-%m-%d_T%H-%M-%S")
    logger(f"[{time_now}]")

    if os.path.exists(f'{l4_logfile_path}.txt'):
        print("Logfile 4 exists!")
        l4_logfile_path = f'{l4_logfile_path}_{time_now}'
        print(f"File saved as: {l4_logfile_path}.")

    copy_log_file(original_logfile_path, l4_logfile_path, clear_original=True)

log_parser(file_path=l4_logfile_path, output_dir=l4_output_dir, metadata_type="family_consumption")