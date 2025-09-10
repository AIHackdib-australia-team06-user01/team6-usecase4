import pandas as pd
import json

filepath = "./blueprint.xlsx"

df = pd.read_excel(filepath, sheet_name=1, header=1)
df = df.iloc[:, 1:]

# print(df.head())
# print(df.iloc[4])


filtered_df = df[(df["ML2"] == "Yes") & (df["Technology addressed"] == "Yes")]

json_list = []
for _, row in filtered_df.iterrows():
    entry = {
        row["Identifier"]: {
            "Description": row["Description"]
        }
    }
    json_list.append(entry)

print(json.dumps(json_list, indent=2))

# Save to data.json
with open("data.json", "w") as f:
    json.dump(json_list, f, indent=2)