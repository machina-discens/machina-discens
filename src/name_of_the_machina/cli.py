# -*- coding: utf-8 -*-
# Python

"""Copyright (c) Alexander Fedotov.
This source code is licensed under the license found in the
LICENSE file in the root directory of this source tree.
"""
import os
import sys
import select
import fileinput
import argparse
import syslog
from .config import Config
from .utilities import new_plato_text


def options_and_arguments():
    parser = argparse.ArgumentParser(
        description="Machina-Ratiocinatrix ratiocinates.",
        epilog="Example:  machina input_text.txt > output_text.txt"
    )

    # Give the access key and token, or set the environment variables in advance.
    parser.add_argument('-p', '--provider-api-key',
                        default=os.getenv('PROVIDER_API_KEY', 'no_key'),
                        help="LLM provider API key (defaults to $PROVIDER_API_KEY)")
    parser.add_argument('-g', '--github-token',
                        default=os.getenv('GITHUB_TOKEN', 'no_token'),
                        help="GitHub API token (defaults to $GITHUB_TOKEN)")

    parser.add_argument('-a', '--append',
                        action='store_true',
                        help="Append the proceeds to the input.")

    parser.add_argument('-d', '--debug',
                        action='store_true',
                        help="Debug flag.")

    parser.add_argument('-i', '--interactive',
                        action='store_true',
                        help="Enable interactive mode (defaults to False)")

    # Positional arguments (files)
    # '*' captures zero or more arguments into a list, nargs='+' one or more.
    parser.add_argument('filenames',
                        nargs='*',
                        help="Zero (when text comes though a pipe) or more files to process.")
    return parser


def run():
    """After installation, on Linux prompt
    $ machina file1.txt file2.txt > output.txt
    """
    args = options_and_arguments().parse_args()

    # If no files are provided AND no data is being piped in - exit.
    # if not args.filenames:
    #     # Check if stdin (fd 0) is ready to be read
    #     readable, _, _ = select.select([sys.stdin], [], [], 0.1)
    #     if not readable:
    #         print("Error: No input files or piped text stream.")
    #         options_and_arguments().print_help()
    #         sys.exit(1)

    # Ingest files line by line. Join is here for long files.
    # lines = []
    # for line in fileinput.input(files=args.filenames or ['-'], encoding="utf-8"):
    #     lines.append(line)
    # raw_input = "".join(lines)

    config = Config()

    if args.provider_api_key:
        if args.provider_api_key.startswith('sk-'):
            if args.provider_api_key.startswith('sk-proj-'):
                config.provider = 'OpenAI'
                os.environ['OPENAI_API_KEY'] = args.provider_api_key
            elif args.provider_api_key.startswith('sk-ant-'):
                config.provider = 'Anthropic'
                os.environ['ANTHROPIC_API_KEY'] = args.provider_api_key
            elif args.provider_api_key.startswith('LLM|'):
                config.provider = 'MetAI'
                os.environ['METAI_API_KEY'] = args.provider_api_key
            else:
                config.provider = 'DepSek'
                os.environ['DEPSEK_API_KEY'] = args.provider_api_key

        config.provider_api_key = args.provider_api_key

        if args.github_token:
            config.github_token = args.github_token
            os.environ['GITHUB_TOKEN'] = args.github_token

    # Ingest files line by line. Join is here for long files.
    lines = []
    for line in fileinput.input(files=args.filenames or ['-'], encoding="utf-8"):
        lines.append(line)
    raw_input = "".join(lines)

    from .main import machina

    try:
        thoughts, text = machina(raw_input, config)
        output = new_plato_text(thoughts, text, config.name)
        if args.append:
            output = raw_input + '\n\n' + output
        sys.stdout.write(output)
        sys.stdout.flush()

        # Assesment and signals.

        utterance = "Machina is ready"
        # Open syslog connection
        syslog.openlog(
            ident="machina-ratiocinatrix",
            logoption=syslog.LOG_NDELAY,
            facility=syslog.LOG_USER
        )
        # Signal (single line less than 4096 only!)
        syslog.syslog(syslog.LOG_INFO, utterance)
        syslog.closelog()

    except Exception as e:
        if args.debug:
            import traceback
            traceback.print_exc()
        else:
            sys.stderr.write(f'Machina did not work {e}\n')
            sys.stderr.flush()
        sys.exit(1)


if __name__ == '__main__':
    run()
