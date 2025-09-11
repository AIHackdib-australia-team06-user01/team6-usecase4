from ism_control_assessment_tool import run_assessment
import json
import os


def main():
    data_path = os.path.join(os.path.dirname(__file__), "../data/data.json")
    with open(data_path, "r") as f:
        data = json.load(f)
    #list through ISM controls
    for ism in data:
        key =(list(ism.keys())[0])
        description = ism[key]["Description"]
        # Agent request
        state, _, _ = run_assessment(ism, description)
        print(key + " : " + state)
        # print(f"Assessment for ISM {ism}: {result}")

if __name__ == "__main__":
    main()
