# -*- coding: utf-8 -*-
# Python

"""Copyright (c) Alexander Fedotov.
This source code is licensed under the license found in the
LICENSE file in the root directory of this source tree.
"""
import json
import difflib
import subprocess

# Definitive list of authorized execution routines (32 target verbs)
SUPPORTED_VERBS = {
    "think", "reason", "ratiocinate", "reflect", "predict", "deliberate",
    "summarize", "meditate", "fantasize", "analyze", "conceptualize",
    "conjecture", "evaluate", "explore", "understand", "generalize",
    "speculate", "hypothesize", "imagine", "intuit",
    "collate", "synthesize", "verify", "explain", "write", "question",
    "criticize", "argue", "debate", "object", "suggest", "will",
}
# 2. Comprehensive synonym-to-target mapping dictionary
SEMANTIC_SYNONYM_MAP = {
    # --- think ---
    "cogitate": "think",
    "ponder": "think",
    "brainstorm": "think",
    # --- reason ---
    "deduce": "reason",
    "infer": "reason",
    "rationalize": "reason",
    "logicize": "reason",
    # --- ratiocinate ---
    "syllogize": "ratiocinate",
    "philosophize": "ratiocinate",
    # --- reflect ---
    "reconsider": "reflect",
    "review": "reflect",
    "retrospect": "reflect",
    # --- predict ---
    "forecast": "predict",
    "foretell": "predict",
    "project": "predict",
    "anticipate": "predict",
    # --- deliberate ---
    "weigh": "deliberate",
    "contemplate": "deliberate",
    "scrutinize": "deliberate",
    # --- summarize ---
    "condense": "summarize",
    "shorten": "summarize",
    "abbreviate": "summarize",
    "abstract": "summarize",
    "outline": "summarize",
    # --- meditate ---
    "ruminate": "meditate",
    "brood": "meditate",
    # --- fantasize ---
    "daydream": "fantasize",
    "romanticize": "fantasize",
    # --- analyze ---
    "dissect": "analyze",
    "examine": "analyze",
    "inspect": "analyze",
    "deconstruct": "analyze",
    # --- evaluate ---
    "appraise": "evaluate",
    "assess": "evaluate",
    "judge": "evaluate",
    "rate": "evaluate",
    # --- explore ---
    "investigate": "explore",
    "probe": "explore",
    "scout": "explore",
    # --- understand ---
    "comprehend": "understand",
    "grasp": "understand",
    "fathom": "understand",
    "absorb": "understand",
    # --- generalize ---
    "universalize": "generalize",
    "broaden": "generalize",
    "extrapolate": "generalize",
    # --- speculate ---
    "guess": "speculate",
    "surmise": "speculate",
    # --- hypothesize ---
    "theorize": "hypothesize",
    "postulate": "hypothesize",
    "premise": "hypothesize",
    # --- imagine ---
    "envision": "imagine",
    "visualize": "imagine",
    "conceive": "imagine",
    # --- intuit ---
    "sense": "intuit",
    "feel": "intuit",
    # --- collate ---
    "gather": "collate",
    "assemble": "collate",
    "compile": "collate",
    "organize": "collate",
    # --- synthesize ---
    "blend": "synthesize",
    "merge": "synthesize",
    "combine": "synthesize",
    "integrate": "synthesize",
    "amalgamate": "synthesize",
    # --- verify ---
    "confirm": "verify",
    "validate": "verify",
    "authenticate": "verify",
    "corroborate": "verify",
    "fact-check": "verify",
    "proof": "verify",
    # --- explain ---
    "clarify": "explain",
    "elucidate": "explain",
    "describe": "explain",
    "interpret": "explain",
    "demystify": "explain",
    # --- write ---
    "draft": "write",
    "compose": "write",
    "author": "write",
    "generate": "write",
    # --- question ---
    "interrogate": "question",
    "query": "question",
    "challenge": "question",
    # --- criticize ---
    "critique": "criticize",
    "bash": "criticize",
    "fault": "criticize",
    "reprove": "criticize",
    "censure": "criticize",
    # --- argue ---
    "assert": "argue",
    "maintain": "argue",
    "contend": "argue",
    "claim": "argue",
    # --- debate ---
    "dispute": "debate",
    "contest": "debate",
    # --- object ---
    "protest": "object",
    "oppose": "object",
    "counter": "object",
    "demur": "object",
    # --- suggest ---
    "propose": "suggest",
    "recommend": "suggest",
    "advise": "suggest",
    "hint": "suggest",
    # --- will ---
    "intend": "will",
    "resolve": "will",
    "determine": "will",
    "decree": "will",
    # --- conceptualize ---
    "abstract-out": "conceptualize",
    "ideate": "conceptualize",
    "frame": "conceptualize",
    "schematize": "conceptualize",
    # --- conjecture ---
    "suppose": "conjecture",
    "presume": "conjecture",
    "assume": "conjecture"
}

