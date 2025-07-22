import requests
import os
from utils.db_integration import fetch_jira_stories
import json

def _extract_report_summary(report_path):
    """
    Extracts a summary from the HTML or JSON report file.
    For HTML, returns a generic message. For JSON, extracts compliance score and gate stats.
    """
    if report_path.endswith('.json'):
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            score = data.get('overall_score') or data.get('summary', {}).get('overall_score')
            total_gates = data.get('summary', {}).get('total_gates') or len(data.get('gates', []))
            passed = data.get('summary', {}).get('passed_gates')
            failed = data.get('summary', {}).get('failed_gates')
            warning = data.get('summary', {}).get('warning_gates')
            summary = f"Hard Gate Assessment Summary:\n"
            if score is not None:
                summary += f"- Compliance Score: {score:.1f}%\n"
            if total_gates is not None:
                summary += f"- Total Gates: {total_gates}\n"
            if passed is not None:
                summary += f"- Gates Met: {passed}\n"
            if warning is not None:
                summary += f"- Partially Met: {warning}\n"
            if failed is not None:
                summary += f"- Not Met: {failed}\n"
            summary += "\nSee attached report for full details."
            return summary
        except Exception as ex:
            return f"Hard Gate Assessment completed. See attached report for details. (Summary extraction failed: {ex})"
    else:
        return "Hard Gate Assessment completed. See attached HTML report for full details."

def upload_report_to_jira(jira_url, jira_user, jira_token, app_id, report_path, report_type):
    """
    For each JIRA story for the app_id, adds a comment with a summary and attaches the report file.
    Returns a dict with results for each story.
    """
    results = []
    stories = fetch_jira_stories(app_id=app_id)
    if not stories:
        return {"success": False, "message": f"No JIRA stories found for app_id {app_id}", "results": []}
    if not os.path.exists(report_path):
        return {"success": False, "message": f"Report file not found: {report_path}", "results": []}
    with open(report_path, 'rb') as f:
        report_data = f.read()
    filename = os.path.basename(report_path)
    summary = _extract_report_summary(report_path)
    for story in stories:
        story_result = {"story": story}
        try:
            # 1. Add comment
            comment_url = f"{jira_url.rstrip('/')}/rest/api/2/issue/{story}/comment"
            comment_payload = {"body": summary}
            comment_resp = requests.post(
                comment_url,
                auth=(jira_user, jira_token),
                headers={"Content-Type": "application/json"},
                data=json.dumps(comment_payload),
                verify=False,
                timeout=30
            )
            if comment_resp.status_code in (200, 201):
                story_result["comment"] = "success"
            else:
                story_result["comment"] = f"HTTP {comment_resp.status_code}: {comment_resp.text}"
            # 2. Attach report
            attach_url = f"{jira_url.rstrip('/')}/rest/api/2/issue/{story}/attachments"
            attach_headers = {"X-Atlassian-Token": "no-check"}
            attach_files = {'file': (filename, report_data, 'application/octet-stream')}
            attach_resp = requests.post(
                attach_url,
                headers=attach_headers,
                auth=(jira_user, jira_token),
                files=attach_files,
                verify=False,
                timeout=30
            )
            if attach_resp.status_code in (200, 201):
                story_result["attachment"] = "success"
            else:
                story_result["attachment"] = f"HTTP {attach_resp.status_code}: {attach_resp.text}"
            story_result["success"] = story_result["comment"] == "success" and story_result["attachment"] == "success"
        except Exception as ex:
            story_result["success"] = False
            story_result["error"] = str(ex)
        results.append(story_result)
    return {"success": True, "results": results} 