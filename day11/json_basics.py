import json

model_text="""
{"action":"search_paper",
"arguments":{"keyword":"Agent"}
}

"""

print(type(model_text))
decision=json.loads(model_text)
print(type(decision))