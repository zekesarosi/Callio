# OpenAI API Call Formatter Scripts

These scripts provide a graphical user interface (GUI) application and job runner for making bulk API calls to the OpenAI API.

## GUI Script

The GUI script is a Python script built using the WXPython, a graphical toolkit for creating desktop user interface applications. This GUI script is used to define the parameters for making API calls to the OpenAI models. The parameters include OpenAI API key, input and output file locations, the number of workers to use, model preferences, cost per input and output, max tokens, the temperature for responses, etc.

You input your details and click run. Your details and parameters are saved in a JSON configuration file. The GUI script also has functionalities to validate the API key by making a test API request to OpenAI and validating input files by ensuring the file exists and is a valid .csv file. 

This script provides a user-friendly way to set up your parameters for making API calls to OpenAI without having to mess with code.

## Job Runner Script

The job runner script is a Python script that handles the actual job of making API calls to the API. It reads the parameters set in the configuration JSON file created by the GUI script and makes concurrent API calls to the API using a ThreadPoolExecutor. 

It also keeps track of usage by counting input and output tokens and calculating the total cost accordingly, printing the remaining count of API calls, amount spent so far, and token count in live time.

In summary, the GUI script is used to set up and start the job and the job runner script handles the actual running of the job based on the parameters set via the GUI.

## Dependencies

Both scripts require the `openai`, `wx`, `json`, `csv`, `concurrent.futures`, `subprocess`, `os` and the `time` Python libraries. 

## How to Run

You can simply run the GUI script in a Python environment and use the GUI to set the parameters for your job and click run. This will then use the job runner script to carry out the task. Any required settings are entered through the GUI, you do not have to touch the code or interact with the command line to use these scripts.

Or you can use the provided .exe file to just run the program as an executable.

If you want to **compile your own** .exe 

In a directory containing all src files:
`python -m PyInstaller --onefile app.py`


**Note**: I wrote this in a couple hours so don't expect it to be bug free.