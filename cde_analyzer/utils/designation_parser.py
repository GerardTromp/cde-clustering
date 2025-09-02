# utils/designation_parser.oy
import re
from typing import List, Dict, Optional

# Precompiled regex patterns
QUESTION_PATTERNS = [
    re.compile(r"Question Text"),
    re.compile(r"Alternat(?:e|ive) Question Text"),
    re.compile(r"Question"),
]

NAME_PATTERNS = [
    re.compile(r"Primary Name"),
    re.compile(r"Long Common Name"),
    re.compile(r"Short Name"),
    re.compile(r"Shortname"),
]


def match_by_patterns(
    tags: List[str], designation: Dict, patterns: List[re.Pattern]
) -> Optional[str]:
    for tag in tags:
        for pattern in patterns:
            if pattern.search(tag):
                return designation.get("designation")
    return None


def extract_name_and_question_from_designations(
    designations: List[Dict],
) -> Dict[str, Optional[str]]:
    name = None
    question = None

    for designation in designations:
        tags = designation.get("tags") or []
        if not isinstance(tags, list):
            continue

        if question is None:
            question = match_by_patterns(tags, designation, QUESTION_PATTERNS)
        if name is None:
            name = match_by_patterns(tags, designation, NAME_PATTERNS)
        if name and question:
            break

    # Fallbacks
    if question is None and len(designations) > 1:
        question = designations[1].get("designation")
    if name is None and len(designations) > 0:
        name = designations[0].get("designation")

    return {"Name": name, "Question": question}
