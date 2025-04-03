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
                synonyms = v['synonyms']
                superclasses = v['subclass_of']
                knowledges = v['use_knowledge_of']

                for superclass in superclasses:
                    session.execute_write(merge_triple,
                                        subject=skill,
                                        predicate='subclass_of',
                                        object=superclass,
                                        subject_type='Skill',
                                        object_type='Skill')
                    
                for knowledge in knowledges:
                    session.execute_write(merge_triple,
                                        subject=skill,
                                        predicate='use_knowledge_of',
                                        object=knowledge,
                                        subject_type='Skill',
                                        object_type='Skill')

                for synonym in synonyms:
                    session.execute_write(merge_triple,
                                        subject=synonym,
                                        predicate='synonym',
                                        object=skill,
                                        subject_type='Skill',
                                        object_type='Skill')

def execute_read_query(query):
    def _execute_read_query(tx):
        result = tx.run(query)
        return [record for record in result]
    
    with GraphDatabase.driver(uri, auth=auth) as driver:
        with driver.session() as session:
            result = session.execute_read(_execute_read_query)
            return result

def find_all_possible_course_job_path():
    queries = {
        'single_hop_synonym': (
                "MATCH p = (:Job)-[:require]->(:Skill)<-[:include]-(:Course) "
                "RETURN p"
            ),
        'multi_hop_synonym': (
                "MATCH p = (:Job)-[:require]->(:Skill)-[:synonym*]-(:Skill)<-[:include]-(:Course) "
                "RETURN p"
            ),
        # 'subclass_of': (
        #         "MATCH p = (:Job)-[:require]->(:Skill)-[:subclass_of*..2]->(:Skill)<-[:include]-(:Course) "
        #         "RETURN p"
        #     ),
        # 'subclass_of': (
        #         "MATCH p = (:Job)-[:require]->(:Skill)-[:subclass_of*..2]-(:Skill)<-[:include]-(:Course) "
        #         "RETURN p"
        #     ),
        # 'use_knowledge_of': (
        #         "MATCH p = (:Job)-[:require]->(:Skill)-[:use_knowledge_of*..2]-(:Skill)<-[:include]-(:Course) "
        #         "RETURN p"
        #     ),
    }

    results = {}
    for k, query in queries.items():
        result = execute_read_query(query)
        results[k] = result

    return results

def find_all_possible_skill_job_path():
    queries = {
        'single_hop_synonym': (
                "MATCH p = (:Job)-[:require]->(:Skill) "
                "RETURN p"
            ),
        'multi_hop_synonym': (
                "MATCH p = (:Job)-[:require]->(:Skill)-[:synonym*]-(:Skill) "
                "RETURN p"
            ),
        # 'subclass_of': (
        #         "MATCH p = (:Job)-[:require]->(:Skill)-[:subclass_of*..2]->(:Skill) "
        #         "RETURN p"
        #     ),
        # 'subclass_of': (
        #         "MATCH p = (:Job)-[:require]->(:Skill)-[:subclass_of*..2]-(:Skill) "
        #         "RETURN p"
        #     ),
        # 'use_knowledge_of': (
        #         "MATCH p = (:Job)-[:require]->(:Skill)-[:use_knowledge_of*..2]-(:Skill) "
        #         "RETURN p"
        #     ),
    }

    results = {}
    for k, query in queries.items():
        result = execute_read_query(query)
        results[k] = result

    return results

def find_each_job_requirement():
    query = (
        "MATCH (skill:Skill)<-[:require]-(job:Job) "
        "RETURN skill, job"
    )

    result = execute_read_query(query)
    return result

def get_all_skills():
    query = (
        "MATCH (skill:Skill) "
        "RETURN skill"
    )

    result = execute_read_query(query)
    return result

def node_to_text():
    queries = {
        'is synonym of': (
                "MATCH p = (:Skill)-[:synonym]->(:Skill) "
                "RETURN p"
            ),
        'is subclass of': (
                "MATCH p = (:Skill)-[:subclass_of]->(:Skill) "
                "RETURN p"
            ),
        'use knowledge of': (
                "MATCH p = (:Skill)-[:use_knowledge_of]->(:Skill) "
                "RETURN p"
            ),
    }

    results = {}
    for k, query in queries.items():
        result = execute_read_query(query)
        results[k] = result

    return results