from dotenv import load_dotenv
load_dotenv()

from gates.utils.splunk_integration import execute_splunk_query
import os

if __name__ == "__main__":
    print("SPLUNK_URL:", os.getenv("SPLUNK_URL"))
    print("SPLUNK_TOKEN:", os.getenv("SPLUNK_TOKEN"))
    query = 'search index=* | head 5'
    app_id = os.getenv('TEST_APP_ID', None)
    print(f"Running Splunk query: {query}")
    if app_id:
        print(f"Using app_id: {app_id}")
    result = execute_splunk_query(query, app_id, earliest_time="-10d")
    print("\nSplunk _raw results:")
    if result.get('results'):
        for row in result['results']:
            print(row.get('_raw'))
    else:
        print("No results. Full response for debugging:")
        print(result) 