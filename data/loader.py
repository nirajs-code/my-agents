from dataclasses import dataclass
from pypdf import PdfReader


@dataclass
class ProfileData:
    name: str
    summary: str
    linkedin: str


def load_profile() -> ProfileData:
    with open("sample-data/summary.txt", "r", encoding="utf-8") as f:
        summary = f.read()

    linkedin = ""
    reader = PdfReader("sample-data/profile.pdf")
    for page in reader.pages:
        text = page.extract_text()
        if text:
            linkedin += text

    return ProfileData(name="Niraj Singh", summary=summary, linkedin=linkedin)
