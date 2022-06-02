import requests
import pandas as pd

LOCATION_COLUMN_INDEX = 1

AVERAGE_TEMP_URL = "https://www.stringmeteo.com/synop/temp_month.php?ord=num&dst=1&dend=31&pr=1&year={}&month={}"
MONTH_VALUE_COLUMN_NAME = "Мес."

AVERAGE_TEMP_EXTREMUMS_URL = "https://www.stringmeteo.com/synop/maxmin_month.php?ord=num&dst=1&dend=31&pr=1&year={}&month={}"
AVERAGE_TEMP_EXTREMUMS_VAR_COLUMN_INDEX = 2

SUNSHINE_HOURS_URL = "https://www.stringmeteo.com/synop/sunsh_month.php?ord=num&dst=1&dend=31&pr=1&year={}&month={}"


def __get_location_row(df, location):
    rows_for_location = df.index[df[LOCATION_COLUMN_INDEX] == location]
    if len(rows_for_location) != 1:
        raise Exception("More than one row matches location=" + location)

    return rows_for_location[0]


def __get_header_row(df, location):
    header_rows_index = df.index[df[0] == 'No.']
    if len(header_rows_index) == 0:
        raise Exception("Cannot find header any header rows for location=" + location)
    header_row_index = header_rows_index[0]
    return df.loc[header_row_index, :]


def get_average_temp(location, year, month):
    url = AVERAGE_TEMP_URL.format(year, month)
    df = pd.read_html(url)[0]

    row_index = __get_location_row(df, location)

    header_row = __get_header_row(df, location)

    column_index = header_row.index[header_row == MONTH_VALUE_COLUMN_NAME][0]

    return df[column_index][row_index]


def get_average_temp_extremums(location, year, month):
    url = AVERAGE_TEMP_EXTREMUMS_URL.format(year, month)
    df = pd.read_html(url)[0]

    location_df = df.loc[df.index[df[LOCATION_COLUMN_INDEX] == location]]

    max_index = location_df.index[location_df[AVERAGE_TEMP_EXTREMUMS_VAR_COLUMN_INDEX] == 'Макс.']

    if len(max_index) == 0:
        raise Exception("Cannot find average max temp. for location=" + location)

    min_index = location_df.index[location_df[AVERAGE_TEMP_EXTREMUMS_VAR_COLUMN_INDEX] == 'Мин.']

    if len(min_index) == 0:
        raise Exception("Cannot find average min temp. for location=" + location)

    max_row = max_index[0]
    min_row = min_index[0]

    header_row = __get_header_row(df, location)

    column_index = header_row.index[header_row == 'Мес. ср.'][0]

    return float(location_df[column_index][min_row]), float(location_df[column_index][max_row])


def get_sunshine_hours(location, year, month):
    url = SUNSHINE_HOURS_URL.format(year, month)
    df = pd.read_html(url)[0]

    row_index = __get_location_row(df, location)

    header_row = __get_header_row(df, location)

    column_index = header_row.index[header_row == MONTH_VALUE_COLUMN_NAME][0]

    return df[column_index][row_index]



print('avg temp', get_average_temp('София', 2022, 5))
print('avg temp extremums', get_average_temp_extremums('София', 2022, 5))
print('sunshine hours', get_sunshine_hours('София', 2022, 5))
