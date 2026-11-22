"""Deterministic, auditable canonical labels for aggregation and evaluation."""

from __future__ import annotations

import re

CANONICALIZATION_VERSION = "2026-10-24"
EVALUATION_CANONICALIZATION_VERSION = "2026-10-28-v3"

# Only explicit, review-domain synonyms belong here. New mappings require a
# documented decision so product-level trends remain reproducible.
ALIASES = {
    "audio quality": "sound quality", "sound": "sound quality", "sound fidelity": "sound quality",
    "sound quality for audio books": "sound quality", "sound quality for telephone calls": "call quality",
    "noise cancelling": "noise cancellation", "noise canceling": "noise cancellation",
    "noise reduction": "noise cancellation", "noise isolation": "noise cancellation",
    "sound isolation": "noise cancellation", "ambient noise blocking": "noise cancellation",
    "background noise": "noise cancellation",
    "case": "carrying case", "audio cord": "cable", "cord": "cable",
    "charging cable": "cable", "wireline attachment": "cable", "corded option": "cable",
    "construction": "build quality", "construction quality": "build quality",
    "sturdiness": "build quality", "materials": "build quality", "material": "build quality",
    "fragility": "build quality", "reliability": "build quality", "quality": "build quality",
    "volume": "volume control", "loudness": "volume control", "volume level": "volume control",
    "volume controller": "volume control", "inline volume control": "volume control",
    "touch volume controls": "volume control", "touch volume slider": "volume control",
    "battery": "battery life", "battery replacement": "battery life",
    "pairing": "connectivity", "connection stability": "connectivity",
    "bluetooth interference": "connectivity", "bluetooth signal": "connectivity",
    "wireless functionality": "connectivity", "wireless range": "connectivity",
    "customer support": "customer service", "seller service": "customer service",
    "shipping": "delivery", "ear comfort": "comfort", "warmth": "comfort",
    "temperature": "comfort", "ear foam/temperature": "comfort",
    "microphone quality": "microphone", "phone calls": "call quality",
}

# These mappings are intentionally conservative. They are used only for the
# separate canonical-label consistency evaluation; original checkpoint values
# are never overwritten. The policy is documented in
# data/validation/canonical_label_policy_v2.md.
FIELD_ALIASES = {
    "customer_issues": {
        "poor sound quality": "poor sound quality",
        "terrible sound quality": "poor sound quality",
        "sound quality is below expectations": "poor sound quality",
        "not very comfortable": "discomfort",
        "less comfortable than the cx200 sennheisers": "discomfort",
        "headset slips on the head": "poor fit",
        "earbuds kept falling out": "poor fit",
        "poor noise cancellation": "weak noise cancellation",
        "shipping was an issue": "delivery issue",
        "headphones broke quickly": "poor durability",
        "customer support has not responded": "customer service issue",
    },
    "feature_requests": {
        "volume control": "add volume control",
        "volume up or down buttons": "add volume control",
        "volume controls that are actual buttons": "add volume control",
        "a little more bass": "improve bass",
        "better bass": "improve bass",
        "add a microphone": "add microphone",
        "longer cable": "provide longer cable",
        "fix the casing durability": "improve durability",
        "come with more sizes": "provide more fit sizes",
    },
    "use_cases": {
        "working out": "exercise",
        "workouts": "exercise",
        "workout": "exercise",
        "work out": "exercise",
        "gym": "exercise",
        "gym workouts": "exercise",
        "working out at the gym": "exercise",
        "exercising": "exercise",
        "jogging": "running",
        "runs": "running",
        "listen to music": "listening to music",
        "music": "listening to music",
        "listening": "listening to music",
        "phone calls": "making calls",
        "talking on the phone": "making calls",
        "calls": "making calls",
        "traveling": "travel",
    },
    "positive_points": {
        "great sound": "good sound quality",
        "great sound quality": "good sound quality",
        "good sound": "good sound quality",
        "good sound quality": "good sound quality",
        "amazing sound quality": "good sound quality",
        "amazing sound": "good sound quality",
        "excellent sound quality": "good sound quality",
        "excellent sound": "good sound quality",
        "sound great": "good sound quality",
        "very comfortable": "comfortable fit",
        "comfortable": "comfortable fit",
        "comfortable to wear": "comfortable fit",
        "comfortable fit": "comfortable fit",
        "great price": "good value",
        "good price": "good value",
        "affordable price": "good value",
        "great value": "good value",
        "good value": "good value",
        "great value for the price": "good value",
        "good value for the price": "good value",
        "worth the money": "good value",
        "easy to use": "easy to use",
        "works great": "works well",
    },
    "negative_points": {
        "poor quality": "poor build quality",
        "bad construction": "poor build quality",
        "not very comfortable": "discomfort",
        "not the most comfortable": "discomfort",
        "not noise cancelling": "weak noise cancellation",
        "not noise isolating": "weak noise cancellation",
        "poor sound quality": "poor sound quality",
        "not worth the money": "poor value",
        "waste of money": "poor value",
        "headphones broke way too fast": "poor durability",
    },
}

