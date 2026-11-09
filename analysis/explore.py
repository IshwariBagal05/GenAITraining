from pathlib import Path
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data" / "sample_records.json"

df = pd.read_json(DATA)

print(f"Loaded {len(df)} records\n")

# Fact 1: how records split across insurance types
print("Fact 1: records per insurance type")
print(df["insurance_type"].value_counts().to_string(), "\n")

# Fact 2: how many topics have no stated time limit
no_limit = df[df["time_limit"].str.contains("Not specified", case=False)]
print(f"Fact 2: {len(no_limit)} of {len(df)} topics have no stated time limit")
print("   e.g.", ", ".join(no_limit["topic"].head(3)), "\n")

# Fact 3: which rule summary is longest, i.e. the most complex topic
lengths = df["rule_summary"].str.len()
longest = df.loc[lengths.idxmax()]
print(f"Fact 3: longest rule summary is '{longest['topic']}' "
      f"({lengths.max()} characters, average {lengths.mean():.0f})")