MAX_RETRIES = 3


def count_failures(messages: list) -> int:
    """
    Scans backward through the conversation history to count consecutive
    unsuccessful attempts to use an invalid semantic verb.
    """
    failure_count = 0
    for msg in reversed(messages):
        if msg.get("role") == "tool":
            try:
                content_json = json.loads(msg.get("content", "{}"))
                if content_json.get("error_type") == "invalid_verb":
                    failure_count += 1
                    continue
            except json.JSONDecodeError:
                pass
        # Break count if we hit a human intervention point or a successful turn
        if msg.get("role") == "user" or (msg.get("role") == "assistant" and "tool_calls" not in msg):
            break
    return failure_count


def semantic_operation(call_id: str, verb: str, utterance: str, messages: list, shared_context: str) -> dict:
    """
    Validates the semantic action and manages execution or self-correction loops.
    """
    normalized_verb = verb.strip().lower()
    close_matches = difflib.get_close_matches(normalized_verb, list(SUPPORTED_VERBS), n=2, cutoff=0.6)

    # --- SUCCESS PATH ---
    if normalized_verb in SUPPORTED_VERBS:
        # Replace this placeholder with your actual execution mechanism
        # (e.g., calling an executing LLM pipeline with your shared context)
        execution_result = f"[Successfully executed '{normalized_verb}' on context: {utterance}]"

        return {
            "role": "tool",
            "tool_call_id": call_id,
            "content": json.dumps({"status": "success", "result": execution_result})
        }

    # --- FAILURE / VALIDATION PATH ---
    past_failures = count_failures(messages)

    # Check if this attempt will breach the 3-try threshold
    if past_failures < (MAX_RETRIES - 1):
        # Soft Error: Guide the LLM to fix the parameter on its next turn
        error_payload = {
            "status": "error",
            "error_type": "invalid_verb",
            "message": f"The verb '{verb}' is not a supported semantic_operation.",
            "hint": "Please change your tool call parameter. Choose a valid verb from the allowed list.",
            "supported_alternatives": list(SUPPORTED_VERBS)
        }
    else:
        # Hard Error: Force the loop to stop and make the LLM apologize to the user
        error_payload = {
            "status": "hard_failure",
            "error_type": "loop_prevented",
            "message": f"CRITICAL: You have failed verification {MAX_RETRIES} times. Do not attempt another tool call.",
            "instruction": "Immediately respond to the human user in plain text. Apologize, explain that the requested text action cannot be performed, and display a clean bulleted list of the exact operations you are authorized to run."
        }

    return {
        "role": "tool",
        "tool_call_id": call_id,
        "content": json.dumps(error_payload)
    }


def count_previous_failures(messages: list) -> int:
    """
    Scans backward through the conversation history to count consecutive
    unsuccessful attempts to use an invalid semantic verb.
    """
    failure_count = 0
    for msg in reversed(messages):
        if msg.get("role") == "tool":
            try:
                content_json = json.loads(msg.get("content", "{}"))
                if content_json.get("error_type") == "invalid_verb":
                    failure_count += 1
                    continue
            except json.JSONDecodeError:
                pass
        # Reset tracker if a manual text message or clean turn occurred
        if msg.get("role") == "user" or (msg.get("role") == "assistant" and "tool_calls" not in msg):
            break
    return failure_count


