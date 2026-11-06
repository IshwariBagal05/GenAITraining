from dataclasses import dataclass, asdict


@dataclass
class Record:
    topic: str
    insurance_type: str
    rule_summary: str
    time_limit: str
    who_to_contact: str
    source_url: str

    def to_dict(self):
        return asdict(self)