"""
Fields' analyzers
"""
import abc


class AbstractAnalyzer(metaclass=abc.ABCMeta):
    """Base class for UserDefined/EngineSpecific Analyzers"""
    settings = {}

    @property
    @abc.abstractmethod
    def tokenizer(self):
        """Returns Tokenizer object or None"""

    @property
    @abc.abstractmethod
    def filters(self):
        """Return ordered iterable with filter objects"""

class Analyzer(AbstractAnalyzer):
    name = ''

    def __init__(self, tokenizer, *filters, **settings):
        self.settings = settings
        self._tokenizer = tokenizer
        self._filters = filters

    @property
    def tokenizer(self):
        return self._tokenizer

    @property
    def filters(self):
        return self._filters