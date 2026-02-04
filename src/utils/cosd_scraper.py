import json
import pandas as pd

from bs4 import BeautifulSoup
from datetime import datetime

def load_html_file(file_path):
    """
    Load a given html file.
    Args:
        file_path (str): OS Path to file
    Returns: 
        class['bs4.BeautifulSoup']: File contents (HTML)
    """

    with open(file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
        return soup
    
def get_file_section_names(soup):
    """
    Get all section names in the file.
    Args:
        soup (class['bs4.BeautifulSoup']): File contents (HTML)
    Returns:
        list(str): List of section names
    """

    divs = soup.find_all("div", class_="section level2")
    section_names = []

    for div in divs:
        section_names.append(div.get("id"))

    return section_names

def get_file_child_div_names(soup, parent_div_name):
    """
    Get all subsection names in a given section.
    Args:
        soup (class['bs4.BeautifulSoup']): File contents (HTML)
        parent_div_name (str): Parent div name
    Returns:
        list(str): List of child div names
    """
    parent_div = soup.find("div", id=parent_div_name)

    #Get the level of the current div
    div_class_names = parent_div["class"]
    parent_level = int([x for x in div_class_names if x.startswith("level")][0][-1])
    child_level = parent_level + 1

    child_divs = parent_div.select(f'div[class^="section level{child_level}"]')
    child_names = []

    for div in child_divs:
        child_names.append(div.get("id"))

    return child_names

def pull_data_from_hoverfield(hover_text):
    """
    Extract the numerator and denominator from hover_text.
    Args:
        hover_text: Array containing the on-hover data strings
    Returns:
        array(str): Numerator values
        array(str): Denominator values 
    """
    num_arr = []
    den_arr = []

    if type(hover_text) != list:
        hover_text = [hover_text]

    for data_point in hover_text:
        num_section = data_point.split("Numerator:")[1].split("<")[0].strip()
        den_section = data_point.split("Denominator:")[1].split("<")[0].strip()

        num_arr.append(num_section)
        den_arr.append(den_section)

    return num_arr, den_arr

def load_data_from_tab(soup, tab_div_id):
    """
    Load data from a given tab using the div_id 
    Args:
        soup (class['bs4.BeautifulSoup']): File contents (HTML)
        tab_div_id (str): Tab div name
    Returns:
        DataFrame: Pandas data frame containing the tab data
    """

    parent_div = soup.find("div", id=tab_div_id)
    tab_name = parent_div.find('h4').text
    
    section_num = tab_name.split(" ")[0]
    section_name = tab_name[len(section_num)+1:]

    tab_div = soup.find("div", id=tab_div_id)

    data_script = tab_div.find("script", type="application/json")

    data_json = json.loads(data_script.string)

    #Get plot title
    tab_plot_title = data_json["x"]["layout"]["title"]["text"]
    if len(tab_plot_title.split("(")) > 1:
        plot_name = tab_plot_title.split("(")[1].split(")")[1].strip()
    else:
        plot_name = tab_plot_title

    data_type = data_json["x"]["data"][0]["type"]

    if data_type == "scatter":
        data_dicts = data_json["x"]["data"][1:]
    if data_type == "bar":
        data_dicts = data_json["x"]["data"]

    if "hovertemplate" in data_dicts[0].keys() and data_type == 'bar':
        hover_fields = True
    else:
        hover_fields = False

    df_data = pd.DataFrame()

    if not hover_fields:
        for data_dict in data_dicts:
            df_category = pd.DataFrame(
                {
                    "COSD_SECTION_ID": tab_div_id,
                    "COSD_SECTION_NUM": section_num,
                    "COSD_SECTION_NAME": section_name,
                    "COSD_PLOT_NAME": plot_name,
                    "CATEGORY": data_dict["name"],
                    "X": data_dict["x"],
                    "Y": data_dict["y"]
                }
            )

            df_data = pd.concat([df_data, df_category], ignore_index=True)
    else:
        for data_dict in data_dicts:
            num, den = pull_data_from_hoverfield(data_dict["hovertemplate"])
            df_category = pd.DataFrame(
                {
                    "COSD_SECTION_ID": tab_div_id,
                    "COSD_SECTION_NUM": section_num,
                    "COSD_SECTION_NAME": section_name,
                    "COSD_PLOT_NAME": plot_name,
                    "CATEGORY": data_dict["name"],
                    "X": data_dict["x"],
                    "Y": data_dict["y"],
                    "NUMERATOR":num,
                    "DENOMINATOR":den
                }
            )

            df_data = pd.concat([df_data, df_category], ignore_index=True)

    return df_data

def file_name_metadata(file_name):
    """
    Uses the HTML file name to get the date and organisation as variables
    Args:
        file_name: File name of the HTML file; assumes YEAR_MONTH_ORGCODE_ORGNAME.html name
    Returns:
        date: Date of the file set to the first of the month
        str: Organisation code
        str: Organisation name
    """
    #Assumes YEAR_MONTH_ORGCODE_ORGNAME.html name
    file_name = file_name.replace("_FIX", "")

    file_name_parts = file_name.split(".html")[0].split("_")
    
    meta_year = file_name_parts[0]
    meta_month = file_name_parts[1]
    meta_date = datetime.strptime(
        meta_year+"_"+meta_month+"_01", "%Y_%m_%d").date()
    
    meta_org_code = file_name_parts[2]
    meta_org_name = " ".join(file_name_parts[3:])

    return meta_date, meta_org_code, meta_org_name

def extract_all_tabs_data(data_dir, file_name):
    """
    For a given COSD HTML file, pull data from all embedded tabs in the file
    Args:
        data_dir: Directory containing the data file
        file_name: Target data file name
    Returns:
        dict (DataFrame): Dictionary of data frames from all extracted data tabs
    """
    file_path = data_dir + file_name
    soup = load_html_file(file_path)

    section_names = get_file_section_names(soup)
    extracted_data = {}

    for section_name in section_names:
        subsection_names = get_file_child_div_names(soup, section_name)

        for subsection_name in subsection_names:
            tab_names = get_file_child_div_names(soup, subsection_name)
            
            for tab_name in tab_names:
                #Check tab is within a tabset
                tab_div = soup.find("div", id=tab_name)
                if tab_div.find_parent("div", class_="tabset") is not None:
                    #print(subsection_name, tab_name)
                    extracted_data[tab_name.replace("-", "_")] = load_data_from_tab(soup, tab_name)

    #Get metadata details from the file name and add to dataframes  
    meta_date, meta_org_code, meta_org_name = file_name_metadata(file_name)

    for dataset in extracted_data.keys():
        extracted_data[dataset]["DATE_DATA"] = meta_date
        extracted_data[dataset]["ORG_CODE"] = meta_org_code
        extracted_data[dataset]["ORG_NAME"] = meta_org_name

    return extracted_data

def extract_overall_ranking_data(data_dir, file_name):
    """
    For a given COSD HTML file, extract the Overall Ranking table
    Args:
        data_dir: Directory containing the data file
        file_name: Target data file name
    Returns:
        dict (DataFrame): Dictionary of data frames from all extracted data tabs
    """
    file_path = data_dir + file_name
    soup = load_html_file(file_path)

    appendix_div = soup.find("div", id="appendices")

    section_div = appendix_div.find_all(
        "div", 
        id=lambda x: x and x.endswith('overall-ranking'), 
        class_="section level4"
    )

    if len(section_div) == 0:
        raise Exception("The overall ranking table was not found")
    else:
        section_div = section_div[0]

    section_heading = section_div.find('h4').text
    
    section_num = section_heading.split(" ")[0]
    section_name = section_heading[len(section_num)+1:]

    ort_div = soup.find("div", id=section_div.get("id"))

    data_script = ort_div.find("script", type="application/json")

    data_json = json.loads(data_script.string)

    #Adjustment for older file structure
    if len(data_json["x"]["options"]["columnDefs"]) == 1:
        col_string = data_json["x"]["container"]
        cols = col_string.split("<th>")[1:]
        column_names_raw = [x.split("</th>")[0] for x in cols]
    else:
        column_names_raw = [x["name"] for x in data_json["x"]["options"]["columnDefs"][1:]]

    column_names = [x.upper().replace(" ", "_").replace("(%)", "PER") for x in column_names_raw]
    
    df_raw = pd.DataFrame(
        data=data_json["x"]["data"]
    )

    df = df_raw.transpose()
    df.columns = column_names

    df["COSD_SECTION_ID"] = section_div.get("id").replace("-", "_")
    df["COSD_SECTION_NUM"] = section_num
    df["COSD_SECTION_NAME"] = section_name

    #Reorder columns
    df.insert(0, "COSD_SECTION_ID", df.pop("COSD_SECTION_ID"))
    df.insert(1, "COSD_SECTION_NUM", df.pop("COSD_SECTION_NUM"))
    df.insert(2, "COSD_SECTION_NAME", df.pop("COSD_SECTION_NAME"))

    #Get metadata details from the file name and add to dataframes  
    meta_date, meta_org_code, meta_org_name = file_name_metadata(file_name)

    df["DATE_DATA"] = meta_date

    return df