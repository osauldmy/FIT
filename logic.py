"""
A module which implements Boolean model logic, mainly
process_query() function.

dataset_names() and publish_file_for_5_minutes_and_return_url()
are aux function for smooth runnning.
"""
from typing import Dict, List, Set, Union

import logging
import os
import re
import time

import aiobotocore
import nltk
import pyeda.boolalg.expr


S3_BUCKET = os.getenv("BOOLEAN_MODEL_S3_BUCKET") or "boolean-model"


async def dataset_names() -> List[str]:
    """
    Returns available dataset (collection of texts) names.

    Each has a folder with files on AWS S3 and 2 tables on AWS DynamoDB,
    one for mapping files to ids and other mapping
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
    The main logic thing in the whole project.

    Gets dataset name and boolean query (in string format).
    Checks if dataset exists (there should be 2 tables for each in
    the database and preferably raw texts uploaded to AWS S3 bucket),
    then parses the query with `pyeda` boolean expression parser.
    Raises ValueError if query cannot be parsed or continues otherwise.

    :param str dataset: dataset/text collection name
    :param str query: boolean expression
    :return: custom dictionary with 3 keys (time spent on execution
        to show user, string representation or parsed query to show user
        and list of filenames in what some (or all) query parts are present)
    :rtype: Dict[str, Union[str, float, List[str]]]

    :raises ValueError: on not existing dataset
        or when parser cannot parse the query
    :raises: possibly can be raises any exception from aiobotocore. Code that
        will call this function should handle it by its own.
    """

    if dataset not in await dataset_names():
        raise ValueError(
            "There is no such dataset. Refusing to process the query."
        )

    logging.info("Raw query: %s", query)

    # some time measuring
    begin = time.time()

    # PyEDA doesn't work with and/or/not operators in natural language,
    # need to escape them to mathematical symbols first
    query = re.sub(
        r" or ",
        r" | ",
        re.sub(
            r" and ",
            r" & ",
            # "not" that is not an end of the word (like in "huguenot"),
            # and which has either space or left parenthesis
            re.sub(r"\bnot([( ])", r"~\1", query.lower().strip()),
        ),
    )

    # trying to parse, or otherwise user will get
    # "Cannot parse the query" pop-up on a frontend side
    try:
        expr = pyeda.boolalg.expr.expr(query, simplify=True)
        logging.info("Parsed expr: %s", expr)
    except pyeda.parsing.boolexpr.Error as error:
        logging.exception(error)
        raise ValueError("Cannot parse the query")

    # Using PorterStemmer.
    # Again - lemmatization or some super-duper thing could be used,
    # but for particular project this is more than enough.
    # Moreover, query parts should be processed the same way
    # as data were preprocessed.
    stemmer = nltk.stem.PorterStemmer()

    # Disjunctive Normal Form
    dnf = expr.to_dnf()

    logging.info("DNF: %s", dnf)

    # AWS session
    session = aiobotocore.get_session()

    # first fetch all unique terms from the DynamoDB NoSQL database
    # so then set operations can be done without data fetching and
    # using already prepared data
    fetched_terms: Dict[str, Set[int]] = {}

    async with session.create_client("dynamodb") as dynamodb_client:

        for term in map(stemmer.stem, set(map(str, dnf.inputs))):
            item = await dynamodb_client.get_item(
                TableName=f"{dataset}_terms", Key={"term": {"S": term}}
            )

            try:
                # DynamoDB returns numbers in string format, so we need
                # first to cast it
                fetched_terms[term] = set(
                    map(int, item["Item"]["files"]["NS"])
                )
            except KeyError:
                # if some term (word) is missing in the database, the whole
                # result can be empty set
                # (if the term was in the global AND chain for example)
                fetched_terms[term] = set()

    # Set of file ids (for response), than to be changed to their real names.
    # The appropriate data structure is of course the set, so we can
    # perform standard logical operations with it.
    file_ids: Set[int] = set()

    # Iterate over the list of dists, where terms are keys and values are
    # either 0s or 1s (satisfiability for DNF). Each element of the list
    # is a clause in the OR chain, so in order to return at least some
    # result, there should be one `evaluation` dict with terms that
    # are presented in the table (therefore in text as well) and evaluation
    # should produce not empty set.
    for evaluation in dnf.satisfy_all():

        # Create temporary set for multiple ANDs.
        # `evaluation` dict with 0s and 1s will be sorted, so firstly
        # 1s will be added to temp set (with intersection) and then 0s
        # will be substracted from the set.
        #
        # After each `evaluation` pair `temp` set will be added to
        # `file_ids` set (OR of multiple clauses in DNF).
        temp: Set[int] = set()

        for symbol, value in reversed(
            sorted(evaluation.items(), key=lambda item: item[1])
        ):

            contents = fetched_terms[stemmer.stem(str(symbol))]

            # there is no such term in the table
            # (therefore in collection as well), so there is no sense to
            # do ANDs (intersection with update) for `temp` set
            if len(contents) == 0:
                break

            # adding to `temp` set
            if value == 1:
                if len(temp) != 0:
                    temp.intersection_update(contents)
                else:
                    temp = contents
            # substracting from `temp` set (for e.g. "and not cats")
            else:
                temp -= contents

        # adding it as OR
        file_ids.update(temp)

    # set names of files
    response: List[str] = []

    async with session.create_client("dynamodb") as dynamodb_client:
        for file_id in file_ids:
            file_item = await dynamodb_client.get_item(
                TableName=f"{dataset}_files", Key={"id": {"N": str(file_id)}}
            )

            response.append(file_item["Item"]["filename"]["S"])

    return {
        # the set was not sorted,
        # and the list was created after not sorted set iteration
        "data": sorted(response),
        "query": str(dnf),
        "time": time.time() - begin,
    }


async def publish_file_for_5_minutes_and_return_url(
    dataset: str, filename: str
) -> str:
    """
    Little aux function to make the user happy.
    When results are shown (if they are), near each record with filename
    there is a `Download` button, so user can click it
    and file will be open/downloaded.
    The thing is files are located on a private S3 bucket, so there is a need
    to expose them/make them public for some short time. So particular function
    makes files (of datasets) public for a 5 minutes on a request.

    :param str dataset: the name of dataset / text collection (as it on S3)
    :param str filename: the name of file in the collection
    :return: an URL to publicly accessible for a 5 minutes file
    :rtype: str

    :raises: possibly some aiobotocore exception. Code that calls this function
      does exceptions handling.
    """
    session = aiobotocore.get_session()

    # create shareable url to download the file (valid for 300 seconds)
    async with session.create_client("s3") as s3_client:

        url: str = await s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": S3_BUCKET,
                "Key": f"static/{dataset}/{filename}",
            },
            ExpiresIn=300,  # seconds
        )

        return url