def proposed_execute_semantic_operation(call_id: str, verb: str, utterance: str, messages: list, shared_context: str) -> dict:
    """
    Main orchestration router. Sanitizes parameters, performs synonym translation,
    and handles loop resolution boundaries.
    """
    # 1. Standardize string formatting
    requested_verb = verb.strip().lower()

    # 2. Translate synonyms seamlessly on the fly
    if requested_verb in SEMANTIC_SYNONYM_MAP:
        normalized_verb = SEMANTIC_SYNONYM_MAP[requested_verb]
    else:
        normalized_verb = requested_verb

    # --- SUCCESS PATH ---
    if normalized_verb in SUPPORTED_VERBS:
        # TODO: Route normalized_verb, utterance, and shared_context to your prompt routine execution
        execution_result = f"[Successfully ran operational routine '{normalized_verb}']"

        return {
            "role": "tool",
            "tool_call_id": call_id,
            "content": json.dumps({"status": "success", "result": execution_result})
        }

    # --- FAILURE & RETRY MITIGATION LAYER ---
    past_failures = count_previous_failures(messages)

    # Check if this failure pushes the model over the max retry limit
    if past_failures < (MAX_RETRIES - 1):
        # Turn 1 or 2 Soft Error: Supply alternatives to encourage auto-correction
        error_payload = {
            "status": "error",
            "error_type": "invalid_verb",
            "message": f"The verb '{verb}' is not supported by semantic_operation.",
            "hint": "Please adjust your tool call arguments. Select an operational verb that exists inside our registry.",
            "supported_alternatives": sorted(list(SUPPORTED_VERBS))
        }
    else:
        # Turn 3 Hard Loop Breaker: Revoke tool calling and order conversational response
        error_payload = {
            "status": "hard_failure",
            "error_type": "loop_prevented",
            "message": f"CRITICAL: You failed verification parameters {MAX_RETRIES} consecutive times. Stop issuing tool requests.",
            "instruction": "Immediately break execution flow and talk to the human user in plain text. Apologize for the inconvenience, explain that your requested action is unavailable, and print a clear list of the operational tasks you are built to run."
        }

    return {
        "role": "tool",
        "tool_call_id": call_id,
        "content": json.dumps(error_payload)
    }


def machine_shop(machine_name, task, **additional):
    print('Received: ', machine_name, task)
    response = f"{machine_name}: I don't know. I can't help you with this."
    return response


# Whitelist matching your exact package roster
ALLOWED_MACHINES = {
    "thinking-machine",
    "reasoning-machine",
    "judging-machine",
    "predicting-machine",
    "summarizing-machine",
    "analyzing-machine"
}


