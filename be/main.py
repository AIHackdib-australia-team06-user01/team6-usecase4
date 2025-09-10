from fastapi import FastAPI
from typing import List
from pydantic import BaseModel
import os
from ssp_excel_updater import update_ssp_excel

app = FastAPI()

# Example usage paths (update as needed)

import datetime
json_path = "./data/results.json"
excel_path = "./data/Blueprint-System-Security-Plan-Annex-Template-(June 2025).xlsx"
def get_output_path():
    now = datetime.datetime.now()
    filename = f"System-Security-Plan-{now.strftime('%d-%m-%y-%H-%M')}.xlsx"
    output_dir = "./output"
    os.makedirs(output_dir, exist_ok=True)
    return os.path.join(output_dir, filename)

class StringList(BaseModel):
    items: List[str]


@app.post("/conduct-assessment")
async def process_strings(string_list: StringList):
    output_path = get_output_path()
    update_ssp_excel(json_path, excel_path, output_path)
    return {"output_file": output_path}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

