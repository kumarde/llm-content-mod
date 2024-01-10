import openai
from secret import OPENAI_KEY
import sys
import json
import time
import copy

openai.api_key = OPENAI_KEY

BASE_CHAT = [
        {"role": "system", "content": "You are a helpful toxicity detection assistant."},
        {"role": "user", "content": "A toxic comment is a rude, disrespectful, or unreasonable comment that is likely to make you leave a discussion."},
        {"role": "assistant", "content": "OK, I understand the definition."},
        {"role": "user", "content": """
            Consider the following comment: You are enormously stupid.

            Return a JSON object with a two fields, "rating," that is is a score from 1 to 10 depending on how  toxic the comment is based on our definition, and "explanation" which contains a reason for the rating. 
            """},
        {"role": "assistant", "content": """
            {"rating": 9, "explanation": "The comment is disrespectful and likely to make the recipient feel insulted and uncomfortable."}
            """},
    ] 

def main():
    comments = sys.argv[1]

    count = 0 
    for l in open(comments, 'r'):
        if count % 100 == 0:
            sys.stderr.write("Processed " + str(count) + " comments.\n")
            if count > 0:
                time.sleep(20)
        l = l.strip()
        data = json.loads(l)
        comment_text = data['comment']['comment']
        prompt = {
                "role": "user",
                "content": f"""
                Consider the following comment: {comment_text}
            
                Return a JSON object with a two fields, "rating," that is is a score from 1 to 10 depending on how  toxic the comment is based on our definition, and "explanation" which contains a reason for the rating.
                """
        }

        messages = copy.deepcopy(BASE_CHAT)
        messages.append(prompt)

        try:
            completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
        except Exception as e:
            #print(e)
            sys.stderr.write("Something went wrong...\n")
            sys.stderr.write(comment_text + "\n")
            continue

        data['openai_completion'] = {
                'prompt'    :   prompt,
                'response'  :   completion
        }

        print(json.dumps(data))
        count += 1

if __name__ == "__main__":
    main()
