from abc import abstractmethod
from enum import StrEnum
from .property_decorators import property_is_valid_time, property_not_nullable


class IntervalItem(object):
    class Frequency(StrEnum):
        Hourly = "Hourly"
        Daily = "Daily"
        Weekly = "Weekly"
        Monthly = "Monthly"

    class Interval_Type(StrEnum):
        Minutes = "minutes"
        Hours = "hours"
        WeekDay = "weekDay"
        MonthDay = "monthDay"
        
    class OccurrenceInMonth(StrEnum):
        First = "First"
        Second = "Second"
        Third = "Third"
        Fourth = "Fourth"
        Fifth = "Fifth"
        LastDay = "LastDay"

    class Day(StrEnum):
        Sunday = "Sunday"
        Monday = "Monday"
        Tuesday = "Tuesday"
        Wednesday = "Wednesday"
        Thursday = "Thursday"
        Friday = "Friday"
        Saturday = "Saturday"
        LastDay = "LastDay"
    
    
class BaseInterval:
    def __init__(self, start_time, interval_value):
        self.start_time = start_time

        # interval should be a tuple, if it is not, assign as a tuple with single value
        # this bypasses the setter and will not call validate_interval
        if isinstance(interval_value, tuple):
            self._interval = interval_value
        else:
            self._interval = (interval_value,)            

    def __repr__(self):
        return f"<{self.__class__.__name__} start={self.start_time} interval={self.interval}>"

    @property
    def _frequency(self):
        return self._frequency

    @property
    def start_time(self):
        return self._start_time

    @start_time.setter
    @property_is_valid_time
    @property_not_nullable
    def start_time(self, value):
        self._start_time = value
        
    @property
    def interval(self):
        return self._interval

    @interval.setter
    def interval(self, intervals):
        self.validate_interval(intervals)
        self._interval = intervals
    
    def clear_schedule(self):
        self._interval = None
        
    # must be implemented by each subclass
    @abstractmethod
    def validate_interval(self):
        assert(False)
        

class Ending_Interval(BaseInterval):

    def __init__(self, start_time, end_time, interval_value):
        self.end_time = end_time
        self.super(start_time, interval_value)
        
    def __repr__(self):
        return f"<{self.__class__.__name__} start={self.start_time} end={self.end_time} interval={self.interval}>"
            
    @property
    def end_time(self):
        return self._end_time

    @end_time.setter
    @property_is_valid_time
    def end_time(self, value):
        self._end_time = value


class HourlyInterval(Ending_Interval):
    @classmethod
    def __init__(self, start_time, end_time, interval_value):
        self._frequency = IntervalItem.Frequency.Hourly
        super.__init__(self, start_time, end_time, interval_value)
            
    HOUR_VALUE = 1
    MINUTE_VALUE = 60
    # requires exactly one of an hours or minutes attribute
    # can have any number of weekday attributes (TODO: what happens if there is none? is it valid to repeat a weekday?)
    def validate_interval(self):
        interval_values = self._interval
        count_hours = 0
        for interval in interval_values:
            # if an hourly interval is a string, then it is a weekDay interval
            if isinstance(interval, str) and not interval.isnumeric():
                if not hasattr(IntervalItem.Day, interval):
                    error = "Invalid weekDay interval {}".format(interval)
                    raise ValueError(error)
                interval_type = IntervalItem.Interval_Type.WeekDay
                interval_value = interval

            # if an hourly interval is a number, it is an hours or minutes interval
            elif isinstance(interval, int):
                if count_hours > 0:
                    raise ValueError("The schedule must have exactly one value for hours/minutes between runs.")
                count_hours = count_hours + 1
                if interval == self.HOUR_VALUE:
                    interval_type = IntervalItem.Interval_Type.Hours
                    interval_value = interval
                elif interval == self.MINUTE_VALUE:
                    interval_type = IntervalItem.Interval_Type.Minutes
                    interval_value = self.to_minutes(interval)
                else:
                    error = "Invalid interval {} not in {}".format(interval, list(self.HOUR_VALUE, self.MINUTE_VALUE))
                    raise ValueError(error)
            else: 
                error = "Invalid interval {} must be a Weekday or an integer.".format(interval)
                raise ValueError(error)
                
            self._interval_type_pairs.append((interval_type, str(interval_value)))



