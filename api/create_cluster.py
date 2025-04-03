import os
from tqdm.auto import tqdm

import llm_utils
import neo4j_utils


def create_cluster(input_data, input_type, cluster_name, cluster_type):

    skill_list = llm_utils.extract_skill(input_data=input_data,
                                            input_type=input_type)
        
    taxonomy_dict = llm_utils.extract_taxonomy(word_list=skill_list)

    neo4j_utils.create_cluster(cluster_name=cluster_name,
                            cluster_type=cluster_type,
                            skill_list=list(taxonomy_dict.keys()),
                            taxonomy_dict=taxonomy_dict)


# for e in tqdm(os.listdir('tmp/jobs')):
#     try:
#         create_cluster(f'tmp/jobs/{e}', 'file', e.split('.')[0], 'Job')
#     except:
#         print('failed', e)

for e in tqdm(os.listdir('tmp/courses')[1:]):
    if e == '.DS_Store':
        continue
    for k in tqdm(os.listdir(f'tmp/courses/{e}'), desc=f'Extract {e}'):
        try:
            create_cluster(f'tmp/courses/{e}/{k}', 'file', e, 'Course')
        except:
            print('failed', e, k)