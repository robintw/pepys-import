import os
from abc import ABC, abstractmethod

from tqdm import tqdm


class Importer(ABC):
    def __init__(self, name, validation_level, short_name):
        super().__init__()
        self.name = name
        self.validation_level = validation_level
        self.short_name = short_name
        self.errors = None
        self.error_type = None

    def __str__(self):
        return self.name

    @abstractmethod
    def can_load_this_type(self, suffix) -> bool:
        """Whether this importer can load files with the specified suffix.

        :param suffix: File suffix (e.g. ".doc")
        :type suffix: String
        :return: Yes/No
        :rtype: bool
        """

    @abstractmethod
    def can_load_this_filename(self, filename) -> bool:
        """Whether this importer can load a file with the provided filename

        :param filename: Full filename
        :type filename: String
        :return: Yes/No
        :rtype: bool
        """

    @abstractmethod
    def can_load_this_header(self, header) -> bool:
        """Whether this importer can load a file with this first line of text

        :param header: The initial line of text
        :type header: String
        :return: Yes/No
        :rtype: bool
        """

    @abstractmethod
    def can_load_this_file(self, file_contents) -> bool:
        """Whether this parser can handle this whole file

        :param file_contents: Whole file contents
        :type file_contents: String
        :return: Yes/No
        :rtype: bool
        """

    def load_this_file(self, data_store, path, file_object, datafile, change_id):
        """Handles the loading of this data file

        Performs the common operations that must be performed before the
        load_this_file method is called, then performs the load
        """
        basename = os.path.basename(path)
        print(f"{self.short_name} working on {basename}")
        self.errors = list()
        self.error_type = f"{self.short_name} - Parsing error on {basename}"
        datafile.measurements[self.short_name] = dict()

        # perform load
        self._load_this_file(data_store, path, file_object, datafile, change_id)

    def _load_this_file(self, data_store, path, file_object, datafile, change_id):
        """Process this data-file

        :param data_store: The data_store
        :type data_store: DataStore
        :param path: File path
        :type path: String
        :param file_object: HighlightedFile object, representing file contents and allowing
        extraction of lines and tokens, and recording of tokens
        :type file_object: HighlightedFile
        :param datafile: DataFile object
        :type datafile: DataFile
        :param change_id: ID of the :class:`Change` object
        :type change_id: Integer or UUID
        """
        for line_number, line in enumerate(tqdm(file_object.lines()), 1):
            self._load_this_line(data_store, line_number, line, datafile, change_id)

    def _load_this_line(self, data_store, line_number, line, datafile, change_id):
        """Process a line from this data-file

        :param data_store: The data_store
        :type data_store: DataStore
        :param line_number: The number of the line in the file (starting from 1)
        :type line_number: Integer
        :param line: A Line object, representing a line from a file and allowing
        extraction of tokens, and recording of tokens
        :type line: Line
        :param datafile: DataFile object
        :type datafile: DataFile
        :param change_id: ID of the :class:`Change` object
        :type change_id: Integer or UUID
        """
        raise NotImplementedError
