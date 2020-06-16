from typing import Dict, Any

import asyncio
import json
import logging
import urllib.parse

import logic

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], _: Any) -> Dict[str, Any]:

    resource_name = event.get("resource", "")
    logging.info("Resource: %s", resource_name)
    logging.info("Path parameters: %s", event.get("pathParameters"))

    status_code = 200

    if resource_name == "/dataset_names":
        try:
            response = json.dumps(asyncio.run(logic.dataset_names()))
        except Exception as exception:
            logging.exception(exception)
            logging.exception(exception)
            status_code = 400
            response = str(exception)

    elif resource_name == "/query/{dataset}/{query}":
        try:
            response = json.dumps(
                asyncio.run(
                    logic.process_query(
                        dataset=urllib.parse.unquote(
                            event["pathParameters"]["dataset"]
                        ),
                        query=urllib.parse.unquote(
                            event["pathParameters"]["query"]
                        ),
                    )
                )
            )
        except Exception as exception:
            logging.exception(exception)
            logging.exception(exception)
            status_code = 400
            response = str(exception)

    elif resource_name == "/publish_file/{dataset}/{filename}":
        try:
            response = json.dumps(
                asyncio.run(
                    logic.publish_file_for_5_minutes_and_return_url(
                        dataset=urllib.parse.unquote(
                            event["pathParameters"]["dataset"]
                        ),
                        filename=urllib.parse.unquote(
                            event["pathParameters"]["filename"]
                        ),
                    )
                )
            )
        except Exception as exception:
            logging.exception(exception)
            status_code = 400
            response = str(exception)
    else:
        status_code = 400
        response = "Unknown route"

    return {
        "statusCode": status_code,
        "body": response,
        "headers": {"Access-Control-Allow-Origin": "*"},
    }
