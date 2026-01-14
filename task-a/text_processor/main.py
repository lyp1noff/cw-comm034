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
    
    metadata = data.get("metadata", {})
    batch_id = metadata.get("batch_id", "default_batch")
    
    def str_to_bool(s):
        return s.lower() == "true"

    analysis_tasks = []
    if str_to_bool(metadata.get("do_frequency", "true")):
        analysis_tasks.append('frequency')
    if str_to_bool(metadata.get("do_starts", "true")):
        analysis_tasks.append('starts')
    if str_to_bool(metadata.get("do_stats", "true")):
        analysis_tasks.append('stats')

    client = storage.Client()
    input_bucket = client.bucket(bucket_name)
    blob = input_bucket.blob(file_name)
    
    content = blob.download_as_text()
    
    result = text_processor.run_analysis(content, tasks=analysis_tasks)
    
    result["meta"] = {
        "batch_id": batch_id,
        "processed_tasks": analysis_tasks
    }

    output_bucket_name = os.environ.get("OUTPUT_BUCKET")
    output_bucket = client.bucket(output_bucket_name)
    
    output_path = f"{batch_id}/result_{file_name.split('/')[-1]}.json"
    output_blob = output_bucket.blob(output_path)
    
    output_blob.upload_from_string(
        json.dumps(result, ensure_ascii=False, indent=2),
        content_type="application/json"
    )
