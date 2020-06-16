#!/bin/env python3
"""
Helper for processing and uploading dataset (text collection).
"""
from typing import Set, Tuple, List, Dict, Any

import argparse
import asyncio
import collections
import itertools
import json
import os
import re
import sys
import time

import aiobotocore
import aiofiles
import nltk
import textract
import tqdm


async def ensure_unique_names_and_create_db_and_bucket(
    session: aiobotocore.session.AioSession, dataset_name: str, s3_bucket: str
) -> bool:
    """
    Gets AWS session and dataset_name. Checks if there are not
    already tables in DynamoDB with same names and bucket contents
    in S3. If they're not - creates 2 tables (one for filenames->ids map
    and second for terms->filenames map).
    """

    async with session.create_client("s3") as s3_client:
        buckets = await s3_client.list_buckets()

        for bucket in buckets["Buckets"]:
            if bucket["Name"] == s3_bucket:
                break
        else:
            print(f'Seems like such bucket "{s3_bucket}" does not exist')
            return False

    files_table = f"{dataset_name}_files"
    terms_table = f"{dataset_name}_terms"

    async with session.create_client("dynamodb") as dynamodb_client:
        all_tables = await dynamodb_client.list_tables()

        if any(
            name in all_tables["TableNames"]
            for name in (files_table, terms_table)
        ):
            print(
                f"Either {files_table} or {terms_table} table exists "
                "in DynamoDB. Rename your dataset folder, if you want "
                "to process and upload it",
                file=sys.stderr,
            )
            return False

        # creating table for filenames and their ids
        table1 = await dynamodb_client.create_table(
            TableName=files_table,
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "N"}
            ],
            ProvisionedThroughput={
                "ReadCapacityUnits": 30,
                "WriteCapacityUnits": 30,
            },
        )

        if table1["ResponseMetadata"]["HTTPStatusCode"] != 200:
            print(f"Table {files_table} creation did not succeed. Aborting")
            return False

        # creating table for terms dictionary
        # (keys are terms, values are sets of numbers (file ids))
        table2 = await dynamodb_client.create_table(
            TableName=terms_table,
            KeySchema=[{"AttributeName": "term", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "term", "AttributeType": "S"}
            ],
            ProvisionedThroughput={
                "ReadCapacityUnits": 30,
                "WriteCapacityUnits": 30,
            },
        )

        if table2["ResponseMetadata"]["HTTPStatusCode"] != 200:
            print(f"Table {terms_table} creation did not succeed. Aborting")
            return False

        waiter = dynamodb_client.get_waiter("table_exists")
        await waiter.wait(TableName=files_table)
        await waiter.wait(TableName=terms_table)

    return True


def process_dataset(
    dataset_dir: str, stopwords_set: Set[str]
) -> Tuple[Dict[str, int], Dict[str, Set[int]]]:

    # generator from 0 to inf
    id_generator = iter(itertools.count())

    # call listdir only once
    files = os.listdir(dataset_dir)

    # first table/dictionary with filenames and ids, next table (terms)
    # will represent map with terms as keys and sets of ids as values
    file_ids = {file_: next(id_generator) for file_ in files}

    # each term (stemmed word) with set of file ids (instead of filenames
    # in order to save space)
    terms = collections.defaultdict(set)

    # we're fine with PorterStemmer, could be done with lemmatization,
    # but doesn't matter much in particular project
    stemmer = nltk.stem.PorterStemmer()

    # just measuring time for user
    processing_start = time.time()

    for file_ in tqdm.tqdm(files):
        # using textract,
        # because there could be binary files with some text (pdf, docx etc)
        file_contents = textract.process(os.path.join(dataset_dir, file_))

        for word in (
            set(
                # re looks like the fastest word tokenizer comparing to nltk,
                # spacy or whatever other options
                re.compile(r"\b[^\d\W]+\b").findall(
                    file_contents.decode().lower()
                )
            )
            - stopwords_set
        ):
            # if term existed, file id will be added to set, otherwise
            # new key will be created first and then file id will be added
            # to the empty set
            terms[stemmer.stem(word)].add(file_ids[file_])

    print("Processing time:", time.time() - processing_start)
    return file_ids, terms


