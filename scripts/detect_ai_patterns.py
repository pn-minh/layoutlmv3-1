#!/usr/bin/env python3
"""
AI Detection & Writing Rhythm Evaluator for Academic Theses.
Evaluates LaTeX manuscripts against standard AI detection heuristics:
- Vocabulary tell / buzzword frequency (e.g. delve, pivotal, testament, tapestry, etc.)
- Sentence length variation & burstiness (standard deviation of word counts)
- Repetitive transitions and formulaic openers
- Paragraph uniformity and passive/hedging density
Computes an estimated "% AI-generated" probability score and verifies it against
the acceptable threshold (< 20%).
"""

import os
import sys
import re
import math
import json
from pathlib import Path

# Common AI detector marker words and filler transitions
AI_BUZZWORDS = [
    "delve", "delves", "delving",
    "testament", "tapestry", "pivotal",
    "underscores", "interplay", "leverage", "leveraging",
    "foster", "fostering", "beacon", "game-changer",
    "groundbreaking", "seamlessly", "holistic", "multifaceted",
    "plethora", "myriad", "paramount", "invaluable",
    "furthermore", "moreover", "in conclusion", "it is worth noting",
    "it is important to note", "not only", "spearheaded", "synergy"
]

def strip_latex(tex_text: str) -> str:
    """Removes LaTeX commands, environments, comments, and math formulas."""
    # Remove comments
    text = re.sub(r'%.*?$', '', tex_text, flags=re.MULTILINE)
    # Remove math mode ($...$ and \[...\] and \begin{equation}...\end{equation})
    text = re.sub(r'\$\$.*?\$\$', ' ', text, flags=re.DOTALL)
    text = re.sub(r'\$.*?\$', ' ', text)
    text = re.sub(r'\\\[.*?\\\]', ' ', text, flags=re.DOTALL)
    text = re.sub(r'\\begin\{(?:equation|align|table|tabular|tikzpicture|figure).*?\}\\end\{(?:equation|align|table|tabular|tikzpicture|figure)\*?\}', ' ', text, flags=re.DOTALL)
    # Remove labels and citations
    text = re.sub(r'\\(?:cite|ref|label|pageref|url|texttt)\{[^}]*\}', ' ', text)
    # Remove generic LaTeX commands with 1 arg: \textbf{...}, \section{...}
    text = re.sub(r'\\[a-zA-Z]+\*?(?:\[[^\]]*\])?\{([^}]*)\}', r'\1', text)
    # Remove remaining lone backslash commands
    text = re.sub(r'\\[a-zA-Z]+', ' ', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def analyze_text(text: str):
    """Analyzes prose for burstiness, sentence variance, and AI markers."""
    if not text:
        return None

    # Split into sentences
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 3]
    if not sentences:
        return None

    sentence_lengths = [len(s.split()) for s in sentences if len(s.split()) > 0]
    num_sentences = len(sentence_lengths)
    total_words = sum(sentence_lengths)

    if num_sentences == 0 or total_words == 0:
        return None

    mean_length = total_words / num_sentences
    variance = sum((l - mean_length) ** 2 for l in sentence_lengths) / num_sentences
    std_length = math.sqrt(variance)

    # Count short vs medium vs long sentences
    short_sentences = sum(1 for l in sentence_lengths if l <= 12)
    medium_sentences = sum(1 for l in sentence_lengths if 13 <= l <= 28)
    long_sentences = sum(1 for l in sentence_lengths if l > 28)

    # Count AI buzzwords
    lower_text = text.lower()
    words = re.findall(r'\b[a-z\-]+\b', lower_text)
    total_clean_words = len(words)
    
    buzzword_matches = {}
    total_buzzwords = 0
    for bw in AI_BUZZWORDS:
        count = len(re.findall(r'\b' + re.escape(bw) + r'\b', lower_text))
        if count > 0:
            buzzword_matches[bw] = count
            total_buzzwords += count

    buzzword_density = (total_buzzwords / max(1, total_clean_words)) * 1000  # per 1000 words

    # Calculate AI-generated probability:
    # 1. Burstiness penalty: AI text has very uniform length (std < 5.0) -> high AI risk.
    #    Human academic text typically has std between 7.5 and 14.0.
    if std_length < 5.0:
        burstiness_risk = 35.0
    elif std_length < 7.0:
        burstiness_risk = 20.0
    elif std_length < 9.0:
        burstiness_risk = 8.0
    else:
        burstiness_risk = 2.0  # highly varied rhythm, very human

    # 2. Buzzword penalty:
    #    If buzzwords > 2.5 per 1000 words -> significant penalty
    if buzzword_density > 4.0:
        buzzword_risk = 45.0
    elif buzzword_density > 2.0:
        buzzword_risk = 25.0
    elif buzzword_density > 1.0:
        buzzword_risk = 10.0
    else:
        buzzword_risk = 1.0

    # 3. Sentence diversity ratio:
    short_ratio = short_sentences / num_sentences
    long_ratio = long_sentences / num_sentences
    # Balanced human writing has both short and long sentences
    if short_ratio >= 0.15 and long_ratio >= 0.10:
        rhythm_bonus = -5.0
    else:
        rhythm_bonus = 5.0

    raw_ai_score = max(1.5, min(95.0, burstiness_risk + buzzword_risk + rhythm_bonus))

    return {
        "num_sentences": num_sentences,
        "total_words": total_words,
        "mean_length": round(mean_length, 2),
        "std_length": round(std_length, 2),
        "short_ratio": round(short_ratio * 100, 1),
        "medium_ratio": round((medium_sentences / num_sentences) * 100, 1),
        "long_ratio": round(long_ratio * 100, 1),
        "buzzwords_found": buzzword_matches,
        "total_buzzwords": total_buzzwords,
        "buzzword_density_per_1k": round(buzzword_density, 2),
        "estimated_ai_score_percent": round(raw_ai_score, 1)
    }

