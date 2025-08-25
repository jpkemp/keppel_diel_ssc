from abc import ABC, abstractmethod

class BaseLocation(ABC):
    @classmethod
    @abstractmethod
    def temperature_data(cls):
        return NotImplemented

    @property
    @abstractmethod
    def location():
        return NotImplemented

    @property
    @abstractmethod
    def timezone(cls):
        return NotImplemented

    @classmethod
    @abstractmethod
    def tide_data(cls, year):
        return NotImplemented

    @classmethod
    @abstractmethod
    def harmonic_constants(cls):
        return NotImplemented

    @classmethod
    def localise_time_series(cls, srs, tz):
        if srs.dt.tz is None:
            result = srs.dt.tz_localize(tz)
        else:
            result = srs.dt.tz_convert(tz)

        return result
