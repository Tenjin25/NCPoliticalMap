# Scripts for North Carolina Election Data Analysis

This folder contains Python scripts used to automate the extraction, cleaning, and analysis of North Carolina election data for the congressional realignment case study. These scripts are provided for transparency and to help others reproduce or extend the analysis.

## How to Use These Scripts

### 1. Prerequisites
- **Python 3.8+** is recommended.
- Required packages: `pandas`, `numpy`, and `openpyxl` (for Excel file support). Install them with:
  ```sh
  pip install pandas numpy openpyxl
  ```
- Place all relevant raw data files (CSV/Excel) in the appropriate data directory as referenced in each script.

### 2. Script Descriptions

- **extract_nc01_presidential_margins.py**
  - Extracts district-level presidential margins for NC-01 and outputs results as CSV.
  - Usage:
    ```sh
    python extract_nc01_presidential_margins.py
    ```

- **make_election_only_files.py**
  - Generates simplified CSVs containing only election results (removes extra columns).
  - Usage:
    ```sh
    python make_election_only_files.py
    ```

- **extract_election_results.py**
  - (If included) Extracts and summarizes election results for all districts and years.
  - Usage:
    ```sh
    python extract_election_results.py
    ```

- **merge_full_statistics.py / merge_and_clean_full_statistics.py**
  - (If included) Merges multiple datasets and cleans data for analysis.
  - Usage:
    ```sh
    python merge_full_statistics.py
    # or
    python merge_and_clean_full_statistics.py
    ```

### 3. Output
- Output files (e.g., `*_election_results_only.csv`) will be saved in the same directory or as specified in each script.
- Review the script comments for details on input/output file locations and any required arguments.

### 4. Customization
- You may modify the scripts to analyze other districts, years, or races by changing the input file paths or parameters as needed.

---

**Note:** These scripts are provided as-is for educational and research purposes. For questions or improvements, please open an issue or submit a pull request on the main project repository.

---

*AI Assistance Disclosure: Some scripts and documentation were streamlined with the help of GitHub Copilot (AI), but all substantive analysis and logic reflect the author's own work.*
