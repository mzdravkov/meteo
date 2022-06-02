import asyncio
from datetime import date

import aiohttp
import requests
import pandas as pd

from . import db
from .models import MonthlyMeasurements

HISTORICAL_DATA_START_YEAR = 2000

LOCATION_COLUMN_INDEX = 1

AVERAGE_TEMP_URL = "https://www.stringmeteo.com/synop/temp_month.php?ord=num&dst=1&dend=31&pr=1&year={}&month={}"
MONTH_VALUE_COLUMN_NAME = "Мес."

AVERAGE_TEMP_EXTREMUMS_URL = "https://www.stringmeteo.com/synop/maxmin_month.php?ord=num&dst=1&dend=31&pr=1&year={}&month={}"
AVERAGE_TEMP_EXTREMUMS_VAR_COLUMN_INDEX = 2

SUNSHINE_HOURS_URL = "https://www.stringmeteo.com/synop/sunsh_month.php?ord=num&dst=1&dend=31&pr=1&year={}&month={}"

RAINFALL_URL = "https://www.stringmeteo.com/synop/prec_month.php?ord=num&pr=1&year={}&month={}"

SNOW_COVER_URL = "https://www.stringmeteo.com/synop/snow_month.php?ord=num&pr=1&year={}&month={}"


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


async def __async_get(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()


async def get_average_temp(location, year, month):
    """
    return average monthly temperature
    """
    url = AVERAGE_TEMP_URL.format(year, month)
    df = pd.read_html(await __async_get(url))[0]

    row_index = __get_location_row(df, location)

    header_row = __get_header_row(df, location)

    column_index = header_row.index[header_row == MONTH_VALUE_COLUMN_NAME][0]

    return df[column_index][row_index]


async def get_average_temp_extremums(location, year, month):
    """
    returns (average min temp, average max temp)
    """
    url = AVERAGE_TEMP_EXTREMUMS_URL.format(year, month)
    df = pd.read_html(await __async_get(url))[0]

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


async def get_sunshine_hours(location, year, month):
    """
    returns total sunshine hours for the month
    """
    url = SUNSHINE_HOURS_URL.format(year, month)
    df = pd.read_html(await __async_get(url))[0]

    row_index = __get_location_row(df, location)

    header_row = __get_header_row(df, location)

    column_index = header_row.index[header_row == MONTH_VALUE_COLUMN_NAME][0]

    return df[column_index][row_index]


async def get_rain_data(location, year, month):
    """
    returns (days with rain, total rainfall in mm.)
    """
    url = RAINFALL_URL.format(year, month)
    df = pd.read_html(await __async_get(url))[0]

    row_index = __get_location_row(df, location)

    header_row = __get_header_row(df, location)

    rainfall_column_index = header_row.index[header_row == 'Сум.'][0]
    rain_days_column_index = header_row.index[header_row == 'Бр.'][0]

    return float(df[rain_days_column_index][row_index]), float(df[rainfall_column_index][row_index])


async def get_snow_data(location, year, month):
    """
    returns (days with snow, average snow cover in cm)
    """
    url = SNOW_COVER_URL.format(year, month)
    df = pd.read_html(await __async_get(url))[0]

    row_index = __get_location_row(df, location)

    header_row = __get_header_row(df, location)

    avg_snow_cover_column_index = header_row.index[header_row == 'Ср.2'][0]
    snow_days_column_index = header_row.index[header_row == 'Бр.1'][0]

    return float(df[snow_days_column_index][row_index]), float(df[avg_snow_cover_column_index][row_index])


async def __load_monthly_measurements(location, year, month, sem):
    # semaphore limits num of simultaneous downloads
    async with sem:
        measurements = await asyncio.gather(
            get_average_temp(location.name, year, month),
            get_average_temp_extremums(location.name, year, month),
            get_sunshine_hours(location.name, year, month),
            get_rain_data(location.name, year, month),
            get_snow_data(location.name, year, month),
        )

        avg_temp = measurements[0]
        avg_min_temp, avg_max_temp = measurements[1]
        sunshine_hours = measurements[2]
        rainy_days, rainfall = measurements[3]
        snowy_days, avg_snow_cover = measurements[4]

        return MonthlyMeasurements(
                location=location.id,
                year=year,
                month=month,
                average_temp=avg_temp,
                average_min_temp=avg_min_temp,
                average_max_temp=avg_max_temp,
                sunshine_hours=sunshine_hours,
                rainfall=rainfall,
                rainy_days=rainy_days,
                average_snow_coverage=avg_snow_cover)


async def load_historical_data(location, overwrite_existing):
    existing_months = {(m.year, m.month) for m in MonthlyMeasurements.query.filter_by(location=location.id)}

    measurements = []

    awaitables = []

    sem = asyncio.Semaphore(6)

    current_year = date.today().year
    for year in range(HISTORICAL_DATA_START_YEAR, current_year + 1):
        max_month = date.today().month if year == current_year else 12
        for month in range(1, max_month + 1):
            if (year, month) in existing_months:
                if overwrite_existing:
                    existing = MonthlyMeasurements.query.filter_by(
                            location=location.id,
                            year=year,
                            month=month).first()
                    db.session.delete(existing)
                    db.session.commit()
                else:
                    continue
            awaitables.append(__load_monthly_measurements(location, year, month, sem))

    for coroutine in asyncio.as_completed(awaitables):
        measurement = await coroutine
        db.session.add(measurement)
    db.session.commit()

