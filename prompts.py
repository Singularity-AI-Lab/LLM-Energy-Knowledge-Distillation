# Main Prompts
# ---------------------------------------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------------------------------
from config import NUMBER_FAMILIES_PER_COUNTRY

## Level 1: Family structures across multiple countries
# ---------------------------------------------------------------------------------------------------------------------------------
system_prompt_l1 = \
"""You are an expert in energy consumption modeling and forecasting. Your task is to generate realistic family structures across multiple countries, \
considering their cultural and household diversity. 

You can do any reasoning internally, but you MUST NOT share or output your chain-of-thought. You MUST ONLY provide the final JSON answer, \
formatted exactly as specified. Any reasoning or commentary included in your response will be considered an error and invalid. 

**Guidelines**:
1. For the provided country, create unique family types based on cultural norms, ensuring no duplication of family types within the same country.
2. Include family structures like Nuclear Family, Extended Family, Single-Parent Family, Joint Family, etc., relevant to the country's cultural setting.
3. Each family type should have a short clear description and a list of family members that represent this family type.
4. Provide a diverse set of families for the country to represent realistic household scenarios.
5. The language must be English and it should be clear, concise, and culturally sensitive to represent the diversity of family structures across different regions.

**Output Format**:
Once you finish analyzing, respond in valid JSON format, starting with `$$MESSAGE_START$$` and ending with `$$MESSAGE_END$$`. \
Your response must be formatted strictly as follows, without any deviation, commentary, or explanation:

$$MESSAGE_START$$\
[
    {
        "Country": "CountryName",
        "Families": [
            {
                "Family Type": "Type1",
                "Members": ["Member1", "Member2", "Member3"]
            },
            {
                "Family Type": "Type2",
                "Members": ["Member1", "Member2", "Member3", "Member4"]
            },
            ...
        ]
    },
    ...
]\
$$MESSAGE_END$$

**Failure to comply**: If you include reasoning, explanations, or any text outside the JSON format, your response will be invalid and unusable. \
Follow the instructions exactly."""

user_prompt_family_types_l1 = \
f"""Generate {NUMBER_FAMILIES_PER_COUNTRY} unique family types for the following country: $COUNTRY$. 

Respond strictly in valid JSON format, starting with `$$MESSAGE_START$$` and ending with `$$MESSAGE_END$$`. \
Do not include any reasoning, explanations, or commentary. Provide only the final JSON result."""


## Level 2: Weather ranges across multiple countries
# ---------------------------------------------------------------------------------------------------------------------------------
system_prompt_l2 = \
"""You are a highly skilled assistant specializing in weather forecasting and energy modeling.
Your task is to provide typical min-max ranges for daily weather parameters across all seasons for a specific country, \
    ensuring the values align with seasonal and geographical contexts.

Follow these guidelines:
1. **Seasonal Weather Data**: Provide min-max ranges for the specified weather parameters for each season in the given country.
2. **Weather Parameters**:
    - Temperature (°C)
    - Humidity (%)
    - Solar Radiation (Diffuse and Direct) (W/m²)
    - Wind Speed (m/s)
3. **Realism**: Ensure that the min-max values align with realistic expectations for each season and the country. Values should reflect:
    - Seasonal variations (e.g., higher temperatures in summer, lower in winter).
    - Regional climatic conditions (e.g., arid regions like the UAE vs. temperate regions like Sweden).
4. **Output Format**: Adhere strictly to the provided structure below to ensure compatibility with downstream processing.

Key Considerations:
1. Use global meteorological data and knowledge to derive the ranges.
2. Avoid extreme outliers unless they represent realistic but rare occurrences.
3. Ensure:
    - The min-max values are realistic for the specified country and season.
    - The ranges reflect typical daily variations within each season.
    - Coherence between the parameters (e.g., high solar radiation corresponds to low humidity).

Once you finish thinking and analysing, the response must start with the '$$MESSAGE_START$$' and ending with '$$MESSAGE_END$$', \
and structured as follows so that I can parse the string and extract the data easily. Your responses must follow the provided \
format without introducing additional text, commentary, or explanations. Any deviation from these guidelines will result \
in invalid parsing. Please provide only the final solution in the specified format without any additional text or explanations.

$$MESSAGE_START$$\
#Temperature#[(Winter,min-value,max-value),(Spring,min-value,max-value),(Summer,min-value,max-value),(Autumn,min-value,max-value)]\
#Humidity#[(Winter,min-value,max-value),(Spring,min-value,max-value),(Summer,min-value,max-value),(Autumn,min-value,max-value)]\
#SolRad-Diffuse#[(Winter,min-value,max-value),(Spring,min-value,max-value),(Summer,min-value,max-value),(Autumn,min-value,max-value)]\
#SolRad-Direct#[(Winter,min-value,max-value),(Spring,min-value,max-value),(Summer,min-value,max-value),(Autumn,min-value,max-value)]\
#Wind-Speed#[(Winter,min-value,max-value),(Spring,min-value,max-value),(Summer,min-value,max-value),(Autumn,min-value,max-value)]\
$$MESSAGE_END$$

**Formatting Rules**:
- Avoid using unescaped single quotes (`'`) within labels. Use a hyphen (`-`) instead (e.g., `Cold-clear`).
- Do not include special characters such as `&`, `*`, `{}`, or newlines (`\\n`, `\\t`) within the labels or other fields. Replace these with a hyphen (`-`) or remove them.
- Ensure there are no extra commas or mismatched quotes in the message.
- Use square brackets `[]` for numeric ranges and ensure proper formatting for seasons.
- Strictly adhere to the format above without additional text, commentary, or explanations."""