def execute_machine_shop(call_id: str, machine_name: str, payload: str) -> dict:
    """
    Spins up the requested machine package as a secure subprocess, pipes
    the text workload payload into stdin, and grabs stdout output safely.
    """
    normalized_machine = machine_name.strip().lower()

    # 1. Verification Layer
    if normalized_machine not in ALLOWED_MACHINES:
        return {
            "role": "tool",
            "tool_call_id": call_id,
            "content": json.dumps({
                "status": "error",
                "error_type": "unregistered_machine",
                "message": f"Execution rejected. Engine '{machine_name}' is not allowed.",
                "allowed_inventory": sorted(list(ALLOWED_MACHINES))
            })
        }

    # 2. Execution Subprocess Pipeline
    try:
        process = subprocess.Popen(
            [normalized_machine], # Executes the package via active environment
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Send data and wait up to 60 seconds
        stdout_capture, stderr_capture = process.communicate(input=payload, timeout=60)

        if process.returncode == 0:
            response = {
                "status": "success",
                "engine": normalized_machine,
                "output": stdout_capture.strip()
            }
        else:
            response = {
                "status": "engine_runtime_failure",
                "engine": normalized_machine,
                "exit_code": process.returncode,
                "error_log": stderr_capture.strip()
            }

    except subprocess.TimeoutExpired:
        process.kill()
        response = {
            "status": "error",
            "error_type": "timeout",
            "message": f"Engine '{normalized_machine}' execution timed out after 60 seconds."
        }
    except Exception as system_fault:
        response = {
            "status": "error",
            "error_type": "system_fault",
            "message": f"Subprocess spawning failure: {str(system_fault)}"
        }

    return {
        "role": "tool",
        "tool_call_id": call_id,
        "content": json.dumps(response)
    }


def get_weather(location):
    # print(f"Executing weather tool for location: {location}")
    return {"temperature": "72F", "condition": "Sunny"}


"""
{
  "name": "execute_semantic_operation",
  "description": "Executes a meaning-driven or conceptual transformation over the active text context.",
  "parameters": {
    "type": "object",
    "properties": {
      "verb": {
        "type": "string",
        "description": "The specific high-level semantic action to perform.",
        "enum": ["summarize", "criticize", "hypothesize", "metaphorize", "analyze", "synthesize"]
      },
      "utterance": {
        "type": "string",
        "description": "A natural language explanation or instruction details for *how* the verb should be applied to the current context."
      }
    },
    "required": ["verb", "utterance"]
  }
}
{
  "name": "execute_semantic_operation",
  "description": "Executes a conceptual, meaning-driven transformation over the active text context.",
  "parameters": {
    "type": "object",
    "properties": {
      "verb": {
        "type": "string",
        "description": "A single imperative verb representing the core analytical or creative action required (e.g., 'summarize', 'criticize', 'hypothesize', 'verify')."
      },
      "utterance": {
        "type": "string",
        "description": "The detailed execution instruction for how the verb should be applied to the current context."
      }
    },
    "required": ["verb", "utterance"]
  }
}
final
{
  "name": "semantic_operation",
  "description": "Executes a conceptual, meaning-driven transformation or analysis over the shared text context.",
  "parameters": {
    "type": "object",
    "properties": {
      "verb": {
        "type": "string",
        "description": "A single lowercase action verb defining the semantic operation to perform (e.g., 'summarize', 'criticize', 'hypothesize', 'metaphorize')."
      },
      "utterance": {
        "type": "string",
        "description": "The detailed execution instruction provided by the calling agent explaining exactly how to execute this operation over the current context."
      }
    },
    "required": ["verb", "utterance"]
  }
}
{
  "name": "machine_shop",
  "description": "Deploys a specialized local processing micro-engine package as a system subprocess to execute complex text workloads and return stdout analytics.",
  "parameters": {
    "type": "object",
    "properties": {
      "machine_name": {
        "type": "string",
        "description": "The exact name of the target PyPI engine package. Choose carefully based on capabilities:\n- 'thinking-machine': Deep critical thinking, multi-perspective analysis, conceptual exploration.\n- 'reasoning-machine': Step-by-step logical deduction, problem-solving, structured ratiocination.\n- 'judging-machine': Quality assessments, formal critiques, appraisals, audits.\n- 'predicting-machine': Forecasting, trend projection, timeline calculation.\n- 'summarizing-machine': Core insight extraction, distillation, shortening inputs.\n- 'analyzing-machine': Technical structure processing, pattern dissection, data deconstruction."
      },
      "payload": {
        "type": "string",
        "description": "The input text text, data context, or core instructions to pass directly into the machine's stdin execution pipe."
      }
    },
    "required": ["machine_name", "payload"]
  }
}

"""
"""
The exact name of the target PyPI engine package. Choose carefully based on capabilities:
- 'thinking-machine': Deep critical thinking, multi-perspective analysis, conceptual exploration.
- 'reasoning-machine': Step-by-step logical deduction, problem-solving, structured ratiocination.
- 'judging-machine': Quality assessments, formal critiques, appraisals, audits.
- 'predicting-machine': Forecasting, trend projection, timeline calculation.
- 'summarizing-machine': Core insight extraction, distillation, shortening inputs.
- 'analyzing-machine': Technical structure processing, pattern dissection, data deconstruction.

"""