import sys
import json
from markdown import Markdown
from io import StringIO
import openai
from secret import OPENAI_KEY
import csv
import copy
import time

openai.api_key = OPENAI_KEY

def unmark_element(element, stream=None):
    if stream is None:
        stream = StringIO()
    if element.text:
        stream.write(element.text)
    for sub in element:
        unmark_element(sub, stream)
    if element.tail:
        stream.write(element.tail)
    return stream.getvalue()


# patching Markdown
Markdown.output_formats["plain"] = unmark_element
__md = Markdown(output_format="plain")
__md.stripTopLevelTags = False

def unmark(text):
    return __md.convert(text)

def extract_rules_text(rules):
    rules_text = []
    count = 1
    for r in rules:
        if r['kind'] == 'link':
            continue
        cleaned_rule = unmark(r['description']).strip()
        rules_text.append(str(count) + ". " + cleaned_rule)
        count += 1
    return rules_text

def make_user_dict(string):
    return {"role": "user", "content": string}

def make_assistant_dict(string):
    return {"role": "assistant", "content": string}

def get_rules_string(rules_text):
    return "\n".join(rules_text)

def read_moderated_comments(politics_f):
    body_to_decision = {}
    with open(politics_f, 'r') as infile:
        reader = csv.reader(infile)
        next(reader)
        for row in reader:
            body = row[0]
            moderated = int(row[2])
            body_to_decision[body] = moderated
    return body_to_decision

def read_rules_f(subreddit_rules_f):
    subreddit_to_rules = {}
    subreddit_to_description = {}
    for l in open(subreddit_rules_f, 'r'):
        l = l.strip()
        data = json.loads(l)
        subreddit = data['subreddit']
        description = data['description']
        rules = data['rules']

        rules_text = extract_rules_text(rules)
        rules_string = get_rules_string(rules_text)

        subreddit_to_description[subreddit] = description
        subreddit_to_rules[subreddit] = rules_string
    
    return subreddit_to_description, subreddit_to_rules

def main():
    subreddit_rules_f = sys.argv[1]
    subreddit_to_description, subreddit_to_rules = read_rules_f(subreddit_rules_f)
  
    #print(subreddit_to_description.keys())
    for subreddit, description in subreddit_to_description.items():
        f_name = "rule_dataset/"+subreddit+".csv"
        body_to_decision = read_moderated_comments(f_name)
        
        description = subreddit_to_description[subreddit]
        rules_string = subreddit_to_rules[subreddit]
    
        base_chat = []
        first_string = f'''You are a helpful content moderation assistant for the online subreddit called {subreddit}. The subreddit has the following description: "{description}".
        
Here are the rules for the community:

{rules_string}'''
        #print(first_string)
        base_chat.append(make_user_dict(first_string))
        base_chat.append(make_assistant_dict("OK, I understand the rules of the community."))
        second_string = '''Consider the following comment: "You are a stupid idiot."'''
        base_chat.append(make_user_dict(second_string))
        base_chat.append(make_assistant_dict("OK, I understand the comment."))

        third_string = '''Return a JSON object with five fields, "would_moderate," that is either "yes" or "no" depending on if you would remove this comment from the subreddit, "rule" which is the text of the rule being violated, "rule_nums" which are a comma-separated list of rules being violated, "explanation" which contains a reason for your decision, and "rating" which is a score from 1 to 5 depending on how violative the comment is based on the rules.'''
        sample_json = '''{"would_moderate": "yes", "rule": "<rule_being_violated>", "rule_nums": "5,6,7", "explanation": "<explanation>", "rating": 3}'''
        
        base_chat.append(make_user_dict(third_string))
        base_chat.append(make_assistant_dict(sample_json))

        mod_chat = copy.deepcopy(base_chat)
        sys.stderr.write("Processing subreddit: " + subreddit + "\n")
        sys.stderr.write("Total comments: " + str(len(body_to_decision)) + "\n")
        count = 1

        for b, decision in body_to_decision.items():
            if count % 100 == 0:
                sys.stderr.write("Processed " + str(count) + " records.\n")
                sys.stderr.write("Sleeping...\n")
                sys.stderr.flush()
                time.sleep(20)
            second_string = f'''Consider the following comment: "{b}"'''
            mod_chat.append(make_user_dict(second_string))
            mod_chat.append(make_assistant_dict("OK, I understand the comment."))
            third_string = '''Return a JSON object with five fields, "would_moderate," that is either "yes" or "no" depending on if you would remove this comment from the subreddit, "rule" which is the text of the rule being violated, "rule_nums" which are a comma-separated list of rules being violated, "explanation" which contains a reason for your decision, and "rating" which is a score from 1 to 5 depending on how violative the comment is based on the rules.'''
            mod_chat.append(make_user_dict(third_string))
            #print(mod_chat) 
            try:
                completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=mod_chat, temperature=0)
            except Exception as e:
                sys.stderr.write("Something went wrong...\n")
                sys.stderr.write("Sleeping...\n")
                sys.stderr.write(str(e) + "\n")
                sys.stderr.flush()
                mod_chat = copy.deepcopy(base_chat)
                time.sleep(10)
                continue
            
            out = {}

            out['comment'] = b
            out['decision'] = decision
            out['subreddit'] = subreddit
            out['openai_completion'] = completion
            
            # Reset mod chat
            mod_chat = copy.deepcopy(base_chat)
            print(json.dumps(out))
            count += 1
            
if __name__ == "__main__":
    main()
