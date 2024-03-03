from language_tool_python import LanguageTool
from pydantic.dataclasses import dataclass
from dataclasses import field
from collections import Counter
from functools import partial
from tqdm.contrib.concurrent import process_map
from pathlib import Path
import shelve


@dataclass(frozen=True)
class Match_:
    category: str
    ruleId: str
    ruleIssueType: str
    offsetInContext: int = field(hash=False, repr=False)
    context: str = field(hash=False, repr=False)
    replacements: tuple[str, ...] = field(hash=False, repr=False)
    errorLength: int = field(hash=False, repr=False)
    message: str
    offset: int = field(hash=False, repr=False)
    sentence: str = field(hash=False, repr=False)

    @property
    def matchedText(self):
        """Returns the text that garnered the error (without its surrounding context)."""
        return self.context[
            self.offsetInContext : self.offsetInContext + self.errorLength
        ]


def check_file(file: Path, tool: LanguageTool) -> list[Match_]:
    text = file.read_text()
    return [Match_(**m.__dict__) for m in tool.check(text)]


def main():
    path = Path("/Users/astadnik/misc/obsidian/Main/")
    files = list(path.glob("**/*.md"))

    with shelve.open("matches") as db:
        if "matches" not in db:
            tool = LanguageTool("en-US", remote_server="http://0.0.0.0:8081")

            matches_for_file: list[list[Match_]] = process_map(
                partial(check_file, tool=tool), files[:10]
            )
            db["matches"] = [m for matches in matches_for_file for m in matches]
        matches = db["matches"]

    matches: list[Match_] = [m for m in matches if m.matchedText != "LvBS"]

    counter = Counter(matches)
    for m, count in counter.most_common(10):
        print(f"{m.message}: {m.matchedText} ({count} occurrences)")


if __name__ == "__main__":
    main()
