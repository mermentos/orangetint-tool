import os
import uuid
import zipfile
import tempfile
from flask import render_template, request, flash, redirect, url_for, send_file, jsonify, session
from werkzeug.utils import secure_filename
from app import app
from image_processor import process_image, ALLOWED_EXTENSIONS
import logging

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    # Get processed files from session if available
    if 'processed_files' not in session:
        session['processed_files'] = []
    session.permanent = True
    processed_files = session.get('processed_files', [])
    return render_template('index.html', processed_files=processed_files)

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        flash('No files selected', 'error')
        return redirect(url_for('index'))
    
    files = request.files.getlist('files')
    
    if not files or all(file.filename == '' for file in files):
        flash('No files selected', 'error')
        return redirect(url_for('index'))
    
    processed_files = []
    errors = []
    
    for file in files:
        if file and file.filename and file.filename != '':
            if allowed_file(file.filename):
                try:
                    # Generate unique filename to avoid conflicts
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    
                    # Save uploaded file
                    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    file.save(upload_path)
                    
                    # Process the image
                    output_filename = process_image(unique_filename)
                    
                    if output_filename:
                        processed_files.append({
                            'original': filename,
                            'processed': output_filename,
                            'original_path': unique_filename
                        })
                        logging.info(f"Successfully processed {filename}")
                    else:
                        errors.append(f"Failed to process {filename}")
                        logging.error(f"Failed to process {filename}")
                        
                except Exception as e:
                    errors.append(f"Error processing {file.filename}: {str(e)}")
                    logging.error(f"Error processing {file.filename}: {str(e)}")
            else:
                errors.append(f"Invalid file type: {file.filename}")
    
    if errors:
        for error in errors:
            flash(error, 'error')
    
    if processed_files:
        # Store processed files in session to persist across page navigation
        if 'processed_files' not in session:
            session['processed_files'] = []
        session['processed_files'].extend(processed_files)
        session.permanent = True
        session.modified = True
        
        flash(f"Successfully processed {len(processed_files)} image(s)", 'success')
        return render_template('results.html', processed_files=session['processed_files'])
    else:
        flash('No files were processed successfully', 'error')
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    try:
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        if os.path.exists(output_path):
            return send_file(output_path, as_attachment=True)
        else:
            flash('File not found', 'error')
            return redirect(url_for('index'))
    except Exception as e:
        logging.error(f"Error downloading file {filename}: {str(e)}")
        flash('Error downloading file', 'error')
        return redirect(url_for('index'))

@app.route('/preview/<original_filename>/<processed_filename>')
def preview_comparison(original_filename, processed_filename):
    try:
        original_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
        processed_path = os.path.join(app.config['OUTPUT_FOLDER'], processed_filename)
        
        if not os.path.exists(original_path) or not os.path.exists(processed_path):
            flash('Images not found', 'error')
            return redirect(url_for('index'))
        
        # Ensure session is maintained
        session.permanent = True
        
        return render_template('preview.html', 
                             original_filename=original_filename,
                             processed_filename=processed_filename)
    except Exception as e:
        logging.error(f"Error loading preview: {str(e)}")
        flash('Error loading preview', 'error')
        return redirect(url_for('index'))

@app.route('/results')
def show_results():
    """Show results page with current processed files"""
    session.permanent = True
    processed_files = session.get('processed_files', [])
    return render_template('results.html', processed_files=processed_files)

@app.route('/image/<path:folder>/<filename>')
def serve_image(folder, filename):
    """Serve images from upload or output folders"""
    try:
        if folder == 'uploads':
            return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        elif folder == 'output':
            return send_file(os.path.join(app.config['OUTPUT_FOLDER'], filename))
        else:
            return "Invalid folder", 404
    except Exception as e:
        logging.error(f"Error serving image {folder}/{filename}: {str(e)}")
        return "Image not found", 404

@app.route('/download_all')
def download_all():
    """Download all processed images as a ZIP file"""
    try:
        processed_files = session.get('processed_files', [])
        if not processed_files:
            flash('No processed files to download', 'error')
            return redirect(url_for('index'))
        
        # Create temporary ZIP file
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        
        with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_info in processed_files:
                output_path = os.path.join(app.config['OUTPUT_FOLDER'], file_info['processed'])
                if os.path.exists(output_path):
                    # Use original filename in ZIP
                    zip_file.write(output_path, file_info['processed'])
        
        temp_zip.close()
        
        def remove_file(response):
            try:
                os.unlink(temp_zip.name)
            except Exception:
                pass
            return response
        
        return send_file(
            temp_zip.name,
            as_attachment=True,
            download_name='sora_corrected_images.zip',
            mimetype='application/zip'
        )
        
    except Exception as e:
        logging.error(f"Error creating ZIP download: {str(e)}")
        flash('Error creating download archive', 'error')
        return redirect(url_for('index'))

@app.route('/remove_file/<filename>')
def remove_file(filename):
    """Remove a specific processed file from session and filesystem"""
    try:
        processed_files = session.get('processed_files', [])
        
        # Find and remove the file from session
        updated_files = []
        file_to_remove = None
        
        for file_info in processed_files:
            if file_info['processed'] == filename:
                file_to_remove = file_info
            else:
                updated_files.append(file_info)
        
        if file_to_remove:
            # Remove from filesystem
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], file_to_remove['original_path'])
            
            if os.path.exists(output_path):
                os.remove(output_path)
            if os.path.exists(upload_path):
                os.remove(upload_path)
            
            # Update session
            session['processed_files'] = updated_files
            session.permanent = True
            session.modified = True
            flash(f'Removed {file_to_remove["original"]}', 'success')
        else:
            flash('File not found', 'error')
            
    except Exception as e:
        logging.error(f"Error removing file {filename}: {str(e)}")
        flash('Error removing file', 'error')
    
    # Get current page context to redirect appropriately
    referrer = request.environ.get('HTTP_REFERER')
    if referrer and 'results' in referrer:
        return render_template('results.html', processed_files=session.get('processed_files', []))
    else:
        return redirect(url_for('index'))

@app.route('/cleanup', methods=['POST'])
def cleanup_files():
    """Clean up uploaded and processed files"""
    try:
        # Clean uploads folder
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            if filename != '.gitkeep':
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                os.remove(file_path)
        
        # Clean output folder
        for filename in os.listdir(app.config['OUTPUT_FOLDER']):
            if filename != '.gitkeep':
                file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
                os.remove(file_path)
        
        # Clear session
        session.pop('processed_files', None)
        session.permanent = True
        session.modified = True
        
        flash('Files cleaned up successfully', 'success')
    except Exception as e:
        logging.error(f"Error during cleanup: {str(e)}")
        flash('Error during cleanup', 'error')
    
    return redirect(url_for('index'))

@app.errorhandler(413)
def too_large(e):
    flash('File is too large. Maximum size is 16MB.', 'error')
    return redirect(url_for('index'))
