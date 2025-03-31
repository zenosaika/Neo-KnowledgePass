import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from tqdm.auto import tqdm

# Load environment variables
load_dotenv()

# Neo4j Configuration
uri = os.getenv("NEO4J_URI")
auth = ("neo4j", os.getenv("NEO4J_PASSWORD"))


def merge_triple(tx, subject: str, predicate: str, object: str, subject_type: str, object_type: str):
    tx.run(
        f"MERGE (s:{subject_type} {{name: $subject}}) "
        f"MERGE (o:{object_type} {{name: $object}}) "
        f"MERGE (s)-[:{predicate}]->(o)",
        subject=subject,
        object=object
    )

def create_cluster(cluster_name, cluster_type, skill_list, taxonomy_dict):
    with GraphDatabase.driver(uri, auth=auth) as driver:
        with driver.session() as session:

            # level 1 relation
            for skill in tqdm(skill_list, desc=f'Add lv.1 relation of {cluster_name}'):
                session.execute_write(merge_triple,
                                      subject=cluster_name,
                                      predicate='include' if cluster_type == 'Course' else 'require',
                                      object=skill,
                                      subject_type=cluster_type,
                                      object_type='Skill')
                
            # level 2 relation
            for skill, v in tqdm(taxonomy_dict.items(), desc=f'Add lv.2 relation of {cluster_name}'):
                superclasses = v['is_a']
                associated_terms = v['associate_to']
                used_knowledges = v['use_knowledge_of']
                synonyms = v['synonyms']

                for superclass in superclasses:
                    session.execute_write(merge_triple,
                                        subject=skill,
                                        predicate='is_a',
                                        object=superclass,
                                        subject_type='Skill',
                                        object_type='Skill')
                    
                for associated_term in associated_terms:
                    session.execute_write(merge_triple,
                                        subject=skill,
                                        predicate='associate_to',
                                        object=associated_term,
                                        subject_type='Skill',
                                        object_type='Skill')
                
                for used_knowledge in used_knowledges:
                    session.execute_write(merge_triple,
                                        subject=skill,
                                        predicate='use_knowledge_of',
                                        object=used_knowledge,
                                        subject_type='Skill',
                                        object_type='Skill')

                for synonym in synonyms:
                    session.execute_write(merge_triple,
                                        subject=synonym,
                                        predicate='synonym',
                                        object=skill,
                                        subject_type='Skill',
                                        object_type='Skill')
                    
def _find_all_possible_course_job_path(tx):
    query = (
        "MATCH (course:Course)-[:include]->(course_skill:Skill)-[:relate]->(rep_skill:Skill)<-[:relate]-(job_skill:Skill)<-[:require]-(job:Job) "
        "RETURN course, course_skill, rep_skill, job_skill, job"
    )
    result = tx.run(query)
    return [record for record in result]

def find_all_possible_course_job_path():
    with GraphDatabase.driver(uri, auth=auth) as driver:
        with driver.session() as session:
            result = session.execute_read(_find_all_possible_course_job_path)
            return result
        
def _find_all_possible_skill_job_path(tx):
    query = (
        "MATCH (skill:Skill)-[:relate]->(rep_skill:Skill)<-[:relate]-(job_skill:Skill)<-[:require]-(job:Job) "
        "RETURN skill, rep_skill, job_skill, job"
    )
    result = tx.run(query)
    return [record for record in result]

def find_all_possible_skill_job_path():
    with GraphDatabase.driver(uri, auth=auth) as driver:
        with driver.session() as session:
            result = session.execute_read(_find_all_possible_skill_job_path)
            return result
        
def _find_all_job_requirement(tx):
    query = (
        "MATCH (job_skill:Skill)<-[:require]-(job:Job) "
        "RETURN job_skill, job"
    )
    result = tx.run(query)
    return [record for record in result]

def find_all_job_requirement():
    with GraphDatabase.driver(uri, auth=auth) as driver:
        with driver.session() as session:
            result = session.execute_read(_find_all_job_requirement)
            return result
        
def _get_all_skills(tx):
    query = (
        "MATCH (skill:Skill) "
        "RETURN skill"
    )
    result = tx.run(query)
    return [record for record in result]

def get_all_skills():
    with GraphDatabase.driver(uri, auth=auth) as driver:
        with driver.session() as session:
            result = session.execute_read(_get_all_skills)
            return result