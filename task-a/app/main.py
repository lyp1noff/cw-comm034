import os
import json
import functions_framework
from google.cloud import storage
import text_processor

@functions_framework.cloud_event
def process_file(cloud_event):
    data = cloud_event.data
    bucket_name = data["bucket"]
    file_name = data["name"]
    
    client = storage.Client()
    input_bucket = client.bucket(bucket_name)
    blob = input_bucket.blob(file_name)
    
    analysis_tasks = os.environ.get("ANALYSIS_TASKS", "frequency,starts,stats").split(",")

    content = blob.download_as_text()
    
    result = text_processor.run_analysis(content, tasks=analysis_tasks)

    output_bucket_name = os.environ.get("OUTPUT_BUCKET")
    output_bucket = client.bucket(output_bucket_name)
    output_blob = output_bucket.blob(f"result_{file_name}.json")
    
    output_blob.upload_from_string(
        json.dumps(result, ensure_ascii=False, indent=2),
        content_type="application/json"
    )
