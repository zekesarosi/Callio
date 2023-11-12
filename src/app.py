import wx
import json
import subprocess
import os
import openai
from openai import OpenAI
import csv
import threading
from job import response as response
from job import main
from job import read_csv_file as read_csv_file

import pathlib
import sys

import queue

import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(True)
except:
    pass




descriptions = {
    "api_key": "Enter your OpenAI API Key here.",
    "input_file": "Click to browse for input file",
    "output_file": "Enter the name of your output.csv file here.",
    "include_headers": "Check the box to keep the headers of the original file in the output file",
    "keep_data": "Check the box to keep the non-optimized data as well as the optimized. For example if you are using the tool on Column 2, the output file will also have the original data for other columns",
    "max_workers": "Enter the number of workers to use for the script. If you are unsure, leave this at 15.",
    "model": "Select the model that you want to use for the script. If you are unsure, leave this at gpt-3.5-turbo.",
    "input_cost": "Enter the cost in dollars of the input prompt. For gpt-3.5-turbo the value is $0.0015/1000 tokens.",
    "output_cost": "Enter the cost in dollars of the input prompt. For gpt-3.5-turbo the value is $0.002/1000 tokens.",
    "max_tokens": "Enter the maximum number of tokens to leave for the response. If you are unsure, leave this at 30.",
    "temperature": "Enter the models temperature for the response. If you are unsure, leave this at 0.9.",
    "task_timeout": "Enter the maximum number of seconds to wait for a response from the model before retrying the request. If you are unsure, leave this at 20.",
    "sleep_time": "Enter the number of seconds to wait between failed requests to the model. If you are unsure, leave this at 10.",
    "input_columns": "Enter the column numbers of the input data in the input file. Must be seperated by commas. Ex: If the input data is in columns A and B then enter 1,2.",
    "output_column": "Enter the column number of the output data in the input file. Usually this is the same as the input column. Ex: If the output column is C then enter 3.",
    "system_msg": "Enter the role you want the model to take on. Ex: You are a helpful assistant. If you aren't sure just leave it",
    "separator": "Enter the separator that you want between data from multiple rows. If you want {productName} - {price} then enter ' - '. This will only work if multiple input columns are provided",
    "row_start": "Enter the row number to start on in the input file. Ex: If you want to start on row 2 then enter 2. If you want to start on the first row then enter: start.",
    "row_end": "Enter the row number to end on in the input file. Ex: If you want to end on row 100 then enter 100. If you want to end on the last row then enter: end.",
    # and so on for each parameter in your config file
}


config_display = {
    "api_key": "Your API Key",
    "input_file": "Input File",
    "output_file": "Output File",
    "include_headers": "Include Headers",
    "keep_data": "Keep Data",
    "max_workers": "Max Workers",
    "model": "Model to use",
    "input_cost": "Input Cost (Dollars)",
    "output_cost": "Output Cost (Dollars)",
    "max_tokens": "Maximum Tokens",
    "temperature": "Model Temperature",
    "task_timeout": "Model Response Timeout",
    "sleep_time": "Model Sleep Time",
    "input_columns": "Input Columns",
    "output_column": "Output Column",
    "row_start": "Row Start",
    "row_end": "Row End",
    "separator": "Separator",
    "system_msg": "System Message",
}


default_config = {
    "api_key": "your_api_key_here",
    "input_file": "input_data.csv",
    "output_file": "output_data.csv",
    "include_headers": True,
    "keep_data": True,
    "max_workers": 50,
    "model": "gpt-3.5-turbo",
    "input_cost": 0.0015,
    "output_cost": 0.002,
    "max_tokens": 30,
    "temperature": 0.9,
    "task_timeout": 20,
    "sleep_time": 10,
    "input_columns": "2",
    "output_column": 2,
    "row_start": "start",
    "row_end": "end",
    "separator": " - ",
    "system_msg": "You are a helpful assistant",
    # App Parameters
    "sample_inputs": "",
    "frame_size": (800, 800),
}


def is_valid_json(json_string):
    try:
        json.loads(json_string)
    except ValueError:
        return False
    return True





def check_if_output_file(file_path):
    # check if output file is writeable to. ie is not open in another program
    with open(file_path, 'w') as f:
        f.close()
        pass