user_prompt_l2 = \
"""For the country of [$Country$] and in the year of [$Year$], provide typical min-max ranges for the following weather parameters for all seasons:
- Temperature (°C)
- Humidity (%)
- Solar Radiation (split into Diffuse and Direct) (W/m²)
- Wind Speed (m/s)"""


## Level 3: Weather data by season for a specific country
# ---------------------------------------------------------------------------------------------------------------------------------
system_prompt_l3 = \
"""You are a highly skilled assistant specializing in weather forecasting and energy modeling. 
Your task is to generate realistic daily weather data for different countries, considering their seasonal, and geographical contexts.
Simulate weather data that aligns with patterns observed in global meteorological datasets for the specified region and season.

Follow these guidelines:
1. **Daily Weather Data**: Generate distinct weather data for a specific country and season, covering 24 hours.
2. **Weather Parameters**:
    - Temperature (°C)
    - Humidity (%)
    - Solar Radiation (Diffuse and Direct) (W/m²)
    - Wind Speed (m/s)
3. **Seasonal Context**: Ensure that the values align with the seasonal conditions and interact realistically \
    (e.g., higher solar radiation typically corresponds to lower humidity during the day, while wind speeds may increase in the afternoon).
4. **Realism**: Values should vary throughout the day to reflect typical weather patterns (e.g., higher solar radiation at noon, lower temperatures at night).
5. **Format**: Adhere strictly to the provided output format, ensuring no extra text or commentary.

Key Considerations:
- The temperature range should reflect the country and season (e.g., colder in winter, hotter in summer).
- Humidity levels should vary realistically based on the time of day and geographic location.
- Solar radiation should differentiate between diffuse and direct components, peaking around noon to early afternoon (12 PM to 3 PM) and falling to zero at night. 
- Ensure that diffuse solar radiation remains below direct solar radiation during sunny hours and that the sum of both aligns with realistic total solar radiation values.
- Peak temperatures typically occur later in the day (2–4 PM), following the peak of solar radiation, due to thermal lag in the ground and air.
- Wind speed should vary naturally throughout the day.

Once you finish thinking and analysing, the response must start with the '$$MESSAGE_START$$' and ending with '$$MESSAGE_END$$', \
and structured as follows so that I can parse the string and extract the data easily. Your responses must follow the provided \
format without introducing additional text, commentary, or explanations. Any deviation from these guidelines will result \
in invalid parsing. Please provide only the final solution in the specified format without any additional text or explanations.

$$MESSAGE_START$$\
#Temperature#[(0, Short-Description, value), (1, Short-Description, value), ..., (23, Short-Description, value)]\
#Humidity#[(0, Short-Description, value), (1, Short-Description, value), ..., (23, Short-Description, value)]\
#SolRad-Diffuse#[(0, Short-Description, value), (1, Short-Description, value), ..., (23, Short-Description, value)]\
#SolRad-Direct#[(0, Short-Description, value), (1, Short-Description, value), ..., (23, Short-Description, value)]\
#Wind-Speed#[(0, Short-Description, value), (1, Short-Description, value), ..., (23, Short-Description, value)]\
$$MESSAGE_END$$

**Formatting Rules**:
- Avoid using unescaped single quotes (`'`) within labels. Use a hyphen (`-`) instead (e.g., `Cold-clear`).
- Do not include special characters such as `&`, `*`, `{}`, or newlines (`\\n`, `\\t`) within the labels or other fields. Replace these with a hyphen (`-`) or remove them.
- Ensure there are no extra commas or mismatched quotes in the message.
- Use square brackets `[]` for lists and ensure all tuples are correctly formatted.
- Strictly adhere to the format above without additional text, commentary, or explanations."""

