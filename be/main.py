from fastapi import FastAPI
from typing import List
from pydantic import BaseModel

app = FastAPI()

class StringList(BaseModel):
    items: List[str]

@app.post("/conduct-assessment")
async def process_strings(string_list: StringList):
    return {"report_files": string_list.items}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
