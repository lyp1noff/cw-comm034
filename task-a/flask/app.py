import os
import uuid
import json
import hashlib
from flask import Flask, request, jsonify, render_template
from google.cloud import storage, firestore

app = Flask(__name__)

BUCKET_IN = os.environ.get("BUCKET_IN")

storage_client = storage.Client()
db = firestore.Client()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "No files provided"}), 400

    batch_id = str(uuid.uuid4())
    total_count = len(files)
    
    do_freq = request.form.get("frequency", "true").lower()
    do_starts = request.form.get("starts", "true").lower()
    do_stats = request.form.get("stats", "true").lower()

    batch_ref = db.collection("batches").document(batch_id)
    batch_ref.set({
        "batch_id": batch_id,
        "total_count": total_count,
        "processed_count": 0,
        "created_at": firestore.SERVER_TIMESTAMP
    })

    bucket = storage_client.bucket(BUCKET_IN)
    for file in files:
        # content = file.read() # Dangerous if file is big, used for md5 hash
        # file_hash = hashlib.md5(content).hexdigest()
        # blob = bucket.blob(f"{batch_id}/{file_hash}")
        file_uid = str(uuid.uuid4())

        blob = bucket.blob(f"{batch_id}/{file_uid}")
        blob.metadata = {
            "original_filename": file.filename,
            "do_frequency": do_freq,
            "do_starts": do_starts,
            "do_stats": do_stats
        }

        # blob.upload_from_string(content)
        blob.upload_from_file(file)
        

    return jsonify({
        "batch_id": batch_id, 
        "total_files": total_count,
        "status": "upload_complete"
    }), 202

@app.route('/results/<batch_id>', methods=['GET'])
def get_results(batch_id):
    batch_ref = db.collection("batches").document(batch_id)
    batch_doc = batch_ref.get()
    
    if not batch_doc.exists:
        return jsonify({"error": "Batch not found"}), 404
    
    batch_info = batch_doc.to_dict()
    
    results_docs = batch_ref.collection("results").stream()
    final_results = []
    
    for doc in results_docs:
        raw = doc.to_dict()
        analysis_data = json.loads(raw.get("data", "{}"))
        
        final_results.append({
            "file_name": raw.get("file_name"),
            "processed_at": str(raw.get("processed_at")),
            "analysis": analysis_data.get("analysis")
        })

    return jsonify({
        "batch_id": batch_id,
        "progress": {
            "total": batch_info.get("total_count", 0),
            "processed": batch_info.get("processed_count", 0)
        },
        "results": final_results
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))