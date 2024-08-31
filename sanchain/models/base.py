from abc import ABC, abstractmethod


class AbstractBroadcastModel(ABC):
    """A model that can be broadcasted to other nodes."""

    @property
    def model_type(self):
        """The type of the model."""
        return self.__class__.__name__

    @abstractmethod
    def to_json(self):
        """Convert the model to a JSON serializable dictionary.
           Allowed data types: str, int, float, bool, None, dict, list
           Format:
            {
                'type': 'model_type',
                'key1': 'value1',
                'key2': 'value2',
                ...
            }
        """

    @classmethod
    @abstractmethod
    def from_json(self):
        """Create a model from a JSON serializable dictionary.
           Format:
            {
                'type': self.model_type,
                'key1': 'value1',
                'key2': 'value2',
                ...
            }
        """


class AbstractDatabaseModel(ABC):
    """A model that can be stored in the database."""

    @property
    @abstractmethod
    def db_columns(self):
        """The columns of the model in the database. Along with their types.
        Allowed types: 'TEXT', 'INTEGER', 'REAL', 'BLOB'
        Example:
            [
                ('column1_name', 'type1'),
                ('column2_name', 'type2'),
                ...
            ]
        """
        return []

    @abstractmethod
    def to_db_row(self):
        """Convert the model to a tuple that will be written to a database.
          The order of the values should match the order of the columns in db_columns.
          Allowed data types: bytes, str, int, float, bool, None
          Format:
            (
                'value1',
                'value2',
                ...
            )
        """

    @classmethod
    @abstractmethod
    def from_db_row(cls, row):
        """Create a model from a tuple retrieved from a database."""
        pass
