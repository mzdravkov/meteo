from collections import defaultdict
from .models import Location

def get_aggregated_measurements():
    locations = Location.query.all()
    measurements = defaultdict(lambda: {})
    for location in locations:
        for measurement in location.measurements:
            year = measurement.year
            month = measurement.month
            measurements[(year, month)][location] = measurement.as_dict()

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
