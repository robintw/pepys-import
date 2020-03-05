import json
import os
import shutil

from datetime import datetime

from pepys_import.core.store.data_store import DataStore
from pepys_import.core.store.table_summary import TableSummary, TableSummarySet


class FileProcessor:
    def __init__(self, filename=None):
        self.importers = []
        if filename is None:
            self.filename = ":memory:"
        else:
            self.filename = filename
        self.output_path = None

    def process(
        self, path: str, data_store: DataStore = None, descend_tree: bool = True
    ):
        """Process the data in the given path

        :param path: File/Folder path
        :type path: String
        :param data_store: Database
        :type data_store: DataStore
        :param descend_tree: Whether to recursively descend through the folder tree
        :type descend_tree: bool
        """

        processed_ctr = 0

        # get the data_store
        if data_store is None:
            data_store = DataStore("", "", "", 0, self.filename, db_type="sqlite")
            data_store.initialise()

        # check given path is a file
        if os.path.isfile(path):
            with data_store.session_scope():
                states_sum = TableSummary(
                    data_store.session, data_store.db_classes.State
                )
                platforms_sum = TableSummary(
                    data_store.session, data_store.db_classes.Platform
                )
                first_table_summary_set = TableSummarySet([states_sum, platforms_sum])
                print(first_table_summary_set.report("==Before=="))

                filename = os.path.abspath(path)
                current_path = os.path.dirname(path)
                processed_ctr = self.process_file(
                    filename, current_path, data_store, processed_ctr
                )
                states_sum = TableSummary(
                    data_store.session, data_store.db_classes.State
                )
                platforms_sum = TableSummary(
                    data_store.session, data_store.db_classes.Platform
                )
                second_table_summary_set = TableSummarySet([states_sum, platforms_sum])
                print(second_table_summary_set.report("==After=="))
            print(f"Files got processed: {processed_ctr} times")
            return

        # check folder exists
        if not os.path.isdir(path):
            raise FileNotFoundError(f"Folder not found in the given path: {path}")

        # capture path in absolute form
        abs_path = os.path.abspath(path)
        # create output folder if not exists
        self.output_path = os.path.join(abs_path, "output")
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

        # decide whether to descend tree, or just work on this folder
        with data_store.session_scope():

            states_sum = TableSummary(data_store.session, data_store.db_classes.State)
            platforms_sum = TableSummary(
                data_store.session, data_store.db_classes.Platform
            )
            first_table_summary_set = TableSummarySet([states_sum, platforms_sum])
            print(first_table_summary_set.report("==Before=="))

            if descend_tree:
                # loop through this folder and children
                for current_path, folders, files in os.walk(abs_path):
                    for file in files:
                        processed_ctr = self.process_file(
                            file, current_path, data_store, processed_ctr
                        )
            else:
                # loop through this path
                for file in os.scandir(abs_path):
                    if file.is_file():
                        current_path = os.path.join(abs_path, file)
                        processed_ctr = self.process_file(
                            file, current_path, data_store, processed_ctr
                        )

            states_sum = TableSummary(data_store.session, data_store.db_classes.State)
            platforms_sum = TableSummary(
                data_store.session, data_store.db_classes.Platform
            )
            second_table_summary_set = TableSummarySet([states_sum, platforms_sum])
            print(second_table_summary_set.report("==After=="))

        print(f"Files got processed: {processed_ctr} times")

    def process_file(self, file, current_path, data_store, processed_ctr):
        filename, file_extension = os.path.splitext(file)
        # make copy of list of importers
        good_importers = self.importers.copy()

        full_path = os.path.join(current_path, file)
        # print("Checking:" + str(full_path))

        # start with file suffixes
        tmp_importers = good_importers.copy()
        for importer in tmp_importers:
            # print("Checking suffix:" + str(importer))
            if not importer.can_load_this_type(file_extension):
                good_importers.remove(importer)

        # now the filename
        tmp_importers = good_importers.copy()
        for importer in tmp_importers:
            # print("Checking filename:" + str(importer))
            if not importer.can_load_this_filename(filename):
                good_importers.remove(importer)

        # tests are starting to get expensive. Check
        # we have some file importers left
        if len(good_importers) > 0:

            # now the first line
            tmp_importers = good_importers.copy()
            first_line = self.get_first_line(full_path)
            for importer in tmp_importers:
                # print("Checking first_line:" + str(importer))
                if not importer.can_load_this_header(first_line):
                    good_importers.remove(importer)

            # get the file contents
            file_contents = self.get_file_contents(full_path)

            # lastly the contents
            tmp_importers = good_importers.copy()
            for importer in tmp_importers:
                if not importer.can_load_this_file(file_contents):
                    good_importers.remove(importer)

            # ok, let these importers handle the file
            datafile = data_store.get_datafile(filename, file_extension)

            # Run all parsers
            for importer in good_importers:
                processed_ctr += 1
                importer.load_this_file(data_store, full_path, file_contents, datafile)

            # Run all validation tests
            errors = list()
            for importer in good_importers:
                # Call related validation tests, extend global errors lists if the importer has errors
                if not datafile.validate(
                    validation_level=importer.validation_level,
                    errors=importer.errors,
                    parser=importer.short_name,
                ):
                    errors.extend(importer.errors)

            # If all tests pass for all parsers, commit datafile
            # get current time without milliseconds
            timestamp = str(datetime.utcnow())[:-7]
            if not errors:
                log = datafile.commit(data_store.session)
                # write extraction log to output folder
                with open(
                    os.path.join(
                        self.output_path, f"{filename}_output_{timestamp}.log"
                    ),
                    "w",
                ) as f:
                    f.write("\n".join(log))
                # move original file to output folder
                # TODO: Skip for now
                # shutil.move(full_path, os.path.join(self.output_path, file))
            else:
                # write error log to the output folder
                with open(
                    os.path.join(
                        self.output_path, f"{filename}_errors_{timestamp}.log"
                    ),
                    "w",
                ) as f:
                    json.dump(errors, f, ensure_ascii=False, indent=4)

        return processed_ctr

    def register_importer(self, importer):
        """Adds the supplied importer to the list of import modules
        
        :param importer: An importer module that must define the functions defined
        in the Importer base class
        :type importer: Importer
        """
        self.importers.append(importer)

    def register_importers(self, importers):
        """Adds all the importers in the supplied list to the list of import modules

        :param importers: A list of importers, each of which is an Importer class that inherits
        from the Importer base class
        :type importers: list
        """
        for importer in importers:
            self.importers.append(importer)

    @staticmethod
    def get_first_line(file_path: str):
        """Retrieve the first line from the file

        :param file_path: Full file path
        :type file_path: String
        :return: First line of text
        :rtype: String
        """
        try:
            with open(file_path, "r", encoding="windows-1252") as f:
                first_line = f.readline()
            return first_line
        except UnicodeDecodeError:
            return None

    @staticmethod
    def get_file_contents(full_path: str):
        try:
            with open(full_path, "r", encoding="windows-1252") as f:
                lines = f.read().split("\n")
            return lines
        except UnicodeDecodeError:
            return None
