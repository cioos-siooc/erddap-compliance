from types import TracebackType
import requests
from compliance_checker.runner import ComplianceChecker, CheckSuite
from erddapy import ERDDAP
from dateutil import parser
import pandas as pd
from datetime import timedelta
import json
import argparse
import traceback
from pathlib import Path
import os
import urllib
from urllib.parse import urlparse

def main(prog_args):
    # print(prog_args)
    erddap_hostname = urlparse(prog_args.erddap_server).netloc

    epy = ERDDAP(
        server=prog_args.erddap_server,
        protocol="tabledap",
    )
    epy.response = "json"
    epy.dataset_id = "allDatasets"
    epy.constraints={'cdm_data_type!=':"Other","tabledap!=":""}

    df = epy.to_pandas()
    df = df[df["datasetID"] != "allDatasets"]
    
    if prog_args.dataset_id:
        df = df[df["datasetID"].str.contains(prog_args.dataset_id)]

    if prog_args.exclude_regex:
        # print("Filtering dataset list via RegEx...")
        filtered_list = df["datasetID"].str.contains(prog_args.exclude)
        df = df[~filtered_list]
    else:
        # print("Filtering explicit list of datasets...")
        filtered_list = df["datasetID"].isin(prog_args.exclude.split(","))
        df = df[~filtered_list]

    # print("Filtered List: %s" % (filtered_list.to_list()))

    list_of_datasets = df.to_dict("records")

    print("List of datasets to check for compliance:")
    for dataset_id in df["datasetID"].to_list():
        print(f" - {dataset_id}")

    # Ensure path to output directory exists, if not create it
    prog_args.output_dir=os.path.join(prog_args.output_dir,erddap_hostname)
    if not Path(prog_args.output_dir).exists():
        Path(prog_args.output_dir).mkdir(parents=True, exist_ok=True)

    for dataset in list_of_datasets:
        print(dataset["datasetID"], dataset["tabledap"])
        try:
            run_checker(dataset, prog_args, epy)
        except urllib.error.HTTPError as e:
            print("No data found")

        except Exception:
            print(f'ERROR:  Could not validate dataset: {dataset["datasetID"]}')
            traceback.print_exc()


def run_checker(dataset, prog_args, epy):
    # Load all available checker classes
    check_suite = CheckSuite()
    check_suite.load_all_available_checkers()

    if str(dataset["maxTime (UTC)"])=='nan':
        url=f'{prog_args.erddap_server}/tabledap/{dataset["datasetID"]}.csv?time&orderByMax("time")'
        print(url)
        res=pd.read_csv(url,skiprows=[1])
        max_time=res['time'].to_list().pop()
        last_hour_of_dataset = (parser.parse(max_time) - timedelta(hours=1))
        epy.constraints = {"time>=": last_hour_of_dataset.isoformat()}
    else:
        epy.constraints = {"time>": f"max(time)-{prog_args.time_offset}"}


    epy.response = "ncCF"  # Request netCDF file
    epy.dataset_id = dataset["datasetID"]

    # Set values for compliance checker run
    download_url = epy.get_download_url()
    print("Downloading",download_url)
    # If download_local flag is set, download the sample NetCDF file, otherwise
    # pass url to compliance checker
    download_path = fetch_dataset_sample(prog_args=prog_args, dataset_id=dataset["datasetID"], download_url=download_url)
    
    if not download_path:
        print("Error in dataset ",dataset["datasetID"])
        return None
    checker_names = prog_args.standards
    verbose = prog_args.verbose
    criteria = "normal"
    output_format = prog_args.format

    # If text format is selected make file extension "txt" instead
    file_ext = "txt" if (prog_args.format == "text") else prog_args.format

    output_filename = os.path.join(prog_args.output_dir,dataset["datasetID"]+'.'+file_ext)


    """
    Inputs to ComplianceChecker.run_checker

    path            Dataset location (url or file)
    checker_names   List of string names to run, should match keys of checkers dict (empty list means run all)
    verbose         Verbosity of the output (0, 1, 2)
    criteria        Determines failure (lenient, normal, strict)
    output_filename Path to the file for output
    output_format   Format of the output

    @returns                If the tests failed (based on the criteria)
    """
    
    return_value, errors = ComplianceChecker.run_checker(
        download_path,
        checker_names,
        verbose,
        criteria,
        output_filename=output_filename,
        output_format=output_format,
    )

    if return_value:
        print("Return Value: ", return_value)

    if errors:
        print("Errors: ", errors)

    # Open the JSON output and get the compliance scores
    if output_format == "json":
        with open(output_filename, "r") as fp:
            cc_data = json.load(fp)
            for standard in prog_args.standards:
                scored = cc_data[standard]["scored_points"]
                possible = cc_data[standard]["possible_points"]

                print(f"{standard}: CC Scored {scored} out of {possible} possible points")

def fetch_dataset_sample(prog_args, dataset_id, download_url):
    """
    Fetches a NetCDF file from the ERDDAP server, saves it locally to a work 
    directory and returns a path to the file.
    """

    response = requests.get(url=download_url)
    
    if response.status_code == 200:
        local_path = Path(prog_args.work, dataset_id + ".nc")

        if not Path(prog_args.work).exists():
            Path(prog_args.work).mkdir(parents=True, exist_ok=True)

        with open(local_path, "wb") as file:
            file.write(response.content)

        return local_path.as_posix()
    else:
        print(response.text)
        return None


def prep_args(prog_args):
    """
    Prepares submitted arguments for use by the rest of the script.
    """
    prog_args.standards = prog_args.standards.split(",")
    # prog_args.time_offset = int(prog_args.time_offset)

    return prog_args

if __name__ == "__main__":
    raw_args = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    raw_args.add_argument(
        "erddap_server",
        help="The URL of an ERDDAP instance e.g. https://www.example.com/erddap/",
    )

    raw_args.add_argument(
        "-s",
        "--standards",
        help='What Compliance Checker standards each dataset should be checked against.  Multiple standards may be specified as a CSV string. A full list of acceptable values may be gathered by running the command "compliance-checker --list-tests"',
        default="cf:1.6",
    )

    raw_args.add_argument(
        "-e",
        "--exclude",
        help="List of datasets to exclude from compliance checker",
        default="",
    )

    raw_args.add_argument(
        "--exclude_regex",
        help="Use regular expressions to filter list of datasets to exclude",
        action="store_true",
    )

    raw_args.add_argument(
        "-f",
        "--format",
        help="Set the output format [text,html,json,json_new]",
        default="html",
    )

    raw_args.add_argument(
        "-o",
        "--output_dir",
        help=f"Where reports should be written to",
        default="results",
    )

    raw_args.add_argument(
        "-t",
        "--time_offset",
        help="A python Timedelta string that specifies the time range of data to retreive from each dataset.  This is to reduce the size of netCDF files being queried from the ERDDAP server, since metadata compliance is what's being audited and not the actual data, we only need 1 or more records to get a valid netCDF file",
        default="1hour",
    )

    raw_args.add_argument(
        "--timeout",
        help="Number of seconds to wait for a response from the ERDDAP server when downloading a sample of a dataset locally",
        type=int,
        default=30,
    )

    raw_args.add_argument(
        "-v",
        "--verbose",
        help="Passes the desired verbosity flag to the compliance checker library. Acceptable Values: 0, 1, 2.  The higher the value, the more verbose the output.  Default: 0",
        action="store_true",
        default=False,
    )


    raw_args.add_argument(
        "--work",
        help="Specify the temporary working directory for downloaded sample files.",
        default="/tmp/cc_erddap",
    )

    raw_args.add_argument(
        "--dataset_id",
        help="Check single dataset",
    )

    prog_args = raw_args.parse_args()

    # do some pre-processing on the arguments to make them ready for the
    # script to interpret
    prog_args = prep_args(prog_args)

    main(prog_args)
