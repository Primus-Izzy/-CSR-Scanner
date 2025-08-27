#!/usr/bin/env python3
"""
Batch Processing Example for CSR Scanner

This script demonstrates how to process large datasets efficiently
by breaking them into smaller batches and processing them sequentially.
"""

import os
import sys
import pandas as pd
import subprocess
from pathlib import Path
from datetime import datetime


def create_batches(input_file: str, batch_size: int = 10000, output_dir: str = "batches"):
    """Split a large CSV file into smaller batches"""
    
    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)
    
    # Read the input file
    print(f"Reading input file: {input_file}")
    df = pd.read_csv(input_file)
    total_urls = len(df)
    
    print(f"Total URLs to process: {total_urls}")
    print(f"Batch size: {batch_size}")
    
    # Calculate number of batches
    num_batches = (total_urls // batch_size) + (1 if total_urls % batch_size > 0 else 0)
    print(f"Creating {num_batches} batches...")
    
    batch_files = []
    
    # Create batch files
    for i in range(num_batches):
        start_idx = i * batch_size
        end_idx = min((i + 1) * batch_size, total_urls)
        
        batch_df = df.iloc[start_idx:end_idx]
        batch_filename = os.path.join(output_dir, f"batch_{i+1:03d}_input.csv")
        batch_df.to_csv(batch_filename, index=False)
        batch_files.append(batch_filename)
        
        print(f"Created {batch_filename}: {len(batch_df)} URLs")
    
    return batch_files


def process_batch(batch_file: str, output_file: str, config: dict = None):
    """Process a single batch with CSR Scanner"""
    
    print(f"\n{'='*50}")
    print(f"Processing batch: {batch_file}")
    print(f"Output file: {output_file}")
    print(f"{'='*50}")
    
    # Build command
    cmd = [
        sys.executable, 
        "src/run_analysis.py", 
        batch_file,
        "--output", output_file
    ]
    
    # Add configuration options
    if config:
        if "workers" in config:
            cmd.extend(["--workers", str(config["workers"])])
        if "timeout" in config:
            cmd.extend(["--timeout", str(config["timeout"])])
        if "chunk_size" in config:
            cmd.extend(["--chunk-size", str(config["chunk_size"])])
        if "save_interval" in config:
            cmd.extend(["--save-interval", str(config["save_interval"])])
        if config.get("verbose"):
            cmd.append("--verbose")
        if config.get("debug"):
            cmd.append("--debug")
    
    # Execute command
    start_time = datetime.now()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)  # 2 hour timeout
        
        if result.returncode == 0:
            end_time = datetime.now()
            duration = end_time - start_time
            print(f"✅ Batch completed successfully in {duration}")
            print(f"Output saved to: {output_file}")
            return True
        else:
            print(f"❌ Batch failed with return code: {result.returncode}")
            print(f"Error output: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Batch timed out after 2 hours")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def combine_results(batch_output_files: list, final_output_file: str):
    """Combine all batch results into a single file"""
    
    print(f"\nCombining results from {len(batch_output_files)} batches...")
    
    all_results = []
    
    for batch_file in batch_output_files:
        if os.path.exists(batch_file):
            try:
                df = pd.read_csv(batch_file)
                all_results.append(df)
                print(f"✅ Added {len(df)} records from {batch_file}")
            except Exception as e:
                print(f"⚠️ Could not read {batch_file}: {e}")
        else:
            print(f"⚠️ Batch output file not found: {batch_file}")
    
    if all_results:
        # Combine all dataframes
        combined_df = pd.concat(all_results, ignore_index=True)
        
        # Remove duplicates based on URL
        combined_df = combined_df.drop_duplicates(subset=['url'], keep='last')
        
        # Save combined results
        combined_df.to_csv(final_output_file, index=False)
        
        print(f"\n✅ Combined results saved to: {final_output_file}")
        print(f"Total unique URLs processed: {len(combined_df)}")
        
        # Print summary statistics
        status_counts = combined_df['status'].value_counts()
        print(f"\nProcessing Summary:")
        for status, count in status_counts.items():
            print(f"  {status}: {count} ({count/len(combined_df)*100:.1f}%)")
            
        return combined_df
    else:
        print("❌ No valid batch results found to combine")
        return None


def main():
    """Main batch processing workflow"""
    
    # Configuration
    config = {
        "workers": 15,
        "timeout": 25,
        "chunk_size": 100,
        "save_interval": 5,
        "verbose": True,
        "debug": False
    }
    
    # File paths
    input_file = "input_websites.csv"  # Update this path
    batch_size = 5000  # URLs per batch
    batch_dir = "batch_processing"
    results_dir = "batch_results"
    final_output = "combined_results.csv"
    
    # Create directories
    Path(results_dir).mkdir(exist_ok=True)
    
    print("🚀 Starting Batch Processing")
    print(f"Input file: {input_file}")
    print(f"Batch size: {batch_size}")
    print(f"Configuration: {config}")
    
    # Step 1: Create batches
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        return
    
    batch_files = create_batches(input_file, batch_size, batch_dir)
    
    # Step 2: Process each batch
    successful_batches = []
    failed_batches = []
    
    for i, batch_file in enumerate(batch_files, 1):
        batch_output = os.path.join(results_dir, f"batch_{i:03d}_results.csv")
        
        print(f"\n📊 Processing batch {i}/{len(batch_files)}")
        
        if process_batch(batch_file, batch_output, config):
            successful_batches.append(batch_output)
        else:
            failed_batches.append(batch_file)
    
    # Step 3: Combine results
    if successful_batches:
        combined_results = combine_results(successful_batches, final_output)
        
        print(f"\n🎉 Batch processing completed!")
        print(f"Successful batches: {len(successful_batches)}/{len(batch_files)}")
        if failed_batches:
            print(f"Failed batches: {len(failed_batches)}")
            print("Failed batch files:", failed_batches)
        
        if combined_results is not None:
            print(f"Final results saved to: {final_output}")
    else:
        print("❌ No batches were processed successfully")


if __name__ == "__main__":
    main()