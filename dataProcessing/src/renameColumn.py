import numpy as np
import pandas as pd
from getInfo import log, get_info

name_mapping = {}


def column_temperature(df):
    keywords = ["temperature", "amb", "ambient", "°C", "temp"]
    temperature_cols = [
        col for col in df.columns if any(keyword in col.lower() for keyword in keywords)
    ]

    if len(temperature_cols) == 1:
        df.rename(columns={temperature_cols[0]: "Temperature"}, inplace=True)
    elif len(temperature_cols) == 0:
        df["Temperature"] = np.nan
    else:
        # Check for columns with "ambient" in their name
        amb_keywords = ["amb", "ambient"]
        ambient = [
            col
            for col in temperature_cols
            if any(amb_keyword in col.lower() for amb_keyword in amb_keywords)
        ]

        # If there's a column with "ambient", use that. Otherwise, use the first "temperature" column
        col_to_use = ambient[0] if ambient else temperature_cols[0]
        df.rename(columns={col_to_use: "Temperature"}, inplace=True)

        # Drop any other temperature columns to keep the dataframe clean
        cols_to_drop = [col for col in temperature_cols if col != col_to_use]
        df.drop(columns=cols_to_drop, inplace=True)

    return df


def column_wind(df):
    wind = [
        col for col in df.columns if "wind" in col.lower() or "speed" in col.lower()
    ]
    if wind:
        df.rename(columns={wind[0]: "Wind Speed"}, inplace=True)
    else:
        new_wind_col = pd.Series(np.nan, index=df.index, name="Wind Speed")
        df = pd.concat([df, new_wind_col], axis=1)
    return df


def column_voltage(df):
    voltage = [col for col in df.columns if "voltage" in col.lower()]
    if len(voltage) > 1:
        col_to_use = min(voltage, key=lambda col: df[col].isna().sum())
        df.rename(columns={col_to_use: "Meter Voltage"}, inplace=True)
        cols_to_drop = [col for col in voltage if col != col_to_use]
        df.drop(columns=cols_to_drop, inplace=True)
    elif voltage:
        df.rename(columns={voltage[0]: "Meter Voltage"}, inplace=True)
    else:
        df["Meter Voltage"] = np.nan

    return df


def find_keywords(column, keywords_list):
    for keywords in keywords_list:
        if all(keyword.lower() in column.lower() for keyword in keywords):
            return True
    return False


def column_others(df):
    keyword_mapping = {
        "Timestamp": [["timestamp"],["15m"]],
        "POA Irradiance": [["poa"]],
        "Meter Power": [["meter", "power"], ["electric", "power"]],
        # "Meter Power": ["meter", "power"],
    }

    rename_mapping = {}
    for new_name, keywords_list in keyword_mapping.items():
        found = False
        for col in df.columns:
            found = find_keywords(col, keywords_list)
            if found:
                rename_mapping[col] = new_name
                break
        if not found:
            df[new_name] = np.nan

    df.rename(columns=rename_mapping, inplace=True)

    return df


def column_inverter(df):
    known_columns = {
        "Timestamp",
        "POA Irradiance",
        "Meter Voltage",
        "Meter Power",
        "Temperature",
        "Wind Speed",
    }
    inverter_index = 1

    for col in df.columns:
        if col not in known_columns:
            new_name = "Inverter_" + str(inverter_index)
            df.rename(columns={col: new_name}, inplace=True)
            # Used for renaming cols to their original names in the end of the processing
            name_mapping[new_name] = col
            inverter_index += 1

    return df


def column_reorder(df):
    inverter_columns = sorted(
        (col for col in df.columns if "Inverter" in col),
        key=lambda s: int(s.split("_")[1]),
    )
    columns_order = [
        "Timestamp",
        "POA Irradiance",
        "Temperature",
        "Wind Speed",
        "Meter Voltage",
        "Meter Power",
    ] + inverter_columns
    df = df[columns_order]

    return df


def rename(df):
    return (
        df.pipe(column_others)
        .pipe(column_temperature)
        .pipe(column_wind)
        .pipe(column_voltage)
        .pipe(column_inverter)
        .pipe(column_reorder)
    )
