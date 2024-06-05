# LogSecretHunter: Secure Your Logs in S3

## Overview
LogSecretHunter is a powerful tool designed to scan log files stored in Amazon S3 for sensitive information, such as secrets, API keys, and passwords. By leveraging the `detect-secrets` tool, LogSecretHunter ensures your log files are free from sensitive data leaks, helping you maintain security and compliance.

## Features
* **Automated Scanning**: Asynchronous downloads and scans log files using asyncio and aiobotocores from your specified S3 bucket based on a prefix and time window. 
* **Comprehensive Detection**: Utilizes the robust 'detect-secrets' engine to identify a wide range of sensitive information.
* **Easy Integration** : Seamlessly integrates with your existing AWS environment and workflows.
* **Detailed Reporting**: Provides detailed reports on detected secrets for easy remediation.

## Getting Started
1. Prerequisites:

* Python 3.7+
* AWS credentials configured (e.g., via `aws configure` or environment variables)

2. Usage:
* Clone this repository:
```sh
git clone https://github.com/issabayevmk/logsecrethunter.git
cd logsecrethunter
```
* Activate python virtual environment, e.g. for Linux, Mac
```sh
python3 -m venv venv
source venv/bin/activate
```
* Install dependencies
```sh
pip install -r requirements.txt
```
* Run the tool:
```sh
python log_secret_hunter.py <bucket_name> <prefix> <start_time> <end_time> <download_dir> <result_file> [--profile_name <profile_name>] [--log_level <log_level>]
```
**Example**
```sh
python download_s3.py my-bucket my-prefix 2024-01-01T00:00:00 2024-01-31T23:59:59 /path/to/download /path/to/results.txt --profile_name my-aws-profile --log_level INFO
```

### Positional Arguments
* `bucket_name`: The name of the S3 bucket.
* `prefix`: The prefix for the S3 objects.
* `start_time`: The start of the time window (ISO 8601 format, e.g., 2024-01-01T00:00:00).
* `end_time`: The end of the time window (ISO 8601 format, e.g., 2024-01-31T23:59:59).
* `download_dir`: The directory to download the files to.
* `results_file`: The file to save the scan results.
### Optional Arguments
* `--profile_name`: The AWS profile name to use.
* `--log_level`: Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Default is WARNING.

## Logging
The script uses Python's `logging` library to provide detailed logs of its operations. By default, the log level is set to `WARNING`, but this can be adjusted using the `--log_level` argument.

## How It Works
1. **Download Files**: The script downloads files from the specified S3 bucket and prefix that were modified within the specified time window.
2. **Process Files**:
* **Scan for Secrets**: Each file is scanned for secrets using detect-secrets.
* **Decompress Files**: If a file is compressed (.gz or .zip), it is decompressed.
* **Scan Decompressed Files**: Decompressed files are also scanned for secrets.
* **Cleanup**: Both the original and decompressed files are deleted after scanning.
* **Save Results**: The found secrets are saved to the specified result file.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request.

1. Fork the repository.
2. Create a new branch (git checkout -b feature-branch).
3. Make your changes.
4. Commit your changes (git commit -m 'Add new feature').
5. Push to the branch (git push origin feature-branch).
6. Open a pull request.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact
For questions or feedback, feel free to open an issue.
