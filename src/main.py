import pandas as pd
from getInfo import log_messages, log
from readData import read_site
from renameColumn import rename
from normalizeData import normalize
from checkMissing import missing, check_and_autofill_inverter_and_voltage
from checkWorkorder import fetch_workorder, get_off_dates


file_path = "../data/2023-08-01-2023-08-31_Albertson Monthly.csv"
site_name = file_path.split("_")[-1].replace(" Monthly.csv", "")


def main():
    sitedata = read_site(file_path)
    site_df = sitedata.pipe(rename).pipe(normalize, site_name)
    # Check and autofill columns of 'irradiance,' 'temperature,' 'wind speed,' and 'meter power',
    # and return the missing dates where missing meter power cannot be auto-filled.
    missing_dates = missing(site_df)

    log("\nIV.\n")
    if missing_dates:
        matched_records = fetch_workorder(missing_dates, site_name)
        off_dates = get_off_dates(matched_records)
        if off_dates:
            site_df = check_and_autofill_inverter_and_voltage(site_df, off_dates).drop(
                columns="Date"
            )
        else:
            log(
                "No off dates found in the work order for days where missing meter power cannot be auto-filled."
            )
    else:
        log("No missing records to be fetched from the work order.")

    site_df.to_csv(f"../output/exportedData/{site_name}.csv", index=False)
    with open(f"../output/log/log_{site_name}.txt", "w") as file:
        for message in log_messages:
            file.write(message + "\n")


if __name__ == "__main__":
    main()
