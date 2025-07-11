import os
import json
from datetime import datetime
from utils.logging import LogType, log


def collect_chunks(chunk_logfile_path, general_logfile_path, chunk_data, chunk_output_dir, chunk_num):
    try:
        os.makedirs(chunk_output_dir, exist_ok=True)
        chunk_name = f"chunk_{chunk_num}"
        chunk_path = os.path.join(chunk_output_dir, f"{chunk_name}.pchunk")
        with open(chunk_path, 'wb') as f:
            f.write(chunk_data)
        #log for saved chunk
        log(f"Chunk {chunk_name} saved at {chunk_path}", log_type=LogType.INFO, status="Success", general_logfile_path=general_logfile_path)
        new_entry = {
            chunk_name: {
                "path": chunk_path,
                "creation_time": datetime.now().isoformat()
            }
        }

        existing_data = {}
        if os.path.exists(chunk_logfile_path):
            with open(chunk_logfile_path, 'r') as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    #log for invalid JSON and starting over
                    log("Invalid JSON in chunk log file, starting over.", log_type=LogType.ERROR, status="Failure", general_logfile_path=general_logfile_path)
                    pass
        if 'chunk_output_dir' not in existing_data:
            existing_data['chunk_output_dir'] = chunk_output_dir
        existing_data.update(new_entry)
        with open(chunk_logfile_path, 'w') as f:
            json.dump(existing_data, f, indent=2)
        #log for updated chunk log file
        log(f"Chunk log file updated at {chunk_logfile_path}", log_type=LogType.INFO, status="Success", general_logfile_path=general_logfile_path)
    except Exception as e:
        #log for error in collect_chunks
        log(f"Error collecting chunk {chunk_name}: {e}", log_type=LogType.ERROR, status="Failure", general_logfile_path=general_logfile_path)
        raise

def join_chunks(chunk_output_dir, chunk_logfile_path,general_logfile_path):
    try:
        if not os.path.exists(chunk_logfile_path):
            raise FileNotFoundError(f"Log file not found: {chunk_logfile_path}")

        with open(chunk_logfile_path, 'r') as log_file:
            try:
                chunk_info = json.load(log_file)
            except json.JSONDecodeError as e:
                #log(LogType.ERROR, f"Invalid JSON in chunk log file: {e}", None)
                log(f"Invalid JSON in chunk log file: {e}", log_type=LogType.ERROR, status="Failure", general_logfile_path=general_logfile_path)
                raise

        if not isinstance(chunk_info, dict):
            raise ValueError("Chunk log file does not contain a valid dictionary.")
        
        output_dir = chunk_info.get("chunk_output_dir")

        # chunks = sorted(chunk_info.items(), key=lambda x: x[0])
        final_file_path = os.path.join(chunk_output_dir, 'final_file.zstd')
        num = 1
        attempt = 3
        with open(final_file_path, 'wb') as final_file:
            while(os.path.exists(os.path.join(output_dir, f"chunk_{num}.pchunk"))):
                chunk_path = os.path.join(output_dir, f"chunk_{num}.pchunk")
                if not os.path.exists(chunk_path):
                    #log for missing chunk
                    log(f"Stopping finding further chunks", log_type=LogType.ERROR, status="Failure", general_logfile_path=general_logfile_path)
                    break
                with open(chunk_path, 'rb') as chunk_file:
                    final_file.write(chunk_file.read())
                os.remove(chunk_path)
                #log for successfully added chunk
                log(f"Chunk chunk_{num} added to final file {final_file_path}", log_type=LogType.INFO, status="Success", general_logfile_path=general_logfile_path)
                num += 1
            # for chunk_name, info in chunks:
            #     chunk_path = info.get('path')
            #     if not chunk_path or not os.path.exists(chunk_path):
            #         #log for missing chunk
            #         log(f"Chunk file {chunk_path} not found for chunk {chunk_name}", log_type=LogType.ERROR, status="Failure", general_logfile_path=general_logfile_path)
            #         continue
            #     with open(chunk_path, 'rb') as chunk_file:
            #         final_file.write(chunk_file.read())
            #     os.remove(chunk_path)
            #     #log for successfully added chunk
            #     log(f"Chunk {chunk_name} added to final file {final_file_path}", log_type=LogType.INFO, status="Success", general_logfile_path=general_logfile_path)


        #log for successfully joined chunks
        log(f"All chunks successfully joined into {final_file_path}", log_type=LogType.INFO, status="Success", general_logfile_path=general_logfile_path)


        #log for successfully joined chunks
        return final_file_path

    except Exception as e:
        #log for error in join_chunks
        log(f"Error joining chunks: {e}", log_type=LogType.ERROR, status="Failure", general_logfile_path=general_logfile_path)
        raise
