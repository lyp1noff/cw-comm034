from flask import Flask, request, jsonify
from google.cloud import storage
import uuid
import os
import datetime

app = Flask(__name__)

BUCKET_IN = os.environ.get("BUCKET_IN")
BUCKET_OUT = os.environ.get("BUCKET_OUT")
storage_client = storage.Client()

@app.route('/upload', methods=['POST'])
def upload_files():
    files = request.files.getlist("files")
    batch_id = str(uuid.uuid4())
    
    do_freq = request.form.get("frequency", "true").lower()
    do_starts = request.form.get("starts", "true").lower()
    do_stats = request.form.get("stats", "true").lower()

    bucket = storage_client.bucket(os.environ.get("BUCKET_IN"))

    for file in files:
        blob = bucket.blob(f"{batch_id}/{file.filename}")
        blob.metadata = {
            "batch_id": batch_id,
            "do_frequency": do_freq,
            "do_starts": do_starts,
            "do_stats": do_stats
        }
        blob.upload_from_file(file)

    return jsonify({"batch_id": batch_id, "tasks": {"freq": do_freq, "starts": do_starts, "stats": do_stats}}), 202

@app.route('/results/<batch_id>', methods=['GET'])
def get_results(batch_id):
    bucket = storage_client.bucket(BUCKET_OUT)
    blobs = bucket.list_blobs(prefix=f"{batch_id}/")
    
    results = []
    for blob in blobs:
        url = blob.generate_signed_url(
            version="v4",
            expiration=datetime.timedelta(minutes=15),
            method="GET"
        )
        results.append({
            "name": blob.name.split("/")[-1],
            "download_url": url
        })
    
    return jsonify({"batch_id": batch_id, "results": results})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))