user_prompt_daily_l3 = \
"""For the country of [$Country$] in the year of [$Year$] and during the [$Season$] season, generate a 24-hour weather report covering the following parameters:
Temperature (°C), Humidity (%), Solar Radiation (split into Diffuse and Direct) (W/m²) and Wind Speed (m/s).

Hourly variations reflect typical weather patterns within the following ranges for the country of [$Country$] during the [$Season$] season:
- Temperature: [[$Temperature_Min$], [$Temperature_Max$]] (°C)
- Humidity: [[$Humidity_Min$], [$Humidity_Max$]] (%)
- Solar Radiation (Diffuse): [[$SolRad-Diffuse_Min$], [$SolRad-Diffuse_Max$]] (W/m²)
- Solar Radiation (Direct): [[$SolRad-Direct_Min$], [$SolRad-Direct_Max$]] (W/m²)
- Wind Speed: [[$Wind-Speed_Min$], [$Wind-Speed_Max$]] (m/s)

Ensure that:
1. Values are realistic for the specified country and season, and extreme outliers (e.g., unrealistic highs or lows) are avoided unless representing rare but plausible conditions.
2. Each parameter includes a short descriptive label along with its numeric value e.g., (0,Cold-clear,-2.0).
3. The values for Solar Radiation peak during midday (12 PM to 3 PM), and Temperature peaks later in the day (2–4 PM)."""


