from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel
from fastapi.responses import FileResponse
import os
from ssp_excel_updater import update_ssp_excel
from ism_description_svc import get_ism_description
import sys
sys.path.append('/workspaces/team6-usecase4')
from agents.ism_control_assessment_tool import assess_ism_control


app = FastAPI()

# Allow CORS for all origins, methods, and headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Example usage paths (update as needed)

import datetime
json_path = "./data/results.json"
excel_path = "./data/Blueprint-System-Security-Plan-Annex-Template-(June 2025).xlsx"

def get_output_filename():
    now = datetime.datetime.now()
    return f"System-Security-Plan-{now.strftime('%d-%m-%y-%H-%M')}.xlsx"

def get_output_path(filename: str):
    output_dir = "./output"
    os.makedirs(output_dir, exist_ok=True)
    return os.path.join(output_dir, filename)

class StringList(BaseModel):
    items: List[str]


@app.post("/conduct-assessment")
async def process_strings(string_list: StringList):

    results = []

    for ism in string_list.items:
        desc = get_ism_description(ism)
        try:
            
            status, policies = await assess_ism_control(
                ism_title=ism,
                ism_description=desc,
                policy_file="./data/asdbpsc-dsc-entra.txt"
            )
            result = {"ism-control": ism, "result": status, "comment": ", ".join(policies)}
            results.append(result)
            print(f"Assessment for ISM {ism}: {result}")
        except Exception as e:
            print(f"Error assessing ISM {ism}: {str(e)}")
            result = {"ism-control": ism, "result": "Not Assessed", "comment": f"Error: {str(e)}"}
            results.append(result)


    filename = get_output_filename()
    output_path = get_output_path(filename)
    update_ssp_excel(json_path, excel_path, output_path)
    return {"output_file": filename, "assessments": results}


@app.get("/download-report")
def download_latest_report(filename: str):
    output_dir = "./output"
    file_path = os.path.join(output_dir, filename)
    if not os.path.exists(file_path):
        return Response(content="No report found.", status_code=404)
    return FileResponse(file_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=os.path.basename(file_path))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

