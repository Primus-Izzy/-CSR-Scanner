#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Website Rendering Analysis Tool
---------------------------------------
Processes a list of websites to detect their rendering type (Client-Side, Server-Side, or Not Accessible).

This enhanced version includes:
- Comprehensive configuration management
- Environment variable support
- Advanced retry mechanisms
- Performance optimizations
- Detailed logging and debugging
- Resume functionality
- Enhanced error handling

Usage:
    python run_analysis.py [input_file] [options]

Examples:
    # Basic usage
    python run_analysis.py input.csv --output results.csv --workers 10
    
    # Performance tuning
    python run_analysis.py input.csv --workers 15 --timeout 30 --browser-timeout 25
    
    # Debugging
    python run_analysis.py input.csv --verbose --debug --log-file debug.log
    
    # Configuration file
    python run_analysis.py input.csv --config-file config.json
"""

import os
import sys

# Set UTF-8 encoding for Windows compatibility
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
import time
import logging
import traceback
import concurrent.futures
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any

import pandas as pd
from tqdm import tqdm

# Add the current directory to the path to ensure local imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import ConfigLoader, ConfigurationError
from website_renderer import WebsiteRendererDetector
from progress_manager import ProgressManager
from output_manager import OutputManager
from models import ProcessingResult, ProcessingStats, RenderingType, ProcessingStatus, DetectorConfig


def load_websites(input_file: str) -> List[Dict]:
    """Load websites from input file (CSV or Excel) with enhanced error handling."""
    input_file = os.path.abspath(input_file)
    
    if not os.path.exists(input_file):
        logging.error(f"Input file not found: {input_file}")
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    try:
        logging.info(f"Loading websites from: {input_file}")
        
        if input_file.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(input_file, engine='openpyxl')
            logging.debug(f"Loaded Excel file with {len(df)} rows")
        else:
            df = pd.read_csv(input_file)
            logging.debug(f"Loaded CSV file with {len(df)} rows")
        
        # Ensure there's at least a 'url' column
        if 'url' not in df.columns:
            if len(df.columns) > 0:
                df = df.rename(columns={df.columns[0]: 'url'})
                logging.info(f"Renamed column '{df.columns[0]}' to 'url'")
            else:
                raise ValueError("Input file has no columns")
        
        # Clean URLs and remove duplicates
        original_count = len(df)
        df['url'] = df['url'].astype(str).str.strip()
        df = df.drop_duplicates(subset=['url']).reset_index(drop=True)
        
        if len(df) < original_count:
            logging.info(f"Removed {original_count - len(df)} duplicate URLs")
        
        # Keep empty URLs for data integrity but log them
        empty_urls = df[df['url'].isin(['', 'nan', 'None'])].shape[0]
        if empty_urls > 0:
            logging.warning(f"Found {empty_urls} empty/invalid URLs in input file")
        
        logging.info(f"Successfully loaded {len(df)} unique URLs")
        return df.to_dict('records')
    
    except Exception as e:
        logging.error(f"Error loading input file {input_file}: {e}")
        raise


# save_results function removed - now using ProgressManager.save_progress()


def process_websites(websites: List[Dict], output_file: str, config: DetectorConfig) -> ProcessingStats:
    """Process websites and save results incrementally with enhanced configuration."""
    logging.info(f"Starting website processing with configuration:")
    logging.info(f"  Workers: {config.max_workers}")
    logging.info(f"  Chunk size: {config.chunk_size}")
    logging.info(f"  Save interval: {config.save_progress_interval}")
    logging.info(f"  HTTP timeout: {config.timeouts.http_request}s")
    logging.info(f"  Browser timeout: {config.timeouts.browser_load}s")
    logging.info(f"  Max retries: {config.retry.max_attempts}")
    
    # Additional verbose logging
    logging.debug(f"Browser configuration:")
    logging.debug(f"  Headless: {config.browser.headless}")
    logging.debug(f"  Disable images: {config.browser.disable_images}")
    logging.debug(f"  Disable CSS: {config.browser.disable_css}")
    logging.debug(f"  User agent rotation: {config.browser.user_agent_rotation}")
    logging.debug(f"  Window size: {config.browser.window_width}x{config.browser.window_height}")
    
    logging.debug(f"Retry configuration:")
    logging.debug(f"  Backoff base: {config.retry.backoff_base}s")
    logging.debug(f"  Backoff multiplier: {config.retry.backoff_multiplier}")
    logging.debug(f"  Non-retryable errors: {[e.value for e in config.retry.non_retryable_errors]}")
    
    # Initialize the detector with full configuration
    detector = WebsiteRendererDetector(config=config)
    
    # Initialize ProgressManager for resume functionality
    progress_manager = ProgressManager(save_interval=config.save_progress_interval)
    
    # Initialize OutputManager for enhanced output handling
    output_manager = OutputManager()
    
    # Initialize processing statistics
    stats = ProcessingStats(
        total_urls=len(websites),
        start_time=datetime.now()
    )
    
    # Track results and processed count
    processed_count = 0
    start_time = time.time()
    
    # Load existing progress and filter processed URLs
    processed_urls = progress_manager.load_existing_progress(output_file)
    original_count = len(websites)
    
    # Extract URLs from website dictionaries for filtering
    website_urls = [site['url'] for site in websites if site.get('url')]
    remaining_urls = progress_manager.filter_processed_urls(website_urls, processed_urls)
    
    # Filter websites to only include unprocessed ones
    websites = [site for site in websites if site.get('url') in remaining_urls]
    
    # Get and display resume statistics
    resume_stats = progress_manager.get_resume_stats(original_count, processed_urls)
    if resume_stats['is_resume']:
        logging.info(f"Resuming processing: {resume_stats['processed_count']} URLs already processed "
                    f"({resume_stats['completion_percentage']:.1f}% complete)")
        logging.info(f"Remaining URLs to process: {resume_stats['remaining_count']}")
        
        # Create backup of existing file
        backup_path = progress_manager.create_backup(output_file)
        if backup_path:
            logging.info(f"Created backup: {backup_path}")
    else:
        logging.info(f"Starting fresh processing of {original_count} URLs")
    
    if not websites:
        logging.info("No new URLs to process.")
        return stats
    
    logging.info(f"Processing {len(websites)} URLs with {config.max_workers} workers...")
    
    # Track results for incremental saving
    results_buffer = []
    total_processed = resume_stats['processed_count']
    
    try:
        # Process in chunks to save progress
        with tqdm(total=len(websites), desc="Processing", unit="URL", 
                 disable=logging.getLogger().level > logging.INFO) as pbar:
            for i in range(0, len(websites), config.chunk_size):
                chunk = websites[i:i + config.chunk_size]
                chunk_results = []
                
                def process_site(site):
                    if not site['url'] or not site['url'].strip():
                        # Handle empty URL rows while maintaining data integrity
                        return ProcessingResult(
                            url=site['url'],
                            final_url='',
                            rendering_type='',
                            status='',
                            processing_time_sec=0.0,
                            timestamp=datetime.now().isoformat(),
                            frameworks=[],
                            error_category=None,
                            error_message=None,
                            retry_count=0,
                            http_status_code=None
                        )
                    
                    try:
                        # The detect_rendering_type method now returns a ProcessingResult object directly
                        result = detector.detect_rendering_type(site['url'])
                        return result
                    except Exception as e:
                        return ProcessingResult(
                            url=site['url'],
                            final_url=site['url'],
                            rendering_type=RenderingType.NOT_ACCESSIBLE.value,
                            status=ProcessingStatus.FAILED.value,
                            processing_time_sec=0.0,
                            timestamp=datetime.now().isoformat(),
                            frameworks=[],
                            error_category="ProcessingError",
                            error_message=str(e),
                            retry_count=0,
                            http_status_code=None
                        )
                
                # Process sites in parallel
                with concurrent.futures.ThreadPoolExecutor(max_workers=config.max_workers) as executor:
                    futures = [executor.submit(process_site, site) for site in chunk]
                    for future in concurrent.futures.as_completed(futures):
                        try:
                            result = future.result()
                            chunk_results.append(result)
                            results_buffer.append(result)
                            total_processed += 1
                            
                            pbar.update(1)
                            pbar.set_postfix({
                                'Status': result.status,
                                'Type': result.rendering_type[:20] + '...' if len(result.rendering_type) > 20 else result.rendering_type,
                                'Time': f"{result.processing_time_sec:.1f}s"
                            })
                        except Exception as e:
                            logging.error(f"Error processing result: {e}")
                            if logging.getLogger().level <= logging.DEBUG:
                                logging.debug(traceback.format_exc())
                
                # Update statistics for each result
                for result in chunk_results:
                    stats.add_result(result)
                
                # Save progress incrementally using OutputManager
                if progress_manager.should_save_progress(len(results_buffer)):
                    logging.debug(f"Saving progress: {len(results_buffer)} results to {output_file}")
                    output_manager.write_results(results_buffer, output_file, append=resume_stats['is_resume'])
                    logging.debug(f"Progress saved successfully")
                    results_buffer = []  # Clear buffer after saving
                    resume_stats['is_resume'] = True  # Subsequent saves should append
                # Print stats periodically
                if (i // config.chunk_size) % 10 == 0:  # Every 10 chunks
                    elapsed = time.time() - start_time
                    current_processed = i + len(chunk)
                    urls_per_sec = current_processed / elapsed if elapsed > 0 else 0
                    remaining = len(websites) - current_processed
                    eta = remaining / urls_per_sec if urls_per_sec > 0 else 0
                    logging.info(f"Processed: {current_processed}/{len(websites)} "
                               f"({current_processed/len(websites)*100:.1f}%) | "
                               f"Speed: {urls_per_sec:.2f} URLs/sec | "
                               f"ETA: {datetime.fromtimestamp(eta).strftime('%H:%M:%S') if eta > 0 else '--:--:--'}")
                    
                    # Additional debug information
                    logging.debug(f"Chunk {i // config.chunk_size + 1} completed")
                    logging.debug(f"Current chunk size: {len(chunk)} URLs")
                    logging.debug(f"Results buffer size: {len(results_buffer)}")
                    logging.debug(f"Memory usage: ~{current_processed * 0.1:.1f}MB estimated")
    
    except KeyboardInterrupt:
        logging.warning("Process interrupted by user. Saving current progress...")
    except Exception as e:
        logging.error(f"Error during processing: {e}")
        if logging.getLogger().level <= logging.DEBUG:
            logging.debug(traceback.format_exc())
    finally:
        # Ensure all remaining results are saved
        if results_buffer:
            logging.debug(f"Saving final {len(results_buffer)} results")
            output_manager.write_results(results_buffer, output_file, append=True)
            logging.debug(f"Final results saved successfully")
            # Update stats for remaining results
            for result in results_buffer:
                stats.add_result(result)
        
        # Finalize statistics
        stats.end_time = datetime.now()
        
        logging.info(f"Processing complete! Results saved to: {os.path.abspath(output_file)}")
        
        # Generate and display comprehensive summary report
        try:
            logging.debug("Generating comprehensive summary report")
            summary_report = output_manager.generate_summary_report(stats)
            logging.info("Summary Report:\n" + summary_report)
            
            # Save JSON report for programmatic access
            json_report_file = output_file.replace('.csv', '_report.json')
            logging.debug(f"Saving JSON report to: {json_report_file}")
            output_manager.write_json_report(stats, json_report_file)
            logging.info(f"Detailed JSON report saved to: {os.path.abspath(json_report_file)}")
            
        except Exception as e:
            logging.warning(f"Could not generate comprehensive report: {e}")
            if logging.getLogger().level <= logging.DEBUG:
                logging.debug(traceback.format_exc())
            # Fallback to basic statistics
            elapsed = time.time() - start_time
            if elapsed > 0:
                current_session_processed = len(websites)
                logging.info(f"URLs processed in this session: {current_session_processed}")
                logging.info(f"Total URLs in output file: {total_processed}")
                logging.info(f"Session time: {timedelta(seconds=int(elapsed))}")
                logging.info(f"Session speed: {current_session_processed/elapsed:.2f} URLs/sec")
        
        return stats


def main():
    """Enhanced main function with comprehensive configuration management"""
    try:
        # Parse command line arguments using enhanced parser
        parser = ConfigLoader.create_argument_parser()
        args = parser.parse_args()
        
        # Handle special configuration commands first
        if hasattr(args, 'show_config') and args.show_config:
            logging.debug("Showing configuration")
            config = ConfigLoader.load_from_args(args)
            ConfigLoader.print_config(config)
            return
        
        if hasattr(args, 'validate_config') and args.validate_config:
            logging.debug("Validating configuration")
            config = ConfigLoader.load_from_args(args)
            errors = ConfigLoader.validate_config(config)
            if errors:
                print("ERROR: Configuration validation failed:")
                for field, error in errors.items():
                    print(f"  {field}: {error}")
                    logging.error(f"Validation error - {field}: {error}")
                sys.exit(1)
            else:
                print("SUCCESS: Configuration is valid")
                logging.debug("Configuration validation successful")
                return
        
        # Load configuration from all sources (env, file, args)
        config = ConfigLoader.load_from_args(args)
        
        # Save configuration if requested
        if hasattr(args, 'save_config') and args.save_config:
            logging.debug(f"Saving configuration to: {args.save_config}")
            try:
                ConfigLoader.save_to_file(config, args.save_config)
                print(f"Configuration saved to: {args.save_config}")
                logging.info(f"Configuration successfully saved to: {os.path.abspath(args.save_config)}")
                return
            except Exception as e:
                logging.error(f"Failed to save configuration: {e}")
                print(f"ERROR: Failed to save configuration: {e}")
                sys.exit(1)
        
        # Validate configuration
        logging.debug("Validating configuration...")
        errors = ConfigLoader.validate_config(config)
        if errors:
            logging.error("Configuration validation failed")
            print("ERROR: Configuration validation failed:")
            for field, error in errors.items():
                print(f"  {field}: {error}")
                logging.error(f"Configuration error - {field}: {error}")
            sys.exit(1)
        else:
            logging.debug("Configuration validation passed")
        
        # Setup logging based on configuration
        ConfigLoader.setup_logging(
            verbose=getattr(args, 'verbose', False),
            debug=getattr(args, 'debug', False),
            quiet=getattr(args, 'quiet', False),
            log_file=getattr(args, 'log_file', None)
        )
        
        # Display startup banner and configuration
        print("=" * 80)
        print("ENHANCED WEBSITE RENDERING ANALYSIS TOOL".center(80))
        print("=" * 80)
        print(f"Input file:     {os.path.abspath(args.input_file)}")
        print(f"Output file:    {os.path.abspath(args.output)}")
        print("-" * 80)
        
        # Log configuration details for debugging
        logging.debug(f"Configuration loaded successfully")
        logging.debug(f"Max workers: {config.max_workers}")
        logging.debug(f"Chunk size: {config.chunk_size}")
        logging.debug(f"HTTP timeout: {config.timeouts.http_request}s")
        logging.debug(f"Browser timeout: {config.timeouts.browser_load}s")
        logging.debug(f"Max retries: {config.retry.max_attempts}")
        logging.debug(f"Headless mode: {config.browser.headless}")
        logging.debug(f"Save interval: {config.save_progress_interval}")
        
        # Display configuration if verbose
        if getattr(args, 'verbose', False) or getattr(args, 'debug', False):
            ConfigLoader.print_config(config, show_warnings=True)
        else:
            # Show brief configuration summary
            print(f"Workers: {config.max_workers} | "
                  f"Chunk: {config.chunk_size} | "
                  f"Timeout: {config.timeouts.http_request}s | "
                  f"Retries: {config.retry.max_attempts}")
            print("-" * 80)
        
        # Show configuration warnings if any
        warnings = ConfigLoader.get_validation_warnings(config)
        if warnings and not getattr(args, 'quiet', False):
            print("WARNING: Configuration Warnings:")
            for warning in warnings[:3]:  # Show only first 3 warnings
                print(f"  • {warning}")
            if len(warnings) > 3:
                print(f"  ... and {len(warnings) - 3} more (use --verbose to see all)")
            print("-" * 80)
        
        # Load websites
        logging.info("Loading input file...")
        logging.debug(f"Input file path: {os.path.abspath(args.input_file)}")
        websites = load_websites(args.input_file)
        if not websites:
            logging.error("No valid URLs found in the input file.")
            sys.exit(1)
        
        logging.info(f"Found {len(websites)} unique URLs to process.")
        logging.debug(f"Sample URLs: {[w.get('url', '') for w in websites[:5]]}")
        
        # Start processing
        logging.info("Starting website processing...")
        final_stats = process_websites(
            websites=websites,
            output_file=args.output,
            config=config
        )
        
        # Display final performance metrics
        if final_stats:
            try:
                logging.debug("Generating final performance metrics")
                performance_metrics = OutputManager().create_performance_report(final_stats)
                print(f"\nFINAL PERFORMANCE METRICS")
                print(f"Processing Speed: {performance_metrics['throughput']['urls_per_second']:.2f} URLs/second")
                print(f"Success Rate: {performance_metrics['success_metrics']['success_rate']:.1f}%")
                if performance_metrics['error_analysis']['most_common_error']:
                    print(f"Most Common Error: {performance_metrics['error_analysis']['most_common_error']}")
                
                # Additional debug metrics
                logging.debug(f"Total processing time: {performance_metrics['timing']['total_duration']}")
                logging.debug(f"Average processing time per URL: {performance_metrics['timing']['average_processing_time']:.2f}s")
                logging.debug(f"Error breakdown: {performance_metrics['error_analysis']['error_distribution']}")
                
            except Exception as e:
                logging.warning(f"Could not generate performance metrics: {e}")
                if logging.getLogger().level <= logging.DEBUG:
                    logging.debug(traceback.format_exc())
        
        print("\n" + "=" * 80)
        print("PROCESSING COMPLETED SUCCESSFULLY!".center(80))
        print("=" * 80)
        
    except ConfigurationError as e:
        print(f"ERROR: Configuration Error: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"ERROR: File Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nWARNING: Process interrupted by user")
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        if logging.getLogger().level <= logging.DEBUG:
            logging.debug(traceback.format_exc())
        else:
            print(f"ERROR: An unexpected error occurred: {e}")
            print("Use --debug for detailed error information")
        sys.exit(1)


if __name__ == "__main__":
    main()
