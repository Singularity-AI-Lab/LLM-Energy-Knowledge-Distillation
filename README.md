# Knowledge Distillation from LLMs for Household Energy Modeling

**Authors:** [Mohannad Takrouri](https://github.com/MohannadTak/), [Nicolás M. Cuadrado](https://nicolascuadrado.com/), and [Martin Takáč](https://mtakac.com/)

**Paper:** [Knowledge Distillation from Large Language Models for Household Energy Modeling](https://arxiv.org/abs/example) 

This repository contains a structured pipeline for generating and analyzing weather data, energy consumption patterns, and family structures using multiple Large Language Models (LLMs). The process involves multiple levels of data generation and processing, from obtaining family structures to simulating their energy consumption profiles across different seasons and weekdays/weekends.

---
## 📂 Repository Structure

```
├── config.py                                  # Configuration file (LLM models, constants, paths, and settings)
├── prompts.py                                 # Contains structured prompts for LLMs at different stages
├── utils.py                                   # Helper functions for logging, file handling, and data extraction
├── 01_get_multi_llm_response.py               # Main script that executes LLM queries and logs results
├── 02_master_plot_and_extend.ipynb            # Runs multiple notebooks to process and visualize data
├── 02A_plot_llm_response.ipynb                # Plots LLM-generated responses
├── 02B_create_base_dataframes.ipynb           # Creates base yearly dataframes per country
├── 02C_expand_to_yearly_dataframes.ipynb      # Expands data per country (holidays, weekends, etc.)
├── 02D_plot_energy_signatures.ipynb           # Generates energy signature plots
├── environment.yml                            # Environment dependencies for easy setup
├── README.md                                  # This file
```

---
## 🚀 Flow of Execution

### 🔹 **Step 1: Configuration (config.py)**
- Defines the available LLM models.
- Specifies countries, weather parameters, and family types.
- Sets logging paths, output directories, and constants.

### 🔹 **Step 2: Prompting LLMs (01_get_multi_llm_response.py)**
- **Level 1**: Generates family structures per country.
- **Level 2**: Determines typical weather parameter ranges for each season.
- **Level 3**: Creates realistic daily weather profiles based on seasonal variations.
- **Level 4**: Generates daily energy consumption patterns for families.

### 🔹 **Step 3: Data Processing & Expansion (02_master_plot_and_extend.ipynb)**
- Runs 4 notebooks sequentially:
  1. `02A_plot_llm_response.ipynb`: Visualizes LLM-generated responses.
  2. `02B_create_base_dataframes.ipynb`: Creates base yearly profiles for each country.
  3. `02C_expand_to_yearly_dataframes.ipynb`: Expands data per country considering weekends & holidays.
  4. `02D_plot_energy_signatures.ipynb`: Plots energy signatures of families per country.

---
## 🔧 Installation & Setup

### 1️⃣ **Clone the repository**
```bash
git clone https://github.com/Singularity-AI-Lab/LLM-Energy-Knowledge-Distillation.git
cd LLM-Energy-Knowledge-Distillation
```

### 2️⃣ **Create and activate the environment**
```bash
conda env create -f environment.yml
conda activate kdllm
```

### 3️⃣ **Set the configuration parameters**
Edit the 
```bash
config.py
```

### 4️⃣ **Run the LLM data generation script**
```bash
python 01_get_multi_llm_response.py
```

### 5️⃣ **Process and visualize the data**
Run the master plotting and processing notebook:
```bash
02_master_plot_and_extend.ipynb
```

---
## 📊 Expected Outputs
- **Generated JSON files** with family structures.
- **Generated CSV files** with weather data, and energy consumption patterns.
- **Log files** detailing API calls, response times, and token usage.
- **Plots** visualizing energy consumption trends and weather variations per country.

---
## ⚡ Notes
- If `USE_TMY = True` in `config.py`, precomputed Typical Meteorological Year (TMY) data is used instead of LLM-generated weather data. Stage 2 and Stage 3 will be skipped.
- Logs are saved under `logfile_l1.txt`, `logfile_l2.txt`, etc., for different stages.
- Ensure you have an **API key** for the LLM models set as an environment variable (`DEEPINFRA_TOKEN`).

---
## 🔗 References
- **LLM Models Used**:
1. [Meta-Llama-3.1-405B-Instruct](https://deepinfra.com/meta-llama/Meta-Llama-3.1-405B-Instruct)
2. [Meta-Llama-3.3-70B-Instruct](https://deepinfra.com/meta-llama/Llama-3.3-70B-Instruct)
3. [Microsoft/Phi-4](https://deepinfra.com/microsoft/phi-4)
4. [Qwen/QwQ-32B-Preview](https://deepinfra.com/Qwen/QwQ-32B-Preview)
5. [Deepseek-AI/DeepSeek-R1](https://deepinfra.com/deepseek-ai/DeepSeek-R1)

Happy Researching! 🚀
