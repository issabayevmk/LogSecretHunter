import asyncio
import aiofiles
import aiobotocore.session
from datetime import datetime, timezone
import gzip
import json
import logging
import os
import shutil
import subprocess
import zipfile
from concurrent.futures import ThreadPoolExecutor

async def download_file(s3_client, bucket_name, key, download_path):
    logging.info(f"Starting download of {key}")
    response = await s3_client.get_object(Bucket=bucket_name, Key=key)
    async with aiofiles.open(download_path, "wb") as f:
        while True:
            chunk = await response["Body"].read(1024)
            if not chunk:
                break
            await f.write(chunk)
    logging.info(f"Completed download of {key}")


async def scan_file_for_secrets(file_path, key, results_file):
    def run_detect_secrets(file_path):
        logging.info(f"Running detect-secrets scan on {file_path}")
        result = subprocess.run(
            ["detect-secrets", "scan", file_path], capture_output=True, text=True
        )
        return result.stdout

    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, run_detect_secrets, file_path)
        result = json.loads(result)
        if result["results"] != {}:
            logging.warning(f"Secret found in {key}: {result['results']}")
            async with aiofiles.open(results_file, "a") as f:
                await f.write(f"Secrets scan result for {file_path}:\n{result}\n")
        else:
            logging.info(f"No secrets in {key}")


async def decompress_file(file_path):
    decompressed_files = []
    if file_path.endswith(".gz"):
        logging.info(f"Decompressing {file_path}")
        with gzip.open(file_path, "rb") as f_in:
            decompressed_path = file_path[:-3]
            with open(decompressed_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
            decompressed_files.append(decompressed_path)
    elif file_path.endswith(".zip"):
        logging.info(f"Decompressing {file_path}")
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            decompressed_dir = file_path[:-4]
            zip_ref.extractall(decompressed_dir)
            decompressed_files.extend(
                [os.path.join(decompressed_dir, name) for name in zip_ref.namelist()]
            )
    return decompressed_files


async def process_file(file_path, key, results_file):
    # Scan original file
    await scan_file_for_secrets(file_path, key, results_file)
    # Decompress if necessary and scan decompressed files
    decompressed_files = await decompress_file(file_path)
    for decompressed_file in decompressed_files:
        await scan_file_for_secrets(decompressed_file, key, results_file)
        os.remove(decompressed_file)
    # Remove the original file
    os.remove(file_path)


async def download_and_process_files(
    s3_client, bucket_name, key, download_dir, results_file
):
    download_path = os.path.join(download_dir, os.path.basename(key))
    await download_file(s3_client, bucket_name, key, download_path)
    await process_file(download_path, key, results_file)


async def download_files_within_time_window(
    bucket_name, prefix, start_time, end_time, download_dir, results_file, profile_name
):
    session = aiobotocore.session.AioSession(profile=profile_name)
    async with session.create_client("s3") as s3_client:
        paginator = s3_client.get_paginator("list_objects_v2")
        tasks = []
        async for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                last_modified = obj["LastModified"]
                # Ensure both datetimes are aware (UTC)
                if start_time <= last_modified <= end_time:
                    tasks.append(
                        download_and_process_files(
                            s3_client, bucket_name, key, download_dir, results_file
                        )
                    )
        await asyncio.gather(*tasks)


async def main(
    bucket_name, prefix, start_time, end_time, download_dir, results_file, profile_name
):
    # Convert start_time and end_time to aware datetime objects in UTC
    start_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S").replace(
        tzinfo=timezone.utc
    )
    end_time = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S").replace(
        tzinfo=timezone.utc
    )
    await download_files_within_time_window(
        bucket_name,
        prefix,
        start_time,
        end_time,
        download_dir,
        results_file,
        profile_name,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Download S3 files within a time window."
    )
    parser.add_argument("bucket_name", type=str, help="The name of the S3 bucket.")
    parser.add_argument("prefix", type=str, help="The prefix for the S3 objects.")
    parser.add_argument(
        "start_time", type=str, help="The start of the time window (ISO 8601 format)."
    )
    parser.add_argument(
        "end_time", type=str, help="The end of the time window (ISO 8601 format)."
    )
    parser.add_argument(
        "download_dir", type=str, help="The directory to download the files to."
    )
    parser.add_argument(
        "results_file", type=str, help="The file to save the scan results."
    )
    parser.add_argument(
        "--profile_name", type=str, default=None, help="The AWS profile name to use."
    )
    parser.add_argument(
        "--log_level",
        type=str,
        default="WARNING",
        help="Set the logging level (default: WARNING). Use [DEBUG, INFO, WARNING, ERROR, CRITICAL]",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logging.warning(
        f"Starting download with the following parameters:\n"
        f"Bucket: {args.bucket_name}\nPrefix: {args.prefix}\n"
        f"Start Time: {args.start_time}\nEnd Time: {args.end_time}\n"
        f"Download Directory: {args.download_dir}\n"
        f"Result File: {args.results_file}\n"
        f"Profile Name: {args.profile_name}\n"
        f"Log Level: {args.log_level}"
    )

    asyncio.run(
        main(
            args.bucket_name,
            args.prefix,
            args.start_time,
            args.end_time,
            args.download_dir,
            args.results_file,
            args.profile_name,
        )
    )
