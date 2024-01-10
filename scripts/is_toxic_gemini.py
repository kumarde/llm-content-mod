import sys
import pathlib
import textwrap
import json
import time
import csv

import google.generativeai as genai
from secret import *

import grpc

genai.configure(api_key=GEMINI_KEY)

def main():
    comments = sys.argv[1]
    model = genai.GenerativeModel('gemini-pro')
    errors = {}
    
    count = 0
    for l in open(comments, 'r'):
        if count % 60 == 0:
            sys.stderr.write("Processed " + str(count) + " comments.\n")
            if count > 0:
                time.sleep(20)
        l = l.strip()
        data = json.loads(l)
        comment_text = data['comment']['comment']

        prompt = f"""A toxic comment is a rude, disrespectful, or unreasonable comment that is likely to make you leave a discussion.

    Consider the following comment: "{comment_text}"

    Return a JSON object with a two fields, "rating," that is is a score from 1 to 10 depending on how toxic the comment is based on our definition, and "explanation" which contains a reason for the rating."""
        #print(prompt)
        try:
            response = model.generate_content(prompt, 
                                          safety_settings = [{"category": "HARM_CATEGORY_HARASSMENT","threshold": "BLOCK_NONE",},
                                                            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE",},
                                                            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE",},
                                                            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE",}]
                                          )
            data['gemini_completion'] = {
                'prompt'    :   prompt,
                'response'  :   response.text
            }
            print(json.dumps(data))
        except Exception as e:
            if type(e) == grpc.RpcError:
                time.sleep(2)
            else:
                sys.stderr.write("Something went wrong...\n")
                sys.stderr.write("Comment text is: " + comment_text + "\n")
                errors[comment_text] = str(response.prompt_feedback)
                count += 1
            continue

        count += 1

    # Print errors
    with open("data/gemini_errors.log", 'w') as ofile:
        writer = csv.writer(ofile)
        for text, reason in errors.items():
            writer.writerow([text, str(reason)])

if __name__ == "__main__":
    main()
