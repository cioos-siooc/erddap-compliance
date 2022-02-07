from compliance_checker.runner import ComplianceChecker, CheckSuite
from erddapy import ERDDAP
from datetime import datetime, timedelta
from numpy import double
import pandas as pd
import dateutil
import json
import argparse
import traceback
from pathlib import Path


def main(prog_args):
    # print(prog_args)

    epy = ERDDAP(
        server=prog_args.erddap_server,
        protocol="tabledap",
    )
    epy.response = "json"
    epy.dataset_id = "allDatasets"
    epy.variables = ["datasetID", "tabledap", "minTime", "maxTime"]

    df = epy.to_pandas()
    df = df[df["datasetID"] != "allDatasets"]

    if not prog_args.exclude_regex:
        # print("Filtering explicit list of datasets...")
        filtered_list = df["datasetID"].isin(prog_args.exclude.split(","))
        df = df[~filtered_list]
    else:
        # print("Filtering dataset list via RegEx...")
        filtered_list = df["datasetID"].str.contains(prog_args.exclude)
        df = df[~filtered_list]

    # print("Filtered List: %s" % (filtered_list.to_list()))

    list_of_datasets = df.to_dict("records")

    print("List of datasets to check for compliance:")
    for ds_name in df["datasetID"].to_list():
        print(" - %s" % (ds_name))

    # Ensure path to output directory exists, if not create it
    if not Path(prog_args.output_dir).exists():
        Path(prog_args.output_dir).mkdir(parents=True, exist_ok=True)

    for dataset in list_of_datasets:
        print(dataset["datasetID"], dataset["tabledap"])
        try:
            run_checker(dataset, prog_args, epy)
        except Exception as ex:
            print("ERROR:  Could not validate dataset: %s" % (dataset["datasetID"]))
            traceback.print_exc()


def run_checker(dataset, prog_args, epy):
    # Load all available checker classes
    check_suite = CheckSuite()
    check_suite.load_all_available_checkers()

    offset = pd.Timedelta(prog_args.time_offset).to_pytimedelta()

    dataset_variables = get_variables(dataset["datasetID"], epy)
    
    try:
        time_check = dateutil.parser.isoparse(dataset["minTime (UTC)"]) + offset
        epy.constraints = {"time<=": time_check.isoformat()}

    except TypeError as ex_type:
        time_check = dateutil.parser.isoparse(dataset["maxTime (UTC)"]) - offset
        epy.constraints = {"time>=": time_check.isoformat()}

    except Exception as ex_base:
        epy.constraints = {"time>": "max(time)-{}".format(prog_args.time_offset)}


    epy.response = "ncCF"  # Request netCDF file
    epy.variables = dataset_variables
    epy.dataset_id = dataset["datasetID"]

    # Set values for compliance checker run
    path = epy.get_download_url()
    checker_names = prog_args.standards
    verbose = prog_args.verbose
    criteria = "normal"
    output_format = prog_args.format

    if prog_args.output_dir != None:
        # If text format is selected make file extension "txt" instead
        file_ext = "txt" if (prog_args.format == "text") else prog_args.format

        output_filename = "%s/%s.%s" % (
            prog_args.output_dir,
            dataset["datasetID"],
            file_ext,
        )

    else:
        # this is the default value the compliance checker assumes when there
        # is no file output and will dump result to stdout
        output_filename = "-"

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
        path,
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

                print(
                    "{}: CC Scored {} out of {} possible points".format(
                        standard, scored, possible
                    )
                )


def prep_args(prog_args):
    """
    Prepares submitted arguments for use by the rest of the script.
    """
    prog_args.standards = prog_args.standards.split(",")
    # prog_args.time_offset = int(prog_args.time_offset)

    return prog_args


def get_variables(dataset_id, epy):
    """
    Extract and return variable names as a list from a specified ERDDAP dataset.
    """
    metadata_url = epy.get_download_url(
        dataset_id="%s/index" % (dataset_id), response="csv", protocol="info"
    )

    metadata = pd.read_csv(filepath_or_buffer=metadata_url)
    var_names = metadata[metadata["Row Type"] == "variable"]["Variable Name"].to_list()

    return var_names


if __name__ == "__main__":
    raw_args = argparse.ArgumentParser()
    raw_args.add_argument(
        "erddap_server",
        help="The URL of an ERDDAP instance e.g. https://www.server.com/erddap/",
        action="store",
    )

    raw_args.add_argument(
        "-s",
        "--standards",
        help='What Compliance Checker standards each dataset should be checked against.  Multiple standards may be specified as a CSV string. A full list of acceptable values may be gathered by running the command "compliance-checker --list-tests".  Default: cf:1.6',
        default="cf:1.6",
        action="store",
    )

    raw_args.add_argument(
        "-e",
        "--exclude",
        help="List of datasets to exclude from compliance checker, default: allDatasets",
        default="",
        action="store",
    )

    raw_args.add_argument(
        "--exclude_regex",
        help="Use regular expressions to filter list of datasets to exclude",
        action="store_true",
    )

    raw_args.add_argument(
        "-f",
        "--format",
        help="Set the output format [text,html,json,json_new], default: text",
        default="text",
        action="store",
    )

    raw_args.add_argument(
        "-o",
        "--output_dir",
        help="Where reports should be written to.  If not specified output will be printed to screen.",
        default=None,
        action="store",
    )

    raw_args.add_argument(
        "-t",
        "--time_offset",
        help="How many seconds from maxTime (UTC) should a dataset be queried.  This is to reduce the size of netCDF files being queried from the ERDDAP server, since metadata compliance is what's being audited and not the actual data, we only need 1 or more records to get a valid netCDF file.  Default: 86400 (1 day)",
        action="store",
        default="1day",
    )

    raw_args.add_argument(
        "-v",
        "--verbose",
        help="Passes the desired verbosity flag to the compliance checker library. Acceptable Values: 0, 1, 2.  The higher the value, the more verbose the output.  Default: 0",
        action="store",
        default=0,
    )

    prog_args = raw_args.parse_args()

    # do some pre-processing on the arguments to make them ready for the
    # script to interpret
    prog_args = prep_args(prog_args)

    main(prog_args)