def check_if_csv_file(file_path):
    if not os.path.isfile(file_path):
        return False
    if not file_path.endswith(".csv"):
        return False
    try:
        with open(file_path, "r") as f:
            csv.reader(f)
    except:
        return False
    return True


def get_datadir() -> pathlib.Path:

    """
    Returns a parent directory path
    where persistent application data can be stored.

    # linux: ~/.local/share
    # macOS: ~/Library/Application Support
    # windows: C:/Users/<USER>/AppData/Roaming
    """

    home = pathlib.Path.home()

    if sys.platform == "win32":
        return home / "AppData/Roaming"
    elif sys.platform == "linux":
        return home / ".local/share"
    elif sys.platform == "darwin":
        return home / "Library/Application Support"




class MainFrame(wx.Frame):
    def __init__(self):
        
        self.dir_path = get_datadir() / "Callio"
        self.text_font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        try:
            os.mkdir(str(self.dir_path))
        except FileExistsError:
            pass

        self.file_path = str(self.dir_path  / 'config.json')

        if not os.path.isfile(self.file_path):
            self.config = default_config.copy()
            self.context = []  # list of dicts

        else:
            with open(self.file_path, "r") as f:
                self.config = json.load(f)
                self.context = self.config["context"]
                for key in default_config.keys():
                    if key not in self.config:
                        self.config[key] = default_config[key]
                delete_keys = [key for key in self.config.keys() if key not in default_config.keys()]
                for key in delete_keys:
                    del self.config[key]
        self.text_boxes = dict()
        
        wx.Frame.__init__(self, None, title="Callio", size=self.config["frame_size"])
        panel = wx.Panel(self)
        
        vbox = wx.BoxSizer(wx.VERTICAL)

        for i, key in enumerate(self.config.keys()):
            if key == "context":
                continue
            if key == "sample_inputs":
                continue
            if key == "frame_size":
                continue
            hbox = wx.BoxSizer(wx.HORIZONTAL)

            label = wx.StaticText(panel, label=config_display[key])
            label.Bind(wx.EVT_LEFT_DOWN, self.show_description)
            label.SetToolTip(
                descriptions.get(key, "")
            )  # set the description as tooltip
            hbox.Add(label, flag=wx.RIGHT, border=8)




            if key in ["include_headers", "keep_data"]:
                # Use a checkbox for true/false values.
                self.text_boxes[key] = wx.CheckBox(panel)
                # Check or uncheck the box based on the current value.
                self.text_boxes[key].SetValue(self.config.get(key, False))

            else:
                self.text_boxes[key] = wx.TextCtrl(panel)
                self.text_boxes[key].SetValue(str(self.config[key]))

            if self.text_boxes[key].GetContainingSizer() is not None:
                self.text_boxes[key].GetContainingSizer().Detach(self.text_boxes[key])

            if key == "input_file":
                self.text_boxes[key].Bind(wx.EVT_LEFT_DOWN, self.open_file_dialog)
            elif key == "model":
                self.text_boxes[key].Bind(wx.EVT_LEFT_DOWN, self.choose_model)

            hbox.Add(self.text_boxes[key], proportion=1)

            vbox.Add(hbox, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        self.run_button = wx.Button(panel, label="Run")
        self.run_button.Bind(wx.EVT_BUTTON, self.run_script)

        self.context_button = wx.Button(panel, label="Add Context")
        self.context_button.Bind(wx.EVT_BUTTON, self.add_context)

        self.view_context_button = wx.Button(panel, label="View / Edit Context")
        self.view_context_button.Bind(wx.EVT_BUTTON, self.view_edit_context)

        self.clear_context_button = wx.Button(panel, label="Clear Context")
        self.clear_context_button.Bind(wx.EVT_BUTTON, self.clear_context)

        self.sample_responses_button = wx.Button(panel, label="Generate Sample Responses")
        self.sample_responses_button.Bind(wx.EVT_BUTTON, self.sample_responses)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.run_button, flag=wx.RIGHT, border=10)
        hbox.Add(self.context_button, flag=wx.RIGHT, border=10)
        hbox.Add(self.view_context_button, flag=wx.RIGHT, border=10)
        hbox.Add(self.clear_context_button, flag=wx.RIGHT, border=10)

        vbox.Add(hbox, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        vbox.Add(self.sample_responses_button, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        #vbox.Add(self.count_text, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        panel.SetSizer(vbox)
        panel.Fit()
        try:
            self.client = OpenAI(api_key=self.config["api_key"])
        except Exception as e:
            print(e)
            self.client = "no client"

        self.response_queue = queue.Queue()

    def generate_sample_inputs(self, number):
        _, _, input_column_data = read_csv_file(self.config["input_file"], self.config["input_columns"], row_start=self.config["row_start"], number=number)
        sample_inputs = ""
        for i, input in enumerate(input_column_data):
            sample_inputs += input + "\n"
            if i >= number - 1:
                break
        return sample_inputs

    def sample_responses(self, event):
        self.update_config()
        # Create a popup box for user to select if they want to paste sample inputs or generate them from file
        dlg = wx.SingleChoiceDialog(None, 'Select Option', 'Choices', ["Paste Sample Inputs", "Generate Sample Inputs From File"])
        if dlg.ShowModal() == wx.ID_OK:
            selection = dlg.GetSelection()
            if selection == 0:
                text = self.config["sample_inputs"]
            elif selection == 1:
                # Create a text entry for the user to specify how many
                input_box = wx.TextEntryDialog(None, "Enter number of sample inputs to read", style=wx.OK|wx.CANCEL,value="10")
                if input_box.ShowModal() == wx.ID_OK:
                    number = input_box.GetValue()
                    try:
                        number = int(number)
                        text = self.generate_sample_inputs(number)
                    except ValueError:
                        wx.MessageBox(
                            "Invalid number", "Error", wx.OK | wx.ICON_ERROR
                        )
                        return
                    except Exception as e:
                        wx.MessageBox(
                            f"Error generating sample inputs: {e}", "Error", wx.OK | wx.ICON_ERROR
                        )
                        return
                else:
                    return
        
        input_box = wx.TextEntryDialog(None, "Paste Sample Inputs on newlines", style=wx.TE_MULTILINE|wx.RESIZE_BORDER|wx.OK|wx.CANCEL,value=text)
        
        if input_box.ShowModal() == wx.ID_OK:
            # Print the current frame size
            input_data = input_box.GetValue()
            self.config["sample_inputs"] = input_data
            self.save_config()
            os.system('cls' if os.name == 'nt' else 'clear')
            
            # Split inputs and process each in a separate thread
            threads = []
            for i, line in enumerate(input_data.split("\n")):
                if len(line) > 0:
                    thread = threading.Thread(target=self.process_input, args=(i, line, self.response_queue))
                    threads.append(thread)
                    
            # Start threads
            for thread in threads:
                thread.start()

            # Wait for all threads to finish
            for thread in threads:
                thread.join()

            # Process responses in order
            responses_in_order = sorted(list(self.response_queue.queue), key=lambda x: x[0])
            for _, response in responses_in_order:
                self.print_response(response)
    
    def process_input(self, order, line, response_queue):
        try:
            response = self.sample_assistant_response(line)
            response_queue.put((order, response))
        except Exception as e:
            response_queue.put((order, str(e)))
    
    def print_response(self, response):
        wx.CallAfter(print, response)
        wx.CallAfter(print, "\n")

    def choose_model(self, event):
        entries = self.get_model_list()
        if len(entries) == 0:
            wx.MessageBox(
                "No models found", "Error", wx.OK | wx.ICON_ERROR
            )
        else:
            dlg = wx.SingleChoiceDialog(None, 'Select Model', 'Choices', entries)
            if dlg.ShowModal() == wx.ID_OK:
                selection = dlg.GetSelection()
                self.text_boxes["model"].SetValue(entries[selection])

    def get_model_list(self):
        try:
            models = self.client.models.list()
        except Exception as e:
            print(e)
            return []

        model_list = [model.id for model in models]
        return model_list

    def sample_assistant_response(self, input):
        message = [{"role": "system", "content": self.config["system_msg"]}] + self.context
        try:
            open_response = response(self.client, input, timeout = 7, sleep_time = 1, model=self.config["model"], context=message, temperature=self.config["temperature"], max_tokens = self.config["max_tokens"])
            open_response = open_response.choices[0].message.content
        except openai.Timeout:
            open_response = ""
            pass
        except Exception as e:
            print(e)
            open_response = ""
        return open_response

    def open_file_dialog(self, event):
            file_dialog = wx.FileDialog(self, "Open", "", "",
                                        "All Files (*.*)|*.*",
                                        wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)

            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return

            path = file_dialog.GetPath()
            self.text_boxes["input_file"].SetValue(path)


    def on_close(self, event):
        # update config file
        for key in self.text_boxes.keys():
            self.config[key] = self.text_boxes[key].GetValue()
        self.config["context"] = self.context
        with open("config.json", "w") as f:
            json.dump(self.config, f, indent=4)
        self.Destroy()

    def clear_context(self, event):
        self.context = []


    def view_edit_context(self, event, temp_context = None):
        if len(self.context) == 0:
            message = ""
        else:
            message = json.dumps(self.context, indent=4)
            if temp_context is None:
                temp_context = message
        input_box = wx.TextEntryDialog(None, "Edit Context", style= wx.TE_MULTILINE|wx.RESIZE_BORDER|wx.OK|wx.CANCEL,value=temp_context)
        if input_box.ShowModal() == wx.ID_OK:
            valid_context = []
            message = input_box.GetValue()
            temp_context = message
            if is_valid_json(message):
                self.context = json.loads(message)
                self.update_config()
            else:
                wx.MessageBox(
                    f"Invalid context: {message}", "Error", wx.OK | wx.ICON_ERROR
                )
                self.view_edit_context(event, temp_context = temp_context)

    def show_description(self, event):
        label = event.GetEventObject()
        description = label.GetToolTip().GetTip()
        wx.MessageBox(description, "Description", wx.OK | wx.ICON_INFORMATION)


    def add_context(self, event):
        entries = ["User", "Assistant"]
        dlg = wx.MultiChoiceDialog(None, 'Select Role', 'Choices', entries)
        self.update_config()

        if dlg.ShowModal() == wx.ID_OK:
            selections = dlg.GetSelections()

            for idx in selections:
                role = entries[idx]

                default = ""
                # Add additional button for 'Assistant'
                if role == "Assistant":
                    response = self.sample_assistant_response("")
                    default = response

                dialog = wx.TextEntryDialog(None, "Enter text for: " + role, style = wx.TE_MULTILINE|wx.RESIZE_BORDER|wx.OK|wx.CANCEL, value=default)


                if dialog.ShowModal() == wx.ID_OK:
                    self.context.append({"role": role.lower(), "content": dialog.GetValue()})




    def is_api_key_valid(self, api_key):
        try:
            response = self.client.completions.create(
                engine="davinci", prompt="This is a test.", max_tokens=5
            )
        except:
            return False

        return True



    def save_config(self):
        self.update_config()
        with open(self.file_path, "w") as f:
            json.dump(self.config, f)

    def update_config(self):
        # update config file
        for key in self.config.keys():
            if key == "context":
                continue
            if key == "sample_inputs":
                continue
            if key == "frame_size":
                size = self.GetSize()
                self.config["frame_size"] = (size[0], size[1])
                continue
            value = self.text_boxes[key].GetValue()
            if isinstance(self.config[key], int):
                value = int(value)
            elif isinstance(self.config[key], float):
                value = float(value)

            self.config[key] = value
        self.config["context"] = self.context
        # check if input file exist


    def run_script(self, event):

        self.save_config()
        os.system('cls' if os.name == 'nt' else 'clear')

        if not check_if_csv_file(self.config["input_file"]):
            wx.MessageBox(
                "Input file does not exist or not valid csv",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
            return
        try:
            check_if_output_file(self.config["output_file"])
        except Exception as e:
            wx.MessageBox(
                f"Job Error: {e}",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
            return
        try:
            main(self.config)
        except Exception as e:
            wx.MessageBox(
                str(e),
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
            return

def APPmain():
    app = wx.App()
    frame = MainFrame()
    frame.Show()
    app.MainLoop()


if __name__ == "__main__":
    APPmain()