class DailyInterval(Ending_Interval):
    @classmethod
    def __init__(self, start_time, end_time, *interval_values):
        self._frequency = IntervalItem.Interval_Type.WeekDay
        super.__init__(self, start_time, end_time, *interval_values)

    def validate_interval(self):
        interval_values = self._interval
        VALID_INTERVALS = {0.25, 0.5, 1, 2, 4, 6, 8, 12, 24}
        # must have exactly one defined hours attribute. If the value is <24, it must also have an endtime
        # can have any number of weekday attributes. 
        # is it valid to repeat a weekday?
        
        for interval in interval_values:
            # if an hourly interval is a string, then it is a weekDay interval
            if isinstance(interval, str) and not interval.isnumeric() and not hasattr(IntervalItem.Day, interval):
                error = f"Invalid weekDay interval {interval}"
                raise ValueError(error)

            # if an hourly interval is a number, it is an hours or minutes interval
            if isinstance(interval, (int, float)) and float(interval) not in VALID_INTERVALS:
                error = f"Invalid interval {interval} not in {str(VALID_INTERVALS)}"
                raise ValueError(error)

        self._interval = interval_values

    def _interval_type_pairs(self):
        interval_type_pairs = []
        for interval in self.interval:
            # We use fractional hours for the two minute-based intervals.
            # Need to convert to minutes from hours here
            if interval in {0.25, 0.5}:
                calculated_interval = int(interval * 60)
                interval_type = IntervalItem.Interval_Type.Minutes

                interval_type_pairs.append((interval_type, str(calculated_interval)))
            else:
                # if the interval is a non-numeric string, it will always be a weekDay
                if isinstance(interval, str) and not interval.isnumeric():
                    interval_type = IntervalItem.Interval_Type.WeekDay

                    interval_type_pairs.append((interval_type, str(interval)))
                # otherwise the interval is hours
                else:
                    interval_type = IntervalItem.Interval_Type.Hours

                    interval_type_pairs.append((interval_type, str(interval)))

        return interval_type_pairs


class WeeklyInterval(BaseInterval):
    @classmethod
    def __init__(self, start_time, *interval_values):
        self._frequency = IntervalItem.Frequency.Weekly
        super.__init__(self, start_time, interval_values)

    def validate_interval(self):
        interval_values = self._interval
        # A weekly schedule must have 1 to 7 intervals
        # setting 0 intervals will wipe existing settings
        if interval_values is None:
            raise ValueError("Not including intervals will wipe existing values. If you intend to do this, use clear_schedule instead")

        if not all(hasattr(IntervalItem.Day, day) for day in interval_values):
            raise ValueError("Invalid week day defined " + str(interval_values))

        self._interval = interval_values

    def _interval_type_pairs(self):
        return [(IntervalItem.Interval_Type.WeekDay, day) for day in self.interval]


class MonthlyInterval(BaseInterval):
    @classmethod
    def __init__(self, start_time, interval_value):
        self._frequency = IntervalItem.Frequency.Monthly
        super.__init__(self, start_time, interval_value)
            
    def _day_of_month(day):
        # 2. day_of_month
        # Valid values are the whole numbers 1 to 31 or LastDay.
        # This could be a str or int, but there's only 32 possible values so just manually check the whole set
        VALID_DAY_OF_MONTH = list(range(32)).append(IntervalItem.LastDay)        
        if day not in VALID_DAY_OF_MONTH:
            raise ValueError("`{}` is not a valid day for a monthly schedule. ".format(day))
        return (day, ) 
            
        # If you use LastDay then only one instance of interval can be used in the schedule to specify the last day of the month.

    def _occurrence_of_weekday(occurrence, weekday):
        VALID_OCCURRENCE = list(IntervalItem.OccurrenceInMonth.__members__)
        VALID_WEEKDAY = list(IntervalItem.Day.__members__)
        if occurrence not in VALID_OCCURRENCE:
            raise ValueError("`{}` is not a valid schedule occurrence for a monthly schedule. ".format(occurrence))
        if weekday not in VALID_WEEKDAY:
            raise ValueError("`{}` is not a valid weekday for a monthly schedule. ".format(weekday))
        
        return (occurrence, weekday)

    def validate_interval(self):
        interval_values = self._interval
        error = "Invalid interval value for a monthly frequency: {}.".format(interval_values)
        # There are two possible formats for this: (day_of_month) or (occurrence_of_weekday, weekday)        
        if isinstance(interval_values, tuple):
            self._interval = MonthlyInterval._occurrence_of_weekday(interval_values)
        else:
            self._interval=  MonthlyInterval._day_of_month(interval_values)

        for interval_value in interval_values:
            if interval_value not in VALID_INTERVALS:
                error = f"Invalid monthly interval: {interval_value}"
                raise ValueError(error)


    def _interval_type_pairs(self):
        return [(IntervalItem.Interval_Type.MonthDay, self.interval)]
    