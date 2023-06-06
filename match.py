import scipy.io as sio
import numpy as np
import csv

"""
Head width - x1 ~ 1.0
Head height - x2 ~ 1.0
Head depth - x3 ~ 1.0 - [40]?
Height - x14 ~ 0.5
Seated height - x15 ~ 0.5
Head circumference - x16 ~ 1.0
Shoulder circumference - x17 ~ 1.0

Ear length (longest line) - d5 ~ 1.0
Ear width (longest line) - d6 ~ 1.0
Ear inside length - d1, d2, d4 ~ 1.0
Ear inside width - d3 ~ 1.0

weight in Kg - WeightKilograms ~ 0.5

The command used for downloading HRTFs from the HTTPs database:
(new-object System.Net.WebClient).DownloadFile('https://sofacoustics.org/data/database/ari/hrtf_nhXXX.sofa','(path to destination folder)\XXXX.sofa')
where the 'XXX' and 'XXXX' denote the ID of the HRTF. The output of this file is the 4 digit ID.
The HRTFs are all prefixed with the number 3. The 3-digit  HRTF id is
the output of this file without the prefixed number 3.
The command mentioned before is ran in Windows PowerShell
"""

def read_measurements(file_path):
    measurements = [0] * 12
    with open(file_path, 'r') as input:
        rows = csv.reader(input)
        next(rows)
        for i, row in enumerate(rows):
            measurements[i] = float(row[2])
    return measurements


def filter_nan(good, wrong):
    new = [0] * 60
    for i in range(60):
        if np.isnan(good[i]):
            new[i] = wrong[i]
        else:
            new[i] = good[i]
    return new


"""
input: measurement in cm, array of length 60 with measurements of ARI subjects
output: array of length 60 with errors between measurement and all ARI subjects

error is absolute difference normalized under the maximum difference in the ARI
database for that measurement. This way of calculating the normalization factor
keeps the amount of possible variance for the specific measurement in account.
"""
def calculate_error(measurement, data, weight=1.0):
    if len(data) != 60:
        print("Input for function calculate_error is incorrect.")
        return None
    error = [0] * 60
    # Calculate normalization factor
    normalization = max(data) - min(data)
    # Calculate absolute difference between all datapoints
    for i, datapoint in enumerate(data):
        difference = abs(datapoint - measurement)
        # Normalize error
        error[i] = round(difference / normalization * weight, 3)
    return error


def add_errors(total, new):
    return [sum(x) for x in zip(total, new)]


def get_id(data, index):
    return data['id'][index][0]


if __name__ == '__main__':
    # Load the ARI anthropometric data in.
    # dict fields in data.mat: '__header__', '__version__', '__globals__', 'A', 'CreateDate', 'D', 'MeasurementDate', 'WeightKilograms', 'X', 'age', 'id', 'sex', 'theta'
    data = sio.loadmat('./data.mat')

    # Load subject anthropometric measurements in.
    measurements = read_measurements('./measurements/XXX_measurements.csv')

    # For every measurement, calculate the error for all 60 subjects in ARI data.
    head_widths = [subject[0] for subject in data['X']]
    head_heights = [subject[1] for subject in data['X']]
    head_depths = [subject[2] for subject in data['X']]

    heights = [subject[13] for subject in data['X']]
    seated_heights = [subject[14] for subject in data['X']]
    head_circumferences = [subject[15] for subject in data['X']]
    shoulder_circumferences = [subject[16] for subject in data['X']]

    ear_lengths = [subject[4] for subject in data['D']]

    ear_widths = filter_nan([subject[5] for subject in data['D']], [subject[18] for subject in data['D']])
    d1 = filter_nan([subject[0] for subject in data['D']], [subject[16] for subject in data['D']])
    d2 = filter_nan([subject[1] for subject in data['D']], [subject[17] for subject in data['D']])
    d4 = filter_nan([subject[3] for subject in data['D']], [np.nan] * 60)
    ear_inside_lengths = [sum(x) for x in zip(d1, d2, d4)]
    ear_inside_widths = [subject[2] for subject in data['D']]

    weights = [subject[0] for subject in data['WeightKilograms']]

    inputs = [head_widths, head_heights, head_depths, heights, seated_heights, head_circumferences, shoulder_circumferences, ear_lengths, ear_widths, ear_inside_lengths, ear_inside_widths, weights]

    # Add the error to the total of that subject.
    errors = [0] * 60
    for i, input in enumerate(inputs):
        if i == 3 or i == 4 or i == 11:
            error = calculate_error(measurements[i], input, weight=0.5)
        else:
            error = calculate_error(measurements[i], input)
        errors = add_errors(errors, error)

    # Get ID's for best, median, and worst matches.
    # Remove bad datapoints from dataset, make sure list is in descending order.
    ignore_indices = [42]

    for i in ignore_indices:
        errors.pop(i)

    errors_copy = errors.copy()
    errors_copy.sort()
    best_index = errors.index(min(errors))
    median_index = errors.index(errors_copy[len(errors) // 2])
    worst_index = errors.index(max(errors))

    best = get_id(data, best_index)
    median = get_id(data, median_index)
    worst = get_id(data, worst_index)
    print(errors)
    print(min(errors), errors_copy[len(errors) // 2], max(errors))
    print(best, median, worst)