# Ordered patterns cover recurring concepts observed in the original 1,632
# schema-valid extraction records. They remain field-specific: a phrase is
# never compared across different output fields.
FIELD_PATTERNS = {
    "customer_issues": (
        (r"charg|battery.*(?:drain|dead|fail|hold)|(?:drain|dead|fail|hold).*battery", "battery or charging problem"),
        (r"pair|connect|bluetooth|disconnect|sync", "connectivity problem"),
        (r"break|broke|crack|snap|hinge|fall apart|wear out|durab", "poor durability"),
        (r"comfort|uncomfortable|sore|warm|pressure|hurt|pain|cushion", "discomfort"),
        (r"fit|slip|fall(?:ing)? out|stay in place|loose", "poor fit"),
        (r"volume|touch.?control|track control", "volume or controls problem"),
        (r"sound|audio|bass|treble|hiss|static|muffl|distort|crackl|noise", "audio quality problem"),
        (r"cable|cord|wire", "cable problem"),
        (r"support|shipping|deliver", "service or delivery problem"),
    ),
    "feature_requests": (
        (r"volume|sound controls?|dial|rocker", "improve volume control"),
        (r"bass", "improve bass"),
        (r"cushion|pad|foam|comfort|ear.?cup", "improve comfort"),
        (r"cable|cord|wire", "improve cable"),
        (r"mic|microphone", "add or improve microphone"),
        (r"fit|stay in.*ear|ear.?hook|size|xl", "improve fit"),
        (r"bluetooth|connect|wireless", "improve connectivity"),
        (r"durab|solid structure|hinge", "improve durability"),
        (r"bass", "improve bass"),
    ),
    "use_cases": (
        (r"gym|work.?out|exercis|treadmill|run|jogg|bike|motorcycle", "exercise"),
        (r"phone call|calls?|skype|conference", "making calls"),
        (r"music|audio book|playlist|ipod|song", "listening to audio"),
        (r"game|xbox|ps[34]", "gaming"),
        (r"travel|flight|plane|commut|train|car", "travel or commute"),
        (r"work|office|school|desk|factory|studio", "work or study"),
        (r"yard work|power tools?|mow", "yard work"),
        (r"sleep|bed|night", "sleeping"),
    ),
    "positive_points": (
        (r"sound|audio|bass|treble|fidelity|clear", "good sound quality"),
        (r"comfort|comfortable|cushion", "comfortable fit"),
        (r"fit|stay in.*ear|snug", "good fit"),
        (r"price|value|worth|afford|cheap|inexpensive", "good value"),
        (r"battery|charge", "good battery life"),
        (r"noise cancell|noise isolat|noise reduc|block.*noise", "effective noise cancellation"),
        (r"durab|sturdy|solid", "good durability"),
        (r"mic|microphone", "good microphone"),
        (r"cable|cord", "good cable"),
        (r"connect|bluetooth|pair", "good connectivity"),
        (r"easy to use|easy setup|simple", "easy to use"),
        (r"works?(?: very)? (?:well|great)|worked great", "works well"),
    ),
    "negative_points": (
        (r"charg|battery.*(?:drain|dead|fail|hold)|(?:drain|dead|fail|hold).*battery", "battery or charging problem"),
        (r"pair|connect|bluetooth|disconnect|sync", "connectivity problem"),
        (r"break|broke|crack|snap|hinge|fall apart|wear out|durab", "poor durability"),
        (r"comfort|uncomfortable|sore|warm|pressure|hurt|pain|cushion", "discomfort"),
        (r"fit|slip|fall(?:ing)? out|stay in place|loose", "poor fit"),
        (r"volume|touch.?control|track control", "volume or controls problem"),
        (r"sound|audio|bass|treble|hiss|static|muffl|distort|crackl|noise", "audio quality problem"),
        (r"cable|cord|wire", "cable problem"),
        (r"not worth|waste of money|expensive", "poor value"),
        (r"does not work|did not work|stopped working|no sound", "functional failure"),
    ),
}


def normalize_label(label: str) -> str:
    """Normalize formatting only; it does not infer a different concept."""
    return re.sub(r"\s+", " ", re.sub(r"[-_/]", " ", label.lower())).strip()


def canonicalize_aspect(label: str) -> str:
    """Return the configured canonical label while retaining caller's original."""
    normalized = normalize_label(label)
    return ALIASES.get(normalized, normalized)


def canonicalize_field_value(field: str, label: str) -> str:
    """Canonicalize a supported evaluation field without inferring new facts.

    Unmapped values intentionally remain normalized rather than being forced
    into a broad category. This retains distinctions that the policy does not
    explicitly define.
    """
    normalized = normalize_label(label)
    if field == "aspects":
        return canonicalize_aspect(normalized)
    mapped = FIELD_ALIASES.get(field, {}).get(normalized)
    if mapped:
        return mapped
    for pattern, canonical_label in FIELD_PATTERNS.get(field, ()):
        if re.search(pattern, normalized):
            return canonical_label
    return normalized
