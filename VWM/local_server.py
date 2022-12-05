"""
Aux module for local usage/debug/development, frontend sends requests here.

logic module uses data prepared and uploaded to AWS S3 and AWS DynamoDB
"""
import logging

import aiohttp.web
import aiohttp_cors

import logic


async def get_dataset_names(_: aiohttp.web.Request) -> aiohttp.web.Response:
    """
    A view which wraps logic.dataset_names()
    """
    try:
        return aiohttp.web.json_response(await logic.dataset_names())
    except Exception as exception:
        logging.exception(exception)

    raise aiohttp.web.HTTPBadRequest


async def handle_query(request: aiohttp.web.Request) -> aiohttp.web.Response:
    """
    A view which wraps logic.process_query(),
    catches exceptions, returns a response.
    """
    try:
        return aiohttp.web.json_response(
            await logic.process_query(
                dataset=request.match_info["dataset"],
                query=request.match_info["query"],
            )
        )
    except ValueError as error:
        error_text = str(error)
    except Exception as exception:
        logging.exception(exception)
        error_text = str(exception)

    raise aiohttp.web.HTTPBadRequest(text=error_text)


async def get_file_exposed_url(
    request: aiohttp.web.Request,
) -> aiohttp.web.Response:
    try:
        return aiohttp.web.Response(
            text=await logic.publish_file_for_5_minutes_and_return_url(
                dataset=request.match_info["dataset"],
                filename=request.match_info["filename"],
            )
        )
    except Exception as exception:
        logging.exception(exception)
        error_text = str(exception)

    raise aiohttp.web.HTTPBadRequest(text=error_text)


def main() -> None:
    """
    Local server for frontend.
    For local debug/development. For production AWS Lambda is used.
    """
    logging.basicConfig(level=logging.INFO)

    app = aiohttp.web.Application()

    app.add_routes(
        (
            aiohttp.web.get("/dataset_names", get_dataset_names),
            aiohttp.web.get(r"/query/{dataset}/{query}", handle_query),
            aiohttp.web.get(
                r"/publish_file/{dataset}/{filename}", get_file_exposed_url
            ),
        )
    )

    # Configure default CORS settings.
    cors = aiohttp_cors.setup(
        app,
        defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True, expose_headers="*", allow_headers="*",
            )
        },
    )

    # Configure CORS on all routes.
    for route in list(app.router.routes()):
        cors.add(route)

    aiohttp.web.run_app(
        app, host="127.0.0.1", port=8000, reuse_port=True,
    )


if __name__ == "__main__":
    main()