def main():
    thesis_dir = Path("thesis/en")
    if not thesis_dir.exists():
        print(f"Error: Directory {thesis_dir} not found.")
        sys.exit(1)

    print("================================================================")
    print(" 🔍 RUNNING AI DETECTION & WRITING RHYTHM EVALUATOR")
    print("================================================================")

    all_tex_files = sorted(list(thesis_dir.rglob("*.tex")))
    chapter_results = {}
    aggregated_text = []

    for tex_path in all_tex_files:
        # Ignore root main.tex wrapper and acronyms
        if tex_path.resolve() == (thesis_dir / "main.tex").resolve() or tex_path.name == "acronyms.tex":
            continue
        try:
            content = tex_path.read_text(encoding="utf-8")
        except Exception as e:
            continue

        clean_prose = strip_latex(content)
        if len(clean_prose.split()) < 30:
            continue

        res = analyze_text(clean_prose)
        if res:
            rel_name = str(tex_path.relative_to(thesis_dir)).replace("\\", "/")
            chapter_results[rel_name] = res
            aggregated_text.append(clean_prose)

    # Analyze combined full thesis text
    combined_prose = " ".join(aggregated_text)
    overall_res = analyze_text(combined_prose)

    print(f"\nAnalyzed {len(chapter_results)} sections across {overall_res['total_words']} total words.")
    print("-" * 64)
    print(f"{'Section / File':<32} | {'Words':<6} | {'StdDev':<7} | {'% AI Score':<10}")
    print("-" * 64)

    for sec, stats in chapter_results.items():
        print(f"{sec:<32} | {stats['total_words']:<6} | {stats['std_length']:<7.2f} | {stats['estimated_ai_score_percent']}%")

    print("-" * 64)
    print(f"{'OVERALL THESIS (Aggregated)':<32} | {overall_res['total_words']:<6} | {overall_res['std_length']:<7.2f} | {overall_res['estimated_ai_score_percent']}%")
    print("=" * 64)

    overall_score = overall_res["estimated_ai_score_percent"]
    threshold = 20.0  # Strict academic safety limit (< 20%)

    # Write private JSON evaluation report (for local/action artifact use)
    report_data = {
        "status": "PASS" if overall_score <= threshold else "FAIL",
        "overall_ai_generated_score_percent": overall_score,
        "acceptable_threshold_percent": threshold,
        "mean_sentence_length_words": overall_res["mean_length"],
        "sentence_length_std_deviation": overall_res["std_length"],
        "total_words_evaluated": overall_res["total_words"],
        "buzzwords_found_count": overall_res["total_buzzwords"],
        "buzzwords_detected": overall_res["buzzwords_found"],
        "per_file_metrics": chapter_results
    }

    report_path = Path("ai_detection_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    # Write to GitHub Step Summary if available (visible only in Actions run)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as sf:
            sf.write("### 🛡️ AI Pattern & Writing Rhythm Evaluation (Private Audit)\n\n")
            sf.write(f"- **Overall Estimated AI-Generated Score:** `{overall_score}%`\n")
            sf.write(f"- **Acceptable Target Threshold:** `< {threshold}%`\n")
            sf.write(f"- **Verdict:** **{'✅ COMPLIANT / PASS' if overall_score <= threshold else '⚠️ ATTENTION NEEDED'}**\n")
            sf.write(f"- **Total Manuscript Words:** {overall_res['total_words']}\n")
            sf.write(f"- **Sentence Rhythm Burstiness (Std Dev):** {overall_res['std_length']} words (Healthy natural range: 7.5 - 15.0)\n")
            sf.write(f"- **AI Marker Word Density:** {overall_res['buzzword_density_per_1k']} per 1k words\n\n")
            sf.write("| Section | Words | Sentence StdDev | % AI Score |\n")
            sf.write("|:---|:---:|:---:|:---:|\n")
            for sec, stats in chapter_results.items():
                sf.write(f"| `{sec}` | {stats['total_words']} | {stats['std_length']} | {stats['estimated_ai_score_percent']}% |\n")
            sf.write(f"| **Overall Aggregated** | **{overall_res['total_words']}** | **{overall_res['std_length']}** | **{overall_score}%** |\n\n")

    if overall_score <= threshold:
        print(f"✅ VERDICT: PASS! Overall AI score ({overall_score}%) is within acceptable threshold (< {threshold}%).")
        sys.exit(0)
    else:
        print(f"⚠️ VERDICT: FAIL! Overall AI score ({overall_score}%) exceeds acceptable threshold (< {threshold}%).")
        sys.exit(1)

if __name__ == "__main__":
    main()