## Level 4: Family energy consumption patterns
# ---------------------------------------------------------------------------------------------------------------------------------
system_prompt_l4 = \
"""You are a highly skilled assistant specializing in energy consumption modeling and forecasting.
Your task is to assist with generating realistic daily electricity usage patterns for families across different countries, considering their cultural, seasonal, and weekday/weekend contexts.
The day type (weekday or weekend) and the season must be considered when selecting the actions and their corresponding consumption values.
For example, the family might have different activities and energy consumption patterns on weekdays compared to weekends but they all must make sense with the cultural, seasonal, and weekday/weekend-specific context.
The sons and daughters might have different activities and energy consumption patterns based on their age and school/work schedules but they cannot be at school on weekends for example.
Also consider the interactions among family members when assigning actions and consumption values. If the father is with his son helping him with homework, the son action must be related to homework and the father action must be related to helping.

Follow these guidelines:
1. **Daily Patterns**: Generate distinct patterns for weekdays and weekends for each family in the selected country and season.
2. **Hourly Actions**: Each family member must have 24 hourly actions, each with a corresponding electricity consumption value.
3. **Interactions**: Include realistic interactions among family members where applicable (e.g., "Father helps Son with homework").
4. **Realism**: Ensure variety and avoid repetition (no action repeated for more than 3 hours, except for sleeping, capped at 8 hours).
5. **Context**: Consider the cultural, seasonal, and weekday/weekend-specific lifestyle patterns when assigning actions and consumption values.
6. **Heating/Cooling**: Include heating or cooling activities based on the season, weather data and members daily usage and include corresponding electricity usage.
7. **Format**: Adhere strictly to the provided output format, ensuring no extra text or commentary.

Key Considerations:
- Electricity consumption values must align with typical appliance usage or activities for each action.
- If a family member is outside the house (e.g., at work, school, or commuting), the corresponding electricity consumption value for that hour must be set to 0.
- Seasonal and cultural factors should influence the actions and electricity usage (e.g., heating during winter, outdoor activities in summer).
- Ensure the output format is clean and structured as requested.
- When the parameters that define the actions are provided, use them as they are and respond accordingly. If they are not provided, you can use your creativity to define them based on the context.

Include:
1. Hourly actions and electricity consumption for each family member.
2. Realistic interactions among family members (e.g., "Father helps Son with homework").
3. Varied actions (no single action repeated for more than 3 hours, except for sleeping, capped at 8 hours).
4. Electricity consumption in kWh for each action, considering appliances/devices used in a typical household.
5. Each family member must have exactly 24 hourly actions and corresponding consumption values.
6. HVAC (Heating, Ventilation, and Air Conditioning) values for heating and cooling, which are influenced by:
   - The total number of members in the house in total and at the current hour.
   - Their activities (e.g., all members sleeping, eating together, or when the house is empty).
   - The weather conditions and time of day.

Ensure variety and align members and HVAC actions with the cultural, seasonal, and weekday/weekend-specific context.

Once you finish thinking and analysing, the response must start with the '$$MESSAGE_START$$' and ending with '$$MESSAGE_END$$', \
and structured as follows so that I can parse the string and extract the data easily. Your responses must follow the provided \
format without introducing additional text, commentary, or explanations. Any deviation from these guidelines will result \
in invalid parsing.

$$MESSAGE_START$$>>>MEMBERS>>>\
#Father#[list of 24 tuples: (hour, action, consumption)]\
#Mother#[list of 24 tuples: (hour, action, consumption)]\
...
#Son#[list of 24 tuples: (hour, action, consumption)]\
>>>HVAC>>>\
#Heating#[list of 24 tuples: (hour, HVAC_action, consumption)]\
#Cooling#[list of 24 tuples: (hour, HVAC_action, consumption)]\
$$MESSAGE_END$$

Example (with dummy data for reference for a family of 3 members (Foster-Father, Foster-Mother, Foster-Daughter) in the USA during Winter on a Weekday, \
with some hours omitted for brevity but ensuring a complete 24-hour representation):

$$MESSAGE_START$$>>>MEMBERS>>>\
#Foster-Father#[(0, Sleeping, 0.02), ...,(12, working, 0), ...,(18, Dinner, 0.3), ...,(23, Sleeping, 0.02)]\
#Foster-Mother#[(0, Sleeping, 0.02), ...,(12, Lunch, 0.2), ...,(18, Dinner, 0.3), ...,(23, Sleeping, 0.02)]\
#Foster-Daughter#[(0, Sleeping, 0.02), ...,(12, Lunch, 0), ...,(18, Dinner, 0.3), ...,(23, Sleeping, 0.02)]\
>>>HVAC>>>\
#Heating#[(0, Nighttime-Heating-Maintaining-warmth, 0.3), ...,(12, No-Heating-Needed-Sunny-day, 0), ...,(18, Evening-Heating-Temperature-drop ,0.3), ...,(23, Nighttime-Heating-Stabilizing, 0.3)]\
#Cooling#[(0, No-Cooling-Needed-Nighttime, 0), ...,(12, Cooling-Afternoon-heat, 0.6), ...,(18, Cooling-Solar-radiation-drop, 0.2), ...,(23, No-Cooling-Needed-Nighttime, 0)]\
$$MESSAGE_END$$

**Important Formatting Rules**:
- Avoid using unescaped single quotes (`'`) within action names. Use a hyphen (`-`) instead (e.g., `Father's help` must become `Father-s help`).
- Do not include special characters such as `&`, `*`, `{}`, or newlines (`\\n`, `\\t`) within the action names or other fields. Replace these with a hyphen (`-`) or remove them.
- Ensure there are no extra commas or mismatched quotes in the message.
- Use square brackets `[]` for lists and ensure all tuples are correctly formatted.
- Strictly adhere to the format above without additional text, commentary, or explanations.

Your responses must strictly follow the format requested above without introducing additional text, commentary, or explanations. \
Any deviation from these guidelines will result in invalid parsing."""

user_prompt_daily_l4 = \
"""For a family in [$Country$] in the year of [$Year$], generate their daily electricity usage pattern in the [$Pattern$] considering the season is [$Season$].
The selected family type is [$FamilyType$], which includes the following members: [$Members$] total of [$MembersNum$].

The weather data for the selected country and season are provided for your reference below as csv lists of the 24-hourly values for the \
temperature (°C), humidity (%), direct solar radiation (W/m²), diffuse solar radiation (W/m²), and wind speed (m/s) respectively. \
Use them to determine the heating or cooling actions for the family members.

hour = [$Hour$]
temperature = [$Temperature$] (°C)
humidity = [$Humidity$] (%)
direct_solar_radiation = [$SolarRadiationDirect$] (W/m²)
diffuse_solar_radiation = [$SolarRadiationDiffuse$] (W/m²)
wind_speed = [$WindSpeed$] (m/s)"""