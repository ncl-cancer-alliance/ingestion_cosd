import os

from datetime import datetime
from dotenv import load_dotenv
from os import getenv

import utils.cosd_scraper as cosd
import utils.snowflake_ncl as sf

import warnings

#Load environment variables
load_dotenv(override=True)

# Ignore all warnings - snowflake write_pandas function always generates a warning
warnings.filterwarnings("ignore")

def get_files(data_dir, file_ext=""):
    """
    Get a list of data files at the listed data_dir location.
    Args:
        data_dir: Path to data files
        file_ext (optional): Limit data files to a specific extension
    Returns:
        list(str): List of file names
    """
    dir_list = [x for x in os.listdir(data_dir) if x.endswith(file_ext)]

    #Cleanse the list
    if dir_list == []:
        e_message = f"No files were found in {data_dir}" 
        raise Exception(e_message)

    return dir_list

def archive_csv(archive_dir, file_name, dataset_id, df):
    """
    Function to save the extracted data as csv files 
    Args:
        archive_dir: Destination directory for the datafiles
        file_name: Source file name to get the metadata from
        dataset_id: Name of the dataset for the destination filename
        df: Pandas dataframe containing the data
    """

    #Get org code
    org_code = file_name.split("_")[2]
    archive_path = archive_dir + "csv/" + org_code + "/" + file_name
    os.makedirs(archive_path, exist_ok=True)

    df.to_csv(archive_path + "/" + dataset_id + ".csv", index=False)

def archive_html(archive_dir, data_dir, file_name):
    """
    Function to save the source html files in an archived location
    Args:
        archive_dir: Destination directory for the datafiles
        file_name: Source file name to get the metadata from
        dataset_id: Name of the dataset for the destination filename
        df: Pandas dataframe containing the data
    """
    #Get org code
    org_code = file_name.split("_")[2]
    archive_path = archive_dir + "html/" + org_code + "/"
    os.makedirs(archive_path, exist_ok=True)

    src_file = data_dir + file_name
    dst_file = archive_path + file_name

    file_name = file_name.replace("_FIX", "")

    if os.path.exists(dst_file):
        print(f"Warning: The HTML file {dst_file} already exists in the archive directory")
    else:
        os.rename(src_file, dst_file)

def process_files(files, data_dir, process_tabs=True, process_table=True, archive_dir=False, debug=True):
    """
    Process all COSD HTML files given and upload to Snowflake
    Args:
        files: List of file names
        data_dir: Path to data files
        process_tabs (optional): If True then the tab (plot) embedded data is extracted from the HTML files
        process_table (optional): If True then the Overall Ranking embedded data is extracted from the HTML files
        archive_dir (optional): Destination to move files after processing
        debug (optional): If True then prints progress in terminal during execution
    Returns:
        None
    """

    ctx = sf.create_connection(
        account=getenv("SNOWFLAKE_ACCOUNT"), 
        user=getenv("SNOWFLAKE_USER"), 
        role=getenv("SNOWFLAKE_ROLE"),
        warehouse=getenv("SNOWFLAKE_WAREHOUSE"))

    for file_name in files:

        processing_flag = True

        if debug:
            print(f"Processing: {file_name}...")

        #Code to extract the data table
        if process_table:
            
            ort_dir = archive_dir + "csv/overall_ranking_table/"
            ort_file_name = file_name.split("_")[0] + "_" + file_name.split("_")[1] + ".csv"
            ort_file_path = ort_dir + ort_file_name

            if not(os.path.exists(ort_file_path)):
                #Build the destination dir if it doesn't exist
                os.makedirs(ort_dir, exist_ok=True)

            df_ort = cosd.extract_overall_ranking_data(data_dir, file_name)

            ds_id = df_ort.iloc[0,0]

            df_ort["TIMESTAMP"] = datetime.now()

            if debug:
                print("\t"+ds_id)

            description = f"Table containing {ds_id} data from the COSD HTML files. Contact: {sf.get_user(ctx)}"

            res = sf.upload_df(
                    ctx,
                    df_ort, 
                    table_name="_".join(ds_id.split("_")[1:]),
                    database=getenv("DESTINATION_DATABASE"),
                    schema=getenv("DESTINATION_SCHEMA"),
                    replace=False,
                    table_columns=list(df_ort.columns),
                    table_description=description,
                    debug=False
                )
                
            #Set flag to say not all sheets were uploaded successfully. 
            # This prevents the file getting archived if it needs to be re-run
            if not res:
                processing_flag = False

        if process_tabs:

            df_dict = cosd.extract_all_tabs_data(data_dir, file_name)

            for ds_id in df_dict.keys():

                df = df_dict[ds_id]

                df["TIMESTAMP"] = datetime.now()

                if archive_dir:
                    archive_csv(archive_dir, file_name.split(".")[0], ds_id, df)

                #Apply blacklist
                if "stage_by_cancer_group_in_" in ds_id:
                    continue

                if debug:
                    print("\t"+ds_id)

                description = f"Table containing {ds_id} data from the COSD HTML files. Contact: {sf.get_user(ctx)}"
                
                res = sf.upload_df(
                    ctx,
                    df, 
                    table_name=ds_id,
                    database="data_lake__ncl",
                    schema="cancer__cosd_html",
                    replace=False,
                    table_columns=list(df_dict[ds_id].columns),
                    table_description=description,
                    debug=False
                )
                
                #Set flag to say not all sheets were uploaded successfully. 
                # This prevents the file getting archived if it needs to be re-run
                if not res:
                    processing_flag = False

        if processing_flag:
            if archive_dir:
                archive_html(archive_dir, data_dir, file_name)

def get_onedrive_dir():
    #Get username
    od_dir = f"C:/Users/{os.getlogin()}/{getenv("NHS_ONEDRIVE_DIR")}/"

    if not(os.path.exists(od_dir)):
        raise Exception("OneDrive cannot be found on your machine:\n\t" + od_dir)
    
    work_dir = od_dir + getenv("WORK_DIR") + "/"
    
    if not(os.path.exists(work_dir)):
        raise Exception("The OneDrive work directory cannot be found on your machine:\n\t" + work_dir + "\nPlease refer to the README file to set up the OneDrive shortcut in your file explorer.")

    for (root,dirs,files) in os.walk(work_dir):
        if root.split("\\")[-1] == getenv("DATA_SOURCE_DIR"):
            return root.replace("\\", "/") + "/"

base_dir = get_onedrive_dir()
data_dir = base_dir + "unprocessed/"
archive_dir = base_dir + "processed/"

files = get_files(data_dir, file_ext="html")
process_files(files, data_dir, archive_dir=archive_dir)