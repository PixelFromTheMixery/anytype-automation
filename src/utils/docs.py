"""Fast API doc variables"""

DESCRIPTION = """
### Sections
"""

TAGS = [
    {"name": "general", "description": "Endpoints for general use"},
    {"name": "tasks", "description": "Endpoints for task automation"},
    {"name": "journal", "description": "Endpoints for journal automation"},
    {"name": "scheduled", "description": "Which endpoints are also scheduled jobs"},
    {"name": "spaces", "description": "Endpoints for space automation"},
    {
        "name": "timetagger",
        "description": "Endpoints for timetagger integration",
        "externalDocs": {
            "description": "TimeTagger docs",
            "url": "https://timetagger.readthedocs.io/en/latest/",
        },
    },
    {
        "name": "anytype",
        "description": "Endpoints for anytype interaction",
        "externalDocs": {
            "description": "Anytype API docs",
            "url": "https://developers.anytype.io/docs/reference/2025-11-08",
        },
    },
]
