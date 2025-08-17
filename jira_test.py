import requests
from requests.auth import HTTPBasicAuth

jira_url = "https://roshinpv.atlassian.net"
issue_key = "SCRUM-5"
email = "roshinpv@gmail.com"
api_token = "ATATT3xFfGF0Ht6W_d_B_J9DFZO_f2GiFb_N1-6oJgUtt0o5Mc03a_RjMBVbxzSSdKnsWYkxk4s02kjvExSrovHbsP1zCZ_XMYChfLIqifLgJTxBDMNtC0ncLA3Qg4aFP3dDejptSI7NLuHJ05u4UYknncEtJTUPMFzxyDpLGd1D0D4ieHIeOb8=A538893F"
file_path = "./PDF_GENERATION_FOR_JIRA.md"

url = f"{jira_url}/rest/api/3/issue/{issue_key}/attachments"

headers = {
    "X-Atlassian-Token": "no-check"
}

with open(file_path, 'rb') as f:
    files = {"file": f}
    response = requests.post(
        url,
        headers=headers,
        files=files,
        auth=HTTPBasicAuth(email, api_token)
    )

print(response.status_code)
print(response.json())
