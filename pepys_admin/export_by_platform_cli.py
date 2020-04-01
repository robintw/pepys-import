import cmd


class ExportByPlatformNameShell(cmd.Cmd):
    prompt = "(pepys-admin) (export by platform) "

    def __init__(self, data_store, options, objects):
        super(ExportByPlatformNameShell, self).__init__()
        self.data_store = data_store
        self.options = options
        self.objects = objects

    @staticmethod
    def do_cancel():
        print("Returning to the previous menu...")

    def do_export(self, option):
        datafile_id = option["datafile_id"]
        sensor_id = option.get("sensor_id")  # May be missing if it's a Comment object
        platform_id = option.get("platform_id")  # May be missing if it's a State or Contact object
        default_export_name = f"exported_{option['name']}.rep"
        file_name = input(
            f"Please provide a name (Press Enter for default value " f"({default_export_name})):"
        )
        if file_name:
            file_name += ".rep"
        export_file_name = file_name or default_export_name
        print(f"Objects are going to be exported to '{export_file_name}'.")
        with self.data_store.session_scope():
            self.data_store.export_datafile(datafile_id, export_file_name, sensor_id, platform_id)
            print(f"Objects successfully exported to {export_file_name}.")
        return True

    def default(self, line):
        cmd_, arg, line = self.parseline(line)
        if cmd_ in self.options:
            if cmd_ == "0":
                return True
            selected_option = self.objects[int(cmd_) - 1]
            return self.do_export(selected_option)
        else:
            print(f"*** Unknown syntax: {line}")

    def postcmd(self, stop, line):
        if stop is False:
            print("-" * 61)
            print(self.intro)
        return cmd.Cmd.postcmd(self, stop, line)