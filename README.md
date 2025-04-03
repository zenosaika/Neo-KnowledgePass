# Neo-KnowledgePass

### Installation
```
virtualvenv venv
source venv/bin/activate

pip install -r requirements.txt
```

### Create Environment File (.env)
```
NEO4J_URI=
NEO4J_PASSWORD=
GOOGLE_API_KEY=
```

### Run Neo4j (Graph Database) in Docker
```
docker run \
    --restart always \
    --publish=7474:7474 --publish=7687:7687 \
    --env NEO4J_AUTH=neo4j/<your_password> \
    --volume=<path_to_mount_folder>:/data \
    neo4j:2025.03.0
```

### Run FastAPI
```
fastapi dev main.py --port 8081
```