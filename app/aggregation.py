from collections import defaultdict
from .models import Location

def get_aggregated_measurements():
    """
    Returns a dictionary where the keys are months and the value is a dict of aggregated measurements:
    month -> {var1: val1, ...}

    The month is encoded in YYYY-MM format.
    The list of variables in the value dict is:
        - avg_temp
        - avg_min_temp
        - avg_max_temp
        - sunshine
        - rainfall
        - rainy_days
        - avg_snow_cover

    The variables for each month are aggregated form all locations by using a weighted average formula.
    """
    locations = Location.query.all()
    # construct a dict: month->{location -> measurements}
    measurements = defaultdict(lambda: {})
    for location in locations:
        for measurement in location.measurements:
            year = measurement.year
            month = measurement.month
            measurements[(year, month)][location] = measurement.as_dict()

    # find the unadjusted weight of each location for every month
    # also find the total weight sum for every month
    month_to_location_weight = defaultdict(lambda: {})
    month_to_weight_sum = {}
    for year, month in measurements:
        weight_sum = 0
        for location in measurements[(year, month)]:
            # get the weight for the month or 0
            weight = next((w.value for w in location.weights if w.year == year), 0)
            month_to_location_weight[(year, month)][location] = weight
            weight_sum += weight
        month_to_weight_sum[(year, month)] = weight_sum

    # find the adjusted weighted sums for every month
    month_to_weighted_sums = defaultdict(lambda: defaultdict(lambda: 0))
    for year, month in measurements:
        for location in measurements[(year, month)]:
            location_weight = month_to_location_weight[(year, month)][location] 
            weight_sum = month_to_weight_sum[(year, month)]
            adj_weight = location_weight/weight_sum

            loc_measurements = measurements[(year, month)][location]
            adj_vals = {var: adj_weight*val for var, val in loc_measurements.items()}
            for var in adj_vals:
                adj_val = adj_vals[var]
                month_to_weighted_sums[(year, month)][var] += adj_val

    results = {}
    for year, month in measurements:
        weighted_sums = month_to_weighted_sums[(year, month)]
        key = "{}-{}".format(year, str(month).rjust(2, '0'))
        results[key] = weighted_sums

    return results
