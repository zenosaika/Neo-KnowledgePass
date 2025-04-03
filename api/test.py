import llm_utils
import neo4j_utils

cluster_name = 'AI Engineer'
cluster_type = 'Job'
input_data = '''Roles and Responsibilities: 

Analyze large datasets to extract meaningful insights and build predictive models.
Develop and implement machine learning algorithms and AI solutions.
Collaborate with cross-functional teams to integrate AI solutions into business processes.
Support the development of data-driven strategies and decision-making processes.
Participate in management training sessions and shadow senior managers.
Present findings and recommendations to stakeholders.
Preferred Qualifications: 

Bachelor's degree in data science, Computer Science, Statistics, Data Management or a related field.
Strong understanding of machine learning algorithms, statistical models, and data analysis techniques.
Proficiency in programming languages such as Python, R, and SQL.
Experience with data visualization tools (e.g., Tableau, Power BI).
Excellent analytical, problem-solving, and communication skills.
Eagerness to learn and adapt in a fast-paced environment.
Previous internship or project experience in data science or AI is a plus.
What We Offer:

Hands-on training and mentorship from industry experts.
Opportunity to work on cutting-edge AI projects.
Collaborative and inclusive work culture.
Career growth and development opportunities.'''
input_type = 'text'

print('start extracting skill list')
skill_list = llm_utils.extract_skill(input_data=input_data,
                                    input_type=input_type)

print('start extracting taxonomy')      
taxonomy_dict = llm_utils.extract_taxonomy(word_list=skill_list)

print('start creating cluster')
neo4j_utils.create_cluster(cluster_name=cluster_name,
                                cluster_type=cluster_type,
                                skill_list=list(taxonomy_dict.keys()),
                                taxonomy_dict=taxonomy_dict)