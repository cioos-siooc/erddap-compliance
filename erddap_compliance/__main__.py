import argparse
from erddap_compliance.cc_erddap import cc_erddap


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

    cc_erddap(prog_args)
