import json
import openai
import csv
import concurrent.futures
import time
import os

class Job:
    def __init__(self, config):
        self.config = config
        self.api_key = self.config["api_key"]
        openai.api_key = self.api_key
        self.input_file_name = self.config["input_file"]
        self.output_file_name = self.config["output_file"]
        self.include_headers = self.config["include_headers"]
        self.keep_data = self.config["keep_data"]
        self.max_workers = self.config["max_workers"]
        self.model = self.config["model"]
        self.input_cost = self.config["input_cost"]
        self.output_cost = self.config["output_cost"]
        self.max_tokens = self.config["max_tokens"]
        self.temperature = self.config["temperature"]
        self.task_timeout = self.config["task_timeout"]
        self.sleep_time = self.config["sleep_time"]
        self.input_column = self.config["input_column"] - 1
        self.output_column = self.config["output_column"] - 1
        self.system_msg = self.config["system_msg"]
        self.context = self.config["context"]
        self.output_data = []
        self.cost = 0
        self.message = [{"role": "system", "content": self.system_msg}] + self.context
        with open(self.input_file_name, "r", newline="") as input_file:
            reader = csv.reader(input_file)
            self.input_headers = next(reader)
            reader_len = sum(1 for row in reader)
            input_file.seek(0)
            reader = csv.reader(input_file)
            next(reader)
            self.row_start = (0 if self.config["row_start"].lower() == "start" else int(self.config["row_start"]))
            self.row_end = (reader_len if self.config["row_end"].lower() == "end" else int(self.config["row_end"]))
            self.input_data = [row for row in reader][self.row_start:self.row_end]
            self.input_data = [row for row in self.input_data if len(row) > 0]
            self.input_column_data = [row[self.input_column] for row in self.input_data]
        self.count = len(self.input_column_data)
        self.input_tokens = 0
        self.output_tokens = 0

    def update_cost(self):
        self.cost = (
            self.input_cost * self.input_tokens / 1000
            + self.output_cost * self.output_tokens / 1000
        )

    def create_workers(self):
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            futures = executor.map(self.response_wrapper, self.input_column_data)
        return [future for future in futures]



    def response_wrapper(self, input):
        open_response = response(input, self.sleep_time, self.model, self.message, self.task_timeout, self.temperature, self.max_tokens)
        self.input_tokens += open_response["usage"]["prompt_tokens"]
        self.output_tokens += open_response["usage"]["completion_tokens"]
        self.count -= 1
        self.update_cost()
        print(
            f"Remaining: {self.count} | Cost: ${round(self.cost, 4)} | Input Tokens: {self.input_tokens} | Output Tokens: {self.output_tokens}", end="\r"
        )
        open_response = open_response["choices"][0]["message"]["content"]
        return open_response

    def write_data(self):
        with open(self.output_file_name, "w", newline="") as output_file:
            writer = csv.writer(output_file)
            if self.include_headers:
                writer.writerow(self.input_headers)
            if self.keep_data:
                for i, row in enumerate(self.input_data):
                    row[self.output_column] = self.output_data[i]
                writer.writerows(self.input_data)
            else:
                for i in range(len(self.output_data)):
                    writer.writerow([self.output_data[i]])
        os.system('cls' if os.name == 'nt' else 'clear')
        print("Job Complete. Output written to: " + self.output_file_name)
        print("Total Cost: $" + str(round(self.cost, 6)))
        print("Total Tokens: " + str(self.input_tokens + self.output_tokens))

    def main(self):
        self.output_data = self.create_workers()
        self.write_data()



def retry_with_exponential_backoff(
    func,
    initial_delay = 1,
    exponential_base = 2,
    jitter = True,
    max_retries = 20,
    errors = (openai.error.RateLimitError, ),
):
    def wrapper(*args, **kwargs):
        num_retries = 0
        delay = initial_delay

        while True:
            try:
                return func(*args, **kwargs)
            except errors as e:
                num_retries += 1
                if num_retries > max_retries:
                    raise Exception("Max retries exceeded")
                
                delay *= exponential_base * (1 + (jitter * random.random()))
                time.sleep(delay)

            except Exception as e:
                raise e
            
    return wrapper


@retry_with_exponential_backoff
def response(input, sleep_time, model, context, timeout, temperature, max_tokens):
    if len(input) > 0:
        messages = context + [{"role": "user", "content": input}]
    else:
        messages = context
    try:
        open_ai_res = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            request_timeout=timeout,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=1,
        )

    except openai.error.APIError as error:
        print(f"API error in getting response for: {input}: {error}")
        time.sleep(sleep_time)
        return response(input, sleep_time, model, context, timeout, temperature, max_tokens)
    except openai.error.RateLimitError as error:
        time.sleep(sleep_time)
        return response(input, sleep_time, model, context, timeout, temperature, max_tokens)
    except openai.error.Timeout as error:
        time.sleep(sleep_time)
        return response(input, sleep_time, model, context, timeout, temperature, max_tokens)
    except openai.error.ServiceUnavailableError as error:
        time.sleep(sleep_time)
        print(f"Service unavailable error in getting response for: {input}: {error}")
        return response(input, sleep_time, model, context, timeout, temperature, max_tokens)
    return open_ai_res



def main(config):
    job = Job(config)
    job.main()


if __name__ == "__main__":
    main()