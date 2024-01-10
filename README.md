# llm-content-mod
Datasets and code for studying LLMs and Content Moderation

# Datasets
 - The data/ folder contains all the subreddit specific data and toxic content data we curated to conduct our experiments 
 - rule_moderation/ contains balanced datasets for each subreddit we studied. In particular:
    - subreddit_rules_w_description.jsonl contains a description and the rule-string we used for prompting each LLM 
    - subreddit_balanced_datasets contains the actual balanced data files for each subreddit
 - toxic_content/ contains 10k_balanced_sample.jsonl, which is the data file with balanced toxic/nontoxic comments curated for our toxic content evaluation 

# Scripts
 - The scripts/ folder has all the base scripts we used to run our data through various commercial models.
 - scripts/is_toxic_*.py has all the scripts for toxic content detection
 - scripts/rule_based_moderation.py has the code for evaluating rule-based decisions per subreddit
