# -*- coding: utf-8 -*-
# Python

"""Copyright (c) Alexander Fedotov.
This source code is licensed under the license found in the
LICENSE file in the root directory of this source tree.
"""
import sys
from os import environ, path
from .githf import fetch_instructions
from .utilities import (plato_text_to_muj,
                        plato_text_to_mpuj,
                        plato_text_to_cmj,
                        llm_soup_to_text,
                        newtls_to_oldtls)


def machina(plato_text, config, **kwargs):
    """Core agent logic.

    1. Fetches the system prompt from a private GitHub repo.
    2. Calls Provider
    3. Returns a (thoughts, text) tuple.
    """
    # Fetch the confidential system prompt, name is for a checkup.
    name, verb, system_prompt, tools, rubric = fetch_instructions(config)

    system_prompt += '\n' + rubric

    # Load an appropriate library and query the API.
    provider = config.provider
    api_key  = config.provider_api_key
    
    if provider == 'OpenAI':
        # Transform plato_text to MUJ format
        messages = plato_text_to_muj(plato_text=plato_text,
                                     machine_name=name)
        # Call OpenAI API via opehaina
        environ['OPENAI_API_KEY'] = api_key
        try:
            from .providers import openai
        except ImportError:
            print("openai module is missing.", file=sys.stderr)
            sys.exit(1)
            
        thoughts, text = openai.respond(
            messages=messages,
            instructions=system_prompt,
            tools=tools,
            **kwargs
        )

        thoughts = llm_soup_to_text(thoughts)
        return thoughts, text

    elif provider == 'DepSek':
        # Transform plato_text to CMJ format
        messages = plato_text_to_cmj(plato_text=plato_text,
                                     machine_name=name)
        # Transform new tools definition into an old one.
        oldtls = newtls_to_oldtls(tools_definition=tools)
        # Call DepSek API
        environ['DEPSEK_API_KEY'] = api_key
        try:
            from .providers import depsek
        except ImportError:
            print("depsek module is missing.", file=sys.stderr)
            sys.exit(1)

        thoughts, text = depsek.respond(
            messages=messages,
            instructions=system_prompt,
            tools=oldtls,
            **kwargs
        )

        return thoughts, text

    elif provider == 'Xai':
        # Transform plato_text to MUJ format
        messages = plato_text_to_muj(plato_text=plato_text,
                                     machine_name=name)
        # Call OpenAI API via opehaina
        environ['XAI_API_KEY'] = api_key
        try:
            from .providers import strangelove
        except ImportError:
            print("openai module is missing.", file=sys.stderr)
            sys.exit(1)

        thoughts, text = strangelove.respond(
            messages=messages,
            instructions=system_prompt,
            tools=tools,
            **kwargs
        )

        thoughts = llm_soup_to_text(thoughts)
        return thoughts, text

    elif provider == 'MetAI':
        # Transform plato_text to MUJ format
        messages = plato_text_to_muj(plato_text=plato_text,
                                     machine_name=name)
        # Call OpenAI API via opehaina
        environ['METAI_API_KEY'] = api_key
        try:
            from .providers import metai
        except ImportError:
            print("metai module is missing.", file=sys.stderr)
            sys.exit(1)

        thoughts, text = metai.respond(
            messages=messages,
            instructions=system_prompt,
            tools=tools,
            **kwargs
        )

        thoughts = llm_soup_to_text(thoughts)
        return thoughts, text


if __name__ == '__main__':
    print('You have launched main')
