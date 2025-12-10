from datetime import datetime

def endTime_conv(time):
    endTime_obj = datetime.strptime(time, "%Y%m%dT%H%M%S.000Z")
    year = endTime_obj.year
    month = endTime_obj.month
    day = endTime_obj.day
    return year, month, day

def month(num):
    if num == 1:
        month = "Januar"
    elif num == 2:
        month = "Februar"
    elif num == 3:
        month = "Mars"
    elif num == 4:
        month = "April"
    elif num == 5:
        month = "Mai"
    elif num == 6:
        month = "Juni"
    elif num == 7:
        month = "Juli"
    elif num == 8:
        month = "August"
    elif num == 9:
        month = "September"
    elif num == 10:
        month = "Oktober"
    elif num == 11:
        month = "November"
    elif num == 12:
        month = "Desember"
    else:
        raise ValueError("Invalid month number")
    return month