async def batch_write_to_dynamo(
    session: aiobotocore.session.AioSession,
    table_name: str,
    data: List[Dict[str, Any]],
) -> None:

    # NOTE: a snippet below is slightly modified, but taken from
    # https://aiobotocore.readthedocs.io/en/latest/examples.html
    async with session.create_client("dynamodb") as dynamodb_client:

        for slice_index in tqdm.tqdm(range(0, len(data), 25)):

            response = await dynamodb_client.batch_write_item(
                RequestItems={table_name: data[slice_index : slice_index + 25]}
            )

            if len(response["UnprocessedItems"]) != 0:

                # Hit the provisioned write limit
                await asyncio.sleep(3)

                # Items left over that haven't been inserted
                unprocessed_items = response["UnprocessedItems"]

                print("Resubmitting items")
                # Loop until unprocessed items are written
                while len(unprocessed_items) > 0:
                    response = await dynamodb_client.batch_write_item(
                        RequestItems=unprocessed_items
                    )
                    # If any items are still left over, add them to the
                    # list to be written
                    unprocessed_items = response["UnprocessedItems"]

                    # If there are items left over, we could do with
                    # sleeping some more
                    if len(unprocessed_items) > 0:
                        print("Backing off for 5 seconds")
                        await asyncio.sleep(5)


async def upload_dataset_to_dynamodb(
    session: aiobotocore.session.AioSession,
    dataset_name: str,
    file_ids: Dict[str, int],
    terms: Dict[str, Set[int]],
) -> None:

    await batch_write_to_dynamo(
        session,
        f"{dataset_name}_files",
        [
            {
                "PutRequest": {
                    "Item": {
                        "id": {"N": str(file_id)},
                        "filename": {"S": filename},
                    }
                }
            }
            for filename, file_id in file_ids.items()
        ],
    )

    await batch_write_to_dynamo(
        session,
        f"{dataset_name}_terms",
        [
            {
                "PutRequest": {
                    "Item": {
                        "term": {"S": term},
                        "files": {"NS": tuple(map(str, files))},
                    }
                }
            }
            for term, files in terms.items()
        ],
    )


async def upload_files_to_s3(
    session: aiobotocore.session.AioSession,
    dataset_dir: str,
    dataset_name: str,
    s3_bucket: str,
) -> None:

    print(f"Uploading {dataset_dir}")

    async with session.create_client("s3") as s3_client:
        for file_ in tqdm.tqdm(os.listdir(dataset_dir)):
            async with aiofiles.open(
                os.path.join(dataset_dir, file_), "rb"
            ) as f_in:
                await s3_client.put_object(
                    Bucket=s3_bucket,
                    Body=await f_in.read(),
                    Key=f"static/{dataset_name}/{file_}",
                )


def main() -> None:
    """
    Parse CLI args and route to right logic
    """
    arg_parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        allow_abbrev=False,  # disallow abbreviations, be explicit!
    )

    arg_parser.add_argument(
        "--dataset-dir",
        required=True,
        type=str,
        help="A path to directory with files to be processed and used "
        "in boolean model as dataset",
    )

    arg_parser.add_argument(
        "--s3-bucket",
        required=True,
        type=str,
        help="Name of the S3 bucket to upload files to",
    )

    arg_parser.add_argument(
        "--stopwords",
        required=False,
        type=str,
        help="JSON file with stopwords",
    )

    args = arg_parser.parse_args()

    if not (
        os.path.isdir(args.dataset_dir)
        and os.access(args.dataset_dir, os.R_OK)
    ):
        print(
            f'"{args.dataset_dir}" does not exist '
            "or script has no permissions.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.stopwords is not None and not (
        os.path.isfile(args.stopwords) and os.access(args.stopwords, os.R_OK)
    ):
        print(
            f'"{args.stopwords}" does not exist or script has no permissions.',
            file=sys.stderr,
        )
        sys.exit(1)

    if args.stopwords is None:
        stopwords_set = set()
    else:
        with open(args.stopwords, "r") as f_in:
            stopwords_set = set(json.load(f_in))

    dataset_dir = os.path.abspath(os.path.expanduser(args.dataset_dir))
    dataset_name = os.path.basename(dataset_dir)

    print("Dir to be processed and uploaded:", dataset_dir)
    print("Dataset name:", dataset_name)

    session = aiobotocore.get_session()

    if not asyncio.run(
        ensure_unique_names_and_create_db_and_bucket(
            session, dataset_name, args.s3_bucket
        )
    ):
        sys.exit(1)

    file_ids, terms = process_dataset(dataset_dir, stopwords_set)

    asyncio.run(
        upload_dataset_to_dynamodb(session, dataset_name, file_ids, terms)
    )

    asyncio.run(
        upload_files_to_s3(session, dataset_dir, dataset_name, args.s3_bucket)
    )


if __name__ == "__main__":
    main()
