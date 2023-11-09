import wx
import json
import subprocess
import os
import openai
import csv
from job import response as response
from job import main

import pathlib
import sys
from subprocess import Popen, CREATE_NEW_CONSOLE

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
    "input_columns": 2,
    "output_column": 2,
    "row_start": "start",
    "row_end": "end",
    "system_msg": "You are a helpful assistant",
}


def is_valid_json(json_string):
    try:
        json.loads(json_string)
    except ValueError:
        return False
    return True




def is_api_key_valid(api_key):
    try:
        openai.api_key = api_key
        response = openai.Completion.create(
            engine="davinci", prompt="This is a test.", max_tokens=5
        )
    except:
        return False
    else:
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
        wx.Frame.__init__(self, None, title="Callio", size=(600, 800))
        panel = wx.Panel(self)
        
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

        self.text_boxes = dict()
        vbox = wx.BoxSizer(wx.VERTICAL)

        for i, key in enumerate(self.config.keys()):
            if key == "context":
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

        """self.count_text = wx.TextCtrl(panel, style=wx.TE_READONLY)
        self.count_text.SetValue("Count: 0")
        """
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.run_button, flag=wx.RIGHT, border=10)
        hbox.Add(self.context_button, flag=wx.RIGHT, border=10)
        hbox.Add(self.view_context_button, flag=wx.RIGHT, border=10)
        hbox.Add(self.clear_context_button)

        vbox.Add(hbox, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        #vbox.Add(self.count_text, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        panel.SetSizer(vbox)
        panel.Fit()


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
            openai.api_key = self.config["api_key"]
            models = openai.Model.list()["data"]
        except Exception as e:
            print(e)
            return []

        model_list = []
        for model in models:
            model_list.append(model["id"])
        return model_list
    
    def sample_assistant_response(self):
        openai.api_key = self.config["api_key"]
        message = [{"role": "system", "content": self.config["system_msg"]}] + self.context 
        try:
            open_response = response("", sleep_time = 1, model=self.config["model"], context=message, timeout=10, temperature=self.config["temperature"], max_tokens = self.config["max_tokens"])
            open_response = open_response["choices"][0]["message"]["content"]
        except openai.error.Timeout:
            open_response = "Timeout occured (replace this)"
        except Exception as e:
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


    def view_edit_context(self, event):
        if len(self.context) == 0:
            message = ""
        else:
            message = json.dumps(self.context, indent=4)
        input_box = wx.TextEntryDialog(None, "Edit Context", style= wx.TE_MULTILINE|wx.RESIZE_BORDER|wx.OK|wx.CANCEL,value=message)
        if input_box.ShowModal() == wx.ID_OK:
            valid_context = []
            message = input_box.GetValue()
            if is_valid_json(message):
                self.context = json.loads(message)
            else:
                wx.MessageBox(
                    f"Invalid context: {message}", "Error", wx.OK | wx.ICON_ERROR
                )
                self.view_edit_context(event)
        self.update_config()
            
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
                    response = self.sample_assistant_response()
                    default = response
                    
                dialog = wx.TextEntryDialog(None, "Enter text for: " + role, style = wx.TE_MULTILINE|wx.RESIZE_BORDER|wx.OK|wx.CANCEL, value=default)


                if dialog.ShowModal() == wx.ID_OK:
                    self.context.append({"role": role.lower(), "content": dialog.GetValue()}) 
    
    def save_config(self):
        self.update_config()
        with open(self.file_path, "w") as f:
            json.dump(self.config, f)
    
    def update_config(self):
        # update config file
        for key in self.config.keys():
            if key == "context":
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
                str(e),
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