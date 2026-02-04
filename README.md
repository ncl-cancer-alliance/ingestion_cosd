# Ingestion COSD (HTML Files)

Ingestion pipeline for to extract data tables from the COSD HTML files (including both data in tables and plots).

## Quick Start
 ```bash
# Clone and setup
git clone https://github.com/ncl-cancer-alliance/ingestion_cosd

#Setup virtual environment (venv)
python -m venv venv

#Enable virutal environment (venv)
Set-ExecutionPolicy Unrestricted -Scope Process;  venv\Scripts\activate

#Install the project packages to the virtual environment
pip install ./requirements.txt -r

#Manually install the snowflake-connector-python package (this prevents having to authenticate via the Snowflake browser multiple times)
pip install snowflake-connector-python[secure-local-storage]
```

If using the team SharePoint as the source for the COSD HTML files, the team SharePoint folder needs to be added to your local file explorer for the code to access ([Guide](https://support.microsoft.com/en-us/office/add-shortcuts-to-shared-folders-in-onedrive-d66b1347-99b7-4470-9360-ffc048d35a33)).

The expected path to the data files is (where the bold fields are set in the .env file): `C:\Users\$USERNAME$\$NHS_ONEDRIVE_DIR$\$WORK_DIR$\...\$DATA_SOURCE_DIR$`



## What This Project Does
Processes the nationally distributed COSD HTML files. These files contain data tables and interactive visuals containing underlying data which is parsed from the HTML source code and output as csv files and uploaded to the Snowflake environment as standalone tables.

The destination table schema is currently: `DATA_LAKE__NCL.CANCER__COSD_HTML`

## Usage
### Source File Structure
This code assumes the following file structure is used:
* COSD HTML files saved in a SharePoint location
* The files are contained within a directory containing both a "processed" and "unprocessed" folder.

For example (if you save the files in a directory called "COSD HTML"):
```
C:/Users/your-user-name/one-drive-dir-name/SharePoint-parent-folder/.../COSD HTML/
├── processed/
└── unprocessed/
    ├── 2026_1_XXX_My_Hospital.html
    ├── 2026_1_YYY_My_Other_Hospital.html
    └── 2026_2_XXX_My_Hospital.html
```

_When the code is ran, it will build the subdirectories required within processed if they do not already exist._

### Process
1. Save the new HTML files in the unprocessed directory
2. Enable the virutal environment in your directory
3. Run the src/main.py script (The terminal should display progress as the code runs)

## Scripting Guidance

Please refer to the Internal Scripting Guide documentation for instructions on setting up coding projects including virtual environments (venv).

The Internal Scripting Guide is available here: [Internal Scripting Guide](https://nhs.sharepoint.com/:w:/r/sites/msteams_38dd8f/Shared%20Documents/Document%20Library/Documents/Git%20Integration/Internal%20Scripting%20Guide.docx?d=wc124f806fcd8401b8d8e051ce9daab87&csf=1&web=1&e=qt05xI)

## Changelog

### [1.0.0] - 2026-02-04
#### Added
- Initial release of the code


## Licence
This repository is dual licensed under the [Open Government v3]([https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/) & MIT. All code can outputs are subject to Crown Copyright.

## Contact
Jake Kealey - jake.kealey@nhs.net

*The contents and structure of this template were largely based on the template used by the NCL ICB Analytics team available here: [NCL ICB Project Template](https://github.com/ncl-icb-analytics/ncl_project)*