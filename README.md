# OpenAI API Call Formatter Scripts

These scripts provide a graphical user interface (GUI) application and job runner for making bulk API calls to the OpenAI API. Inputs are scraped from a .csv file. 

## GUI Script

The GUI script is a Python script built using the WXPython, a graphical toolkit for creating desktop user interface applications. This GUI script is used to define the parameters for making API calls to the OpenAI models. The parameters include OpenAI API key, input and output file locations, the number of workers to use, model preferences, cost per input and output, max tokens, the temperature for responses, etc.

You input your details and click run. Your details and parameters are saved in a JSON configuration file, so that the program can be closed and relaunched.  

This script provides a user-friendly way to set up your parameters for making API calls to OpenAI without having to mess with code.

You can view sample responses that are generated with the same parameters that will be used on your whole input dataset. 

**NOTE**
The responses from the LLM's are only as good as the context that is given.

A Bad Example Context:

`[
    {
        "role": "user",
        "content": "optimize this product name"
    }
]`

Input:
"Amethyst Gem in Abstract Cut, 11.03 carats, 17.69 x 13.58 mm, Purple Color"
Output:
"Purple Haze Amethyst: Abstract Cut, 11.03 Carats"


A Good Example Context (contains a curated example for the model to refrence)

`[
    {
        "role": "user",
        "content": "I'm going to give you a product name from a gemstone website. You will return only the product name with enhanced language - not overdone. The optimized name can't be more than 15 words long. Must be in this format, Name - Color - Size - Weight - Other"
    },
    {
        "role": "assistant",
        "content": "Sure, please provide me with the product name."
    },
    {
        "role": "user",
        "content": "Amethyst Gem in Abstract Cut, 11.03 carats, 17.69 x 13.58 mm, Purple Color"
    },
    {
        "role": "assistant",
        "content": "Amethyst Abstract Cut - Purple - 17.69x13.58mm - 11.03ct"
    }
]`

Input:

"Xtra Fine Aquamarine Gemstone in Emerald Cut, 14.78 carats, Deep Color, 19.6 x 12.9 mm"

Output:

"Fine Aquamarine - Emerald Cut - Deep Color - 19.6x12.9mm - 14.78ct"



## Job Runner Script

The job runner script is a Python script that handles the actual job of making API calls to the API. It reads the parameters set in the configuration JSON file created by the GUI script and makes concurrent API calls to the API using a ThreadPoolExecutor. 

It also keeps track of usage by counting input and output tokens and calculating the total cost accordingly, printing the remaining count of API calls, amount spent so far, and token count in live time.

In summary, the GUI script is used to set up and start the job and the job runner script handles the actual running of the job based on the parameters set via the GUI.

## Dependencies

Both scripts require the `openai`, `wxPython`, and `backoff` Python libraries. 

## How to Run

You can simply run the GUI script in a Python environment and use the GUI to set the parameters for your job and click run. This will then use the job runner script to carry out the task. Any required settings are entered through the GUI, you do not have to touch the code or interact with the command line to use these scripts.

Or you can use the provided .exe file to just run the program as an executable.

If you want to **compile your own** .exe or other form of executable for a different OS.

In the src directory:
`python -m PyInstaller --onefile app.py`
And then to include the icon!
`python -m PyInstaller --icon ../assets/carrot.ico --onefile app.py`


**Note**: I wrote this in a couple hours so don't expect it to be bug free.