swagger_config = {
    "openapi": "3.0.2",
    "swagger_version": "3.0",
    "disable_swagger": True,
    "title": "IRI+ API",
    "version": "1.0.0",
    "uiversion": 3,
    "static_url_path": "/flasgger_static",
    "specs_route": "/api/docs/",
    "headers": [],
    "parse": True,
    "yml_header": True,
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/api/docs/apispec_1.json',
            "rule_filter": lambda rule: True,  # all in
            "model_filter": lambda tag: True,  # all models
        }
    ],
}
