from fastapi import FastAPI, HTTPException, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import os
import uuid
import pandas as pd
from typing import Optional

import llm_utils
import neo4j_utils


app = FastAPI()


# Create temporary directory
UPLOAD_DIRECTORY = "tmp/uploads"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

COMPILED_GRAPH_DIRECTORY = "tmp/compiled_graphs"
os.makedirs(COMPILED_GRAPH_DIRECTORY, exist_ok=True)


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
    

def make_course_job_dataframe(all_course_job_paths):
    rows = []

    for k in all_course_job_paths.keys():
        for v in all_course_job_paths[k]:
            relations = list(v.get('p'))

            path = []

            path.append(relations[0].start_node.get('name'))

            for r in relations:
                start_node = r.start_node.get('name')
                end_node = r.end_node.get('name')

                if path[-1] != end_node:
                    path.append(f'{r.type}>')
                    path.append(end_node)
                else:
                    path.append(f'{r.type}<')
                    path.append(start_node)

            rows.append({
                'type': k,
                'job': path[0],
                'job_require': path[2],
                'course_acquire': path[-3],
                'course': path[-1],
                'path': path
            })

    return pd.DataFrame(rows)


def make_skill_job_dataframe(all_skill_job_paths):
    rows = []

    for k in all_skill_job_paths.keys():
        for v in all_skill_job_paths[k]:
            relations = list(v.get('p'))

            path = []

            path.append(relations[0].start_node.get('name'))

            for r in relations:
                start_node = r.start_node.get('name')
                end_node = r.end_node.get('name')

                if path[-1] != end_node:
                    path.append(f'{r.type}>')
                    path.append(end_node)
                else:
                    path.append(f'{r.type}<')
                    path.append(start_node)

            rows.append({
                'type': k,
                'job': path[0],
                'job_require': path[2],
                'skill': path[-1],
                'path': path
            })

    return pd.DataFrame(rows)


def make_job_requirement_dataframe(each_job_requirements):
    rows = []

    for path in each_job_requirements:
        rows.append({
            "job": path["job"]["name"],
            "skill": path["skill"]["name"]
        })

    return  pd.DataFrame(rows)


@app.post("/compile_graph")
async def compile_graph():
    try:
        # Precompute all course to job paths
        all_course_job_paths = neo4j_utils.find_all_possible_course_job_path()
        df = make_course_job_dataframe(all_course_job_paths)
        df.to_csv(os.path.join(COMPILED_GRAPH_DIRECTORY, "course_job.csv"), index=False)

         # Precompute all skill to job paths
        all_skill_job_paths = neo4j_utils.find_all_possible_skill_job_path()
        df = make_skill_job_dataframe(all_skill_job_paths)
        df.to_csv(os.path.join(COMPILED_GRAPH_DIRECTORY, "skill_job.csv"), index=False)

         # Get each job requirements
        each_job_requirements = neo4j_utils.find_each_job_requirement()
        df = make_job_requirement_dataframe(each_job_requirements)
        df.to_csv(os.path.join(COMPILED_GRAPH_DIRECTORY, "job_requirement.csv"), index=False)

        return {"message": "Graph compiled successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error compiling graph: {e}")


@app.post("/personalized_recommendation")
async def personalized_recommendation(courses: list[str] = Form(...),
                                      skills: list[str] = Form(...)):
    
    job_requirement_csv_path = os.path.join(COMPILED_GRAPH_DIRECTORY, "job_requirement.csv")
    course_job_csv_path = os.path.join(COMPILED_GRAPH_DIRECTORY, "course_job.csv")
    skill_job_csv_path = os.path.join(COMPILED_GRAPH_DIRECTORY, "skill_job.csv")

    # Compile graph first if the CSV files do not exist
    if not os.path.exists(job_requirement_csv_path) or \
       not os.path.exists(course_job_csv_path) or \
       not os.path.exists(skill_job_csv_path):
        compile_graph()

    rows1 = []
    rows2 = []
    skill_course_dict = {}

    job_requirement_df = pd.read_csv(job_requirement_csv_path)
    job_fulfillment_dict = {}
    for k, g in job_requirement_df.groupby('job'):
        job_fulfillment_dict[k] = {skill:False for skill in g['skill']}
    
    course_job_df = pd.read_csv(course_job_csv_path)
    for k, g in course_job_df.groupby(['course', 'job']):
        course, job = k
        if course in courses:
            for idx, row in g.iterrows():
                job_fulfillment_dict[job][row['job_require']] = True

                # sankey data 1: multi-hop
                rows1.append({
                    'job': job,
                    'course': course,
                    'data': (course, row['course_acquire'], 1)
                })

                if row['course_acquire'] != row['job_require']:
                    rows1.append({
                    'job': job,
                    'course': course,
                    'data': (row['course_acquire'], row['job_require'], 1)
                })
                    
                rows1.append({
                    'job': job,
                    'course': course,
                    'data': (row['job_require'], job, 1)
                })

                # sankey data 2: single-hop
                rows2.append({
                    'job': job,
                    'data': (course, row['job_require'], 1)
                })
                rows2.append({
                    'job': job,
                    'data': (row['job_require'], job, 1)
                })

                if row['job_require'] not in skill_course_dict:
                    skill_course_dict[row['job_require']] = set()
                skill_course_dict[row['job_require']].add(course)


    skill_job_df = pd.read_csv(skill_job_csv_path)
    for k, g in skill_job_df.groupby(['skill', 'job']):
        skill, job = k
        if skill in skills:
            for idx, row in g.iterrows():
                job_fulfillment_dict[job][row['job_require']] = True

                # sankey data 1: multi-hop
                rows1.append({
                    'job': job,
                    'course': "_SKILL",
                    'data': (skill + ' ', row['job_require'], 1)
                })
                    
                rows1.append({
                    'job': job,
                    'course': "_SKILL",
                    'data': (row['job_require'], job, 1)
                })

                # sankey data 2: single-hop
                rows2.append({
                    'job': job,
                    'data': (skill + ' ', row['job_require'], 1)
                })
                    
                rows2.append({
                    'job': job,
                    'data': (row['job_require'], job, 1)
                })

    # Ranking jobs based on skill fulfillment
    job_scores = {}
    for job, skill_fulfillments in job_fulfillment_dict.items():
        total_skills = len(skill_fulfillments)
        fulfilled_skills = sum(skill_fulfillments.values())

        if total_skills > 0:
            job_scores[job] = fulfilled_skills / total_skills
        else:
            job_scores[job] = 0

    ranked_jobs = sorted(job_scores.items(), key=lambda item: item[1], reverse=True)

    return {
        "job_fulfillment": job_fulfillment_dict,
        "ranked_jobs": ranked_jobs,
        'multi_hop_sankey_df': pd.DataFrame(rows1),
        'single_hop_sankey_df': pd.DataFrame(rows2),
        'skill_course_dict': skill_course_dict
    }