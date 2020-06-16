"""
A module which implements Boolean model logic.
"""
from typing import Dict, List, Set, Union

import logging
import os
import time

import aiobotocore
import nltk
import pyeda.boolalg.expr


S3_BUCKET = os.getenv("BOOLEAN_MODEL_S3_BUCKET") or "boolean-model"


async def dataset_names() -> List[str]:
    """
    Returns available datasets (each has a folder with files on AWS S3 and
    2 tables on AWS DynamoDB, one for mapping files to ids and other mapping
    terms/words to ids of files where they can be found.

    :return: list of dataset names
    :rtype: List[str]
    """
    session = aiobotocore.get_session()

    async with session.create_client("dynamodb") as dynamodb_client:
        tables = await dynamodb_client.list_tables()

    table_names: List[str] = tables["TableNames"]

    return list(
        map(
            lambda x: x.rstrip("_terms"),
            filter(lambda x: x.endswith("_terms"), table_names),
        )
    )


async def process_query(
    dataset: str, query: str
) -> Dict[str, Union[str, float, List[str]]]:
    """
    :raises ValueError: on not existing dataset
        or when parser cannot parse the query
    """

    if dataset not in await dataset_names():
        raise ValueError(
            "There is no such dataset. Refusing to process the query."
        )

    logging.debug("Raw query: %s", query)

    # PyEDA doesn't work with and/or/not operators in natural language,
    # need to escape them to mathematical symbols first
    escaped_query = (
        query.lower()
        .replace(" and ", " & ")
        .replace(" or ", " | ")
        .replace("not ", " ~ ")
    )
    # FIXME re sub, instead of replace (could be parentheses)

    logging.debug("Escaped query: %s", escaped_query)

    try:
        expr = pyeda.boolalg.expr.expr(escaped_query, simplify=True)
        logging.debug("Parsed expr: %s", expr)
    except pyeda.parsing.boolexpr.Error as error:
        logging.exception(error)
        raise ValueError("Cannot parse the query")

    # using PorterStemmer
    stemmer = nltk.stem.PorterStemmer()

    # TODO maybe try CNF?
    dnf = expr.to_dnf()
    logging.debug("DNF: %s", dnf)

    # AWS session
    session = aiobotocore.get_session()

    fetched_terms: Dict[str, Set[int]] = {}

    # first fetch all unique terms from the DynanoDB NoSQL database
    async with session.create_client("dynamodb") as dynamodb_client:

        for term in map(stemmer.stem, set(map(str, dnf.inputs))):
            item = await dynamodb_client.get_item(
                TableName=f"{dataset}_terms", Key={"term": {"S": term}}
            )
            try:
                # DynanoDB returns numbers in string format, so we need
                # first to cast it
                fetched_terms[term] = set(
                    map(int, item["Item"]["files"]["NS"])
                )
            except KeyError:
                fetched_terms[term] = set()

    # set of filenames
    final = set()

    begin = time.time()
    for sat in dnf.satisfy_all():

        # create temporary set for multiple ANDs
        # sat dict with 0s and 1s will be sorted, so firstly
        # 1s will be added to temp set (with intersection) and
        # then 0s will be substracted from the set.
        #
        # after each sat pair temp set will be added to final set
        # (OR of multiple clauses in DNF)
        temp: Set[int] = set()

        for symbol, value in reversed(
            sorted(sat.items(), key=lambda item: item[1])
        ):
            logging.debug("temp: %s", temp)
            logging.debug(f"{symbol} is {value}")

            contents = fetched_terms[stemmer.stem(str(symbol))]

            if value == 1:
                if len(temp) != 0:
                    logging.debug("temp was empty")
                    temp.intersection_update(contents)
                # FIXME elif with flag?
                else:
                    temp = contents

                logging.debug("%s is 1. Added to temp %s", symbol, contents)
            else:
                temp -= contents
                logging.debug(
                    "%s is 0. Removed from temp %s", symbol, contents
                )

        logging.debug("temp: %s", temp)
        final.update(temp)
        logging.debug("final: %s", final)

    # set names of files
    response: List[str] = []

    async with session.create_client("dynamodb") as dynamodb_client:
        for file_id in final:
            file_item = await dynamodb_client.get_item(
                TableName=f"{dataset}_files", Key={"id": {"N": str(file_id)}}
            )

            response.append(file_item["Item"]["filename"]["S"])

    return {
        "data": sorted(response),
        "query": str(dnf),
        "time": time.time() - begin,
    }


async def publish_file_for_5_minutes_and_return_url(
    dataset: str, filename: str
) -> str:
    session = aiobotocore.get_session()

    # create shareable url to download the file (valid for 300 seconds)
    async with session.create_client("s3") as s3_client:
        url: str = await s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": S3_BUCKET,
                "Key": f"static/{dataset}/{filename}",
            },
            ExpiresIn=300,
        )

        return url
