from fastapi import FastAPI, HTTPException, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import os
import uuid
from typing import Optional

import llm_utils
import neo4j_utils


app = FastAPI()


# Create temporary directory
UPLOAD_DIRECTORY = "tmp/uploads"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    # Allow requests from your frontend's origin.
    allow_origins=["http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/create_cluster")
async def create_cluster(
    cluster_name: str = Form(...),
    cluster_type: str = Form("Course"),
    text_input: Optional[str] = Form(None),
    file_input: Optional[UploadFile] = File(None)
):
    
    input_data = None
    input_type = None

    if text_input:
        input_data = text_input
        input_type = "text"
    elif file_input:
        file_id = str(uuid.uuid4())
        file_path = os.path.join(UPLOAD_DIRECTORY, f"{file_id}_{file_input.filename}")

        # Save uploaded file to local storage
        try:
            with open(file_path, "wb") as f:
                while contents := await file_input.read(1024 * 1024): # Read in chunks
                    f.write(contents)
            input_data = file_path
            input_type = "file"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error uploading file: {e}")
    else:
        raise HTTPException(status_code=400, detail="Either text or file input is required")
    
    # Graph construction pipeline
    try:
        skill_list = llm_utils.extract_skill(input_data=input_data,
                                            input_type=input_type)
        
        taxonomy_dict = llm_utils.extract_taxonomy(word_list=skill_list)

        neo4j_utils.create_cluster(cluster_name=cluster_name,
                                cluster_type=cluster_type,
                                skill_list=list(taxonomy_dict.keys()),
                                taxonomy_dict=taxonomy_dict)
        
        return {"message": "Cluster created successfully", "file_path": input_data if input_type == "file" else None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating cluster: {e}")