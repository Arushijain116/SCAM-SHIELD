import pandas as pd
import random

scam_templates = [
    "You won {amount} rupees click here",
    "Your bank account is suspended verify now",
    "Urgent update your KYC immediately",
    "Win a free {item} now click link",
    "Your OTP is required to complete transaction",
    "Click here to claim your prize",
    "Account blocked verify urgently",
    "Limited offer get {item} free now",
    "Congratulations you won {amount}",
    "Payment failed retry using this link"
]

safe_templates = [
    "Please submit your assignment",
    "Let's meet tomorrow for project",
    "Dinner tonight?",
    "Your order has been delivered",
    "Meeting at 3 PM",
    "Call me when free",
    "Exam is next week",
    "Project deadline is tomorrow",
    "Notes uploaded check portal",
    "Class starts at 10 AM"
]

amounts = ["500", "1000", "5000", "10000"]
items = ["iPhone", "laptop", "voucher", "gift card"]

data = []

# Generate scam data
for _ in range(300):
    text = random.choice(scam_templates)
    text = text.replace("{amount}", random.choice(amounts))
    text = text.replace("{item}", random.choice(items))
    data.append([text, "scam"])

# Generate safe data
for _ in range(300):
    text = random.choice(safe_templates)
    data.append([text, "safe"])

df = pd.DataFrame(data, columns=["text", "label"])

df.to_csv("scams.csv", index=False)

print("✅ Dataset generated: 600 samples")