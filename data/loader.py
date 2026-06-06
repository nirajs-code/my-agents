from dataclasses import dataclass
import os
from pypdf import PdfReader
from dotenv import load_dotenv
load_dotenv(override=True)


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

    return ProfileData(
        name=os.getenv("PROFILE_NAME", "Niraj Singh"),
        summary=summary, 
        linkedin=linkedin
    )
