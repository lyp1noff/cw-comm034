import json
import functions_framework
from google.cloud import storage, firestore
import text_processor

db = firestore.Client()
storage_client = storage.Client()

@functions_framework.cloud_event
def process_file(cloud_event):
    data = cloud_event.data
    bucket_name = data["bucket"]
    object_name = data["name"]
    
    metadata = data.get("metadata", {})
    batch_id = metadata.get("batch_id", "default_batch")
    file_name = metadata.get("original_filename", object_name)
    batch_id, doc_id = object_name.split('/')
    
    def str_to_bool(s):
        return str(s).lower() == "true"

    analysis_tasks = []
    if str_to_bool(metadata.get("do_frequency", "true")): analysis_tasks.append('frequency')
    if str_to_bool(metadata.get("do_starts", "true")): analysis_tasks.append('starts')
    if str_to_bool(metadata.get("do_stats", "true")): analysis_tasks.append('stats')

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(object_name)
    content = blob.download_as_text()
    
    result = text_processor.run_analysis(content, tasks=analysis_tasks)

    batch_ref = db.collection("batches").document(batch_id)
    
    analysis_data = {
        "analysis": result,
        "meta": {
            "file_name": file_name,
            "tasks": analysis_tasks
        }
    }

    json_payload = json.dumps(analysis_data, ensure_ascii=False)
    result_ref = batch_ref.collection("results").document(doc_id)
    
    result_ref.set({
        "data": json_payload,
        "processed_at": firestore.SERVER_TIMESTAMP,
        "file_name": file_name
    })

    batch_ref.update({
        "processed_count": firestore.Increment(1)
    })

    print(f"Processed {file_name} for batch {batch_id}")