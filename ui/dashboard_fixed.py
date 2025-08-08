# dashboard.py

import dash
from dash import dcc, html, Input, Output, State, dash_table, callback_context
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sqlite3
import json
import os
import subprocess
import threading
import time
import signal
import sys
from datetime import datetime
import base64
import io
import PyPDF2
from pdf2image import convert_from_bytes
from PIL import Image
import tempfile

class ModernInsuranceAIDashboard:
    def __init__(self):
        # Use modern Bootstrap theme
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP])
        self.running_processes = {}
        
        # Initialize state variables
        self.email_listener_process = None
        self.processing_logs = []
        self.processed_emails = []
        self.log_file_path = None
        self.last_log_position = 0
        self.current_progress = 0
        self.current_status = "Ready"
        self.processing_step = ""
        
        # Check for existing log files on startup
        self._load_existing_logs()
        
        self.setup_layout()
        self.setup_callbacks()
    
    def _load_existing_logs(self):
        """Load and process existing log files on startup"""
        try:
            if os.path.exists("logs"):
                log_files = [f for f in os.listdir("logs") if f.startswith("email_listener_") and f.endswith(".log")]
                if log_files:
                    # Use the most recent log file
                    log_files.sort(reverse=True)
                    recent_log = os.path.join("logs", log_files[0])
                    
                    # Check if file has content and is recent (less than 24 hours old)
                    if os.path.getsize(recent_log) > 0 and os.path.getmtime(recent_log) > (time.time() - 86400):
                        self.log_file_path = recent_log
                        self.processing_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Loading existing log: {self.log_file_path}")
                        
                        # Process existing log content
                        with open(self.log_file_path, 'r', encoding='utf-8') as log_file:
                            lines = log_file.readlines()
                            for line in lines:
                                line = line.strip()
                                if line:
                                    # Add original timestamp or current time
                                    if line.startswith('['):
                                        self.processing_logs.append(line)
                                    else:
                                        self.processing_logs.append(f"[LOG] {line}")
                                    
                                    # Process for progress tracking
                                    self._process_log_line(line)
                        
                        # Set initial progress based on log content
                        if self.current_progress == 0 and self.processing_logs:
                            self.current_progress = min(len(self.processing_logs) * 3, 70)
                            if not self.current_status or self.current_status == "Ready":
                                self.current_status = "Log file loaded - monitoring for new activity"
                                self.processing_step = "Log Loaded"
        except Exception as e:
            self.processing_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Error loading existing logs: {str(e)}")
    
    def _process_log_line(self, line):
        """Process a single log line for progress tracking"""
        # Calculate progress based on key milestones and line count
        total_lines = len(self.processing_logs)
        base_progress = min(total_lines * 3, 70)  # Each line adds 3%, max 70% from line count
        
        # Milestone-based progress boosts
        milestone_progress = 0
        
        # Step 1: Email Detection (+10%)
        if "[EMAIL] Insurance Email received:" in line:
            if not any(email.get("status") == "Email Detected" for email in self.processed_emails):
                email_id = f"Email_{datetime.now().strftime('%H%M%S')}"
                self.processed_emails.append({
                    "id": email_id,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "drive_link": None,
                    "folder_name": "Processing...",
                    "progress": 0,
                    "status": "Email Detected",
                    "uploaded_files": []
                })
            milestone_progress += 10
            self.current_status = "Insurance email detected with PDF attachment!"
            self.processing_step = "Email Processing"
        
        # Step 2: PDF Processing (+10%)
        elif "[ATTACH] Saved attachment:" in line:
            if self.processed_emails:
                # Extract attachment name
                attachment_name = line.split("[ATTACH] Saved attachment:")[1].strip()
                self.processed_emails[-1]["attachment_name"] = attachment_name
            milestone_progress += 10
            self.current_status = "PDF attachment downloaded and processed"
            self.processing_step = "PDF Processing"
        
        # Step 3: Folder Creation (+10%)
        elif "[FOLDER] Created folder:" in line and "(ID:" in line:
            parts = line.split("[FOLDER] Created folder:")[1].strip()
            if "(ID:" in parts:
                folder_name = parts.split("(ID:")[0].strip()
                folder_id = parts.split("(ID:")[1].strip().rstrip(")")
                if self.processed_emails:
                    self.processed_emails[-1]["folder_name"] = folder_name
                    self.processed_emails[-1]["folder_id"] = folder_id
            milestone_progress += 10
            self.current_status = f"Google Drive folder '{folder_name}' created"
            self.processing_step = "Folder Created"
        
        # Step 4: Drive Link Available (reach 100%)
        elif "[DRIVE_LINK]" in line:
            drive_url = line.split("[DRIVE_LINK]")[1].strip()
            if self.processed_emails:
                self.processed_emails[-1]["drive_link"] = drive_url
                self.processed_emails[-1]["progress"] = 100
                self.processed_emails[-1]["status"] = "Drive Link Generated"
            self.current_progress = 100
            self.current_status = "Google Drive link generated - Process Complete!"
            self.processing_step = "Complete - Link Available"
        
        # Step 5: File Uploads (maintain 100%)
        elif "[UPLOAD] Uploaded:" in line and "(ID:" in line:
            if self.processed_emails:
                # Extract uploaded file info
                upload_info = line.split("[UPLOAD] Uploaded:")[1].strip()
                file_name = upload_info.split("(ID:")[0].strip()
                file_id = upload_info.split("(ID:")[1].strip().rstrip(")")
                
                # Add to uploaded files list
                if "uploaded_files" not in self.processed_emails[-1]:
                    self.processed_emails[-1]["uploaded_files"] = []
                self.processed_emails[-1]["uploaded_files"].append({
                    "name": file_name,
                    "id": file_id
                })
                
                uploaded_count = len(self.processed_emails[-1]["uploaded_files"])
                self.processed_emails[-1]["status"] = f"Complete - {uploaded_count} files uploaded"
            
            # Keep at 100% once drive link is available
            if self.current_progress < 100:
                self.current_progress = 100
            self.current_status = f"File uploaded: {file_name}"
            self.processing_step = "Complete - Files Uploaded"
        
        # Update overall progress (don't exceed 100% or go backwards)
        if self.current_progress < 100:
            new_progress = min(base_progress + milestone_progress, 99)  # Leave 1% for drive link
            self.current_progress = max(self.current_progress, new_progress)
        
        # Update individual email progress
        if self.processed_emails:
            self.processed_emails[-1]["progress"] = self.current_progress
    
    def setup_layout(self):
        """Setup the streamlined email-based document processing interface"""
        self.app.layout = dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H1([
                            html.I(className="bi bi-envelope-check me-3", style={"color": "#0d6efd"}),
                            "Insurance Document Processor"
                        ], className="text-center mb-0", style={"color": "#2c3e50", "font-weight": "600"}),
                        html.P("Automated Email-Based Document Processing & Google Drive Storage", 
                               className="text-center text-muted mb-4", style={"font-size": "1.1rem"})
                    ])
                ])
            ], className="mb-4"),
            
            # Auto-refresh interval for real-time updates
            dcc.Interval(
                id='interval-component',
                interval=2*1000,  # Update every 2 seconds
                n_intervals=0
            ),
            
            # Main Email Processing Card
            dbc.Card([
                dbc.CardHeader([
                    html.H4([
                        html.I(className="bi bi-gear-fill me-2"),
                        "Email Document Processor"
                    ], className="mb-0", style={"color": "#2c3e50"})
                ]),
                dbc.CardBody([
                    # Step 1: Credentials Input
                    dbc.Row([
                        dbc.Col([
                            html.H5([
                                html.I(className="bi bi-1-circle-fill me-2", style={"color": "#0d6efd"}),
                                "Enter Email Credentials"
                            ], className="mb-3"),
                            dbc.InputGroup([
                                dbc.InputGroupText(html.I(className="bi bi-envelope")),
                                dbc.Input(
                                    id="email-input",
                                    placeholder="your-email@gmail.com",
                                    type="email",
                                    value="canspirittest@gmail.com"
                                )
                            ], className="mb-3"),
                            dbc.InputGroup([
                                dbc.InputGroupText(html.I(className="bi bi-key")),
                                dbc.Input(
                                    id="password-input",
                                    placeholder="App Password (16 characters)",
                                    type="password",
                                    value="ylyh hkml dgxn vdpi"
                                )
                            ], className="mb-3"),
                            dbc.Alert([
                                html.I(className="bi bi-info-circle me-2"),
                                "Use Gmail App Password, not regular password. ",
                                html.A("Generate here", href="https://myaccount.google.com/apppasswords", target="_blank")
                            ], color="info", className="mb-3"),
                            
                            # Control Buttons
                            dbc.ButtonGroup([
                                dbc.Button([
                                    html.I(className="bi bi-play-fill me-2"),
                                    "Start Processing"
                                ], id="start-processing-btn", color="success", size="lg", disabled=False),
                                dbc.Button([
                                    html.I(className="bi bi-stop-fill me-2"),
                                    "Stop Processing"
                                ], id="stop-processing-btn", color="danger", size="lg", disabled=True),
                            ], className="w-100 mb-3"),
                            
                            # Status Badge
                            html.Div([
                                dbc.Badge("Ready to Start", id="status-badge", color="secondary", className="fs-6 p-2")
                            ], className="text-center")
                        ], md=6),
                        
                        # Step 2: Process Status
                        dbc.Col([
                            html.H5([
                                html.I(className="bi bi-2-circle-fill me-2", style={"color": "#198754"}),
                                "Processing Status"
                            ], className="mb-3"),
                            html.Div(id="process-status-content")
                        ], md=6)
                    ]),
                    
                    html.Hr(),
                    
                    # Step 3: Results Display
                    html.H5([
                        html.I(className="bi bi-3-circle-fill me-2", style={"color": "#fd7e14"}),
                        "Processing Results"
                    ], className="mb-3"),
                    html.Div(id="results-content")
                ])
            ], className="mb-4", style={"border": "none", "box-shadow": "0 8px 16px rgba(0, 0, 0, 0.1)", "borderRadius": "15px"}),
            
            # Footer
            dbc.Row([
                dbc.Col([
                    html.P([
                        "Insurance Document Processor v2.0 | ",
                        html.A("Documentation", href="#", className="text-decoration-none"),
                        " | ",
                        html.A("Support", href="#", className="text-decoration-none")
                    ], className="text-center text-muted small")
                ])
            ])
        ], fluid=True, style={"background": "linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)", "minHeight": "100vh", "padding": "20px"})
    
    def setup_callbacks(self):
        """Setup callbacks for the streamlined email processing interface"""
        
        @self.app.callback(
            [Output('start-processing-btn', 'disabled'),
             Output('stop-processing-btn', 'disabled'),
             Output('status-badge', 'children'),
             Output('status-badge', 'color'),
             Output('process-status-content', 'children'),
             Output('results-content', 'children')],
            [Input('start-processing-btn', 'n_clicks'),
             Input('stop-processing-btn', 'n_clicks'),
             Input('interval-component', 'n_intervals')],
            [State('email-input', 'value'),
             State('password-input', 'value')]
        )
        def manage_processing(start_clicks, stop_clicks, n_intervals, email, password):
            ctx = callback_context
            
            # Default values
            start_disabled = False
            stop_disabled = True
            status_text = "Ready to Start"
            status_color = "secondary"
            
            # Determine what triggered the callback
            if ctx.triggered:
                trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
                
                # Start processing button clicked
                if trigger_id == 'start-processing-btn' and start_clicks and start_clicks > 0:
                    # Start the log file reading simulation
                    self._start_log_simulation()
                    start_disabled = True
                    stop_disabled = False
                    status_text = "Processing Active"
                    status_color = "success"
                
                # Stop processing button clicked
                elif trigger_id == 'stop-processing-btn' and stop_clicks and stop_clicks > 0:
                    self._stop_simulation()
                    start_disabled = False
                    stop_disabled = True
                    status_text = "Stopped"
                    status_color = "danger"
            
            # Update display based on simulation state
            if hasattr(self, 'simulation_active') and self.simulation_active:
                start_disabled = True
                stop_disabled = False
                status_text = "Processing Active"
                status_color = "success"
                self._update_simulation()
            elif hasattr(self, 'simulation_complete') and self.simulation_complete:
                start_disabled = False
                stop_disabled = True
                status_text = "Complete"
                status_color = "success"
            
            # Build status and results content
            status_content = self._build_status_content()
            results_content = self._build_results_content()
            
            return start_disabled, stop_disabled, status_text, status_color, status_content, results_content
        
    def _start_log_simulation(self):
        """Start the email listener in background - simple approach"""
        # Reset state
        self.processing_logs.clear()
        self.processed_emails.clear()
        self.current_progress = 0
        self.current_status = "Starting email listener..."
        self.processing_step = "Launching Email Listener"
        
        # Initialize simulation state
        self.simulation_active = True
        self.simulation_complete = False
        self.simulation_lines = []
        self.simulation_index = 0
        self.drive_link_found = None
        
        # Record start time to identify new log files
        self.start_time = datetime.now()
        
        try:
            # Start email listener - let it output to CLI as normal
            self.email_process = subprocess.Popen([
                sys.executable, "engines/run_email_listener.py"
            ], shell=True, cwd=os.path.dirname(os.path.dirname(__file__)))
            
            self.current_status = "Email listener started! Check terminal for output..."
            self.processing_step = "Email Listener Active"
            
        except Exception as e:
            self.current_status = f"Error starting email listener: {str(e)}"
            self.processing_step = "Error"
            self.simulation_active = False
    
    def _update_simulation(self):
        """Update the simulation - monitor for new log files and display them step by step"""
        if not hasattr(self, 'simulation_active') or not self.simulation_active:
            return
        
        # Look for log files created after we started
        if os.path.exists("logs"):
            log_files = []
            for f in os.listdir("logs"):
                if f.startswith("email_listener_") and f.endswith(".log"):
                    file_path = os.path.join("logs", f)
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    # Only consider log files created after we started
                    if file_time > self.start_time:
                        log_files.append((file_time, file_path))
            
            # If we found a new log file, start displaying it
            if log_files and not hasattr(self, 'current_log_file'):
                # Get the most recent log file
                log_files.sort(key=lambda x: x[0], reverse=True)
                self.current_log_file = log_files[0][1]
                self.current_status = "New log file detected! Reading content..."
                
                # Read all lines from the log file
                try:
                    with open(self.current_log_file, 'r', encoding='utf-8') as f:
                        self.simulation_lines = [line.strip() for line in f.readlines() if line.strip()]
                    
                    self.simulation_index = 0
                    self.current_status = "Displaying log content step by step..."
                    
                except Exception as e:
                    self.current_status = f"Error reading log file: {str(e)}"
                    return
            
            # If we have a log file and lines to show, display them step by step
            elif hasattr(self, 'current_log_file') and hasattr(self, 'simulation_lines'):
                # Show one more line every update
                if self.simulation_index < len(self.simulation_lines):
                    self.simulation_index += 1
                    
                    # Calculate progress
                    if len(self.simulation_lines) > 0:
                        self.current_progress = int((self.simulation_index / len(self.simulation_lines)) * 100)
                    
                    # Update status based on current line
                    if self.simulation_index > 0:
                        current_line = self.simulation_lines[self.simulation_index - 1]
                        
                        if "[CONNECT]" in current_line:
                            self.current_status = "Connecting to Gmail..."
                        elif "[SUCCESS]" in current_line and "Connected" in current_line:
                            self.current_status = "Successfully connected to Gmail"
                        elif "[EMAIL]" in current_line:
                            self.current_status = "Insurance email received! Processing..."
                        elif "[ATTACH]" in current_line:
                            self.current_status = "Saving PDF attachment..."
                        elif "[FOLDER]" in current_line:
                            self.current_status = "Creating Google Drive folder..."
                        elif "[DRIVE_LINK]" in current_line:
                            # Extract drive link
                            if "https://" in current_line:
                                link_part = current_line.split("https://", 1)[1].strip()
                                self.drive_link_found = "https://" + link_part
                            self.current_status = "Google Drive folder created!"
                        elif "[UPLOAD]" in current_line:
                            self.current_status = "Uploading files to Google Drive..."
                
                # Check if we're done displaying all lines
                if self.simulation_index >= len(self.simulation_lines):
                    self.simulation_complete = True
                    self.current_progress = 100
                    if self.drive_link_found:
                        self.current_status = "Processing complete! Google Drive link available."
                    else:
                        self.current_status = "Processing complete!"
        
        else:
            # Logs directory doesn't exist yet
            self.current_status = "Email listener starting... waiting for logs directory..."
    
    def _stop_simulation(self):
        """Stop the simulation"""
        self.simulation_active = False
        self.current_status = "Processing stopped by user"
        self.processing_step = "Stopped"
    
    def _build_status_content(self):
        """Build the process status display with progress tracking"""
        status_content = []
        
        # Show current status and progress
        if hasattr(self, 'current_status') and self.current_status:
            if hasattr(self, 'current_progress') and self.current_progress > 0:
                progress_color = "success" if self.current_progress == 100 else "info"
                status_content.append(
                    html.Div([
                        html.H6(f"Current Step: {getattr(self, 'processing_step', 'Processing')}", className="mb-2"),
                        dbc.Progress(
                            value=self.current_progress,
                            color=progress_color,
                            striped=self.current_progress < 100,
                            animated=self.current_progress < 100,
                            className="mb-3",
                            style={"height": "25px"}
                        ),
                        html.P(self.current_status, className="text-muted mb-3")
                    ])
                )
            else:
                status_content.append(
                    html.Div([
                        html.H6("Status:", className="mb-2"),
                        html.P(self.current_status, className="text-muted mb-3")
                    ])
                )
        
        # Display log file content step by step
        if hasattr(self, 'simulation_lines') and self.simulation_lines:
            log_items = []
            # Show lines progressively based on simulation_index
            lines_to_show = getattr(self, 'simulation_index', 0)
            
            for i, line in enumerate(self.simulation_lines[:lines_to_show]):
                # Color coding for different log types
                if "ERROR" in line.upper():
                    color = "danger"
                elif any(tag in line.upper() for tag in ["[EMAIL]", "[ATTACH]", "[FOLDER]", "[DRIVE_LINK]", "[UPLOAD]"]):
                    color = "success"
                elif any(tag in line.upper() for tag in ["[INFO]", "[CONNECT]", "[SUCCESS]"]):
                    color = "info"
                elif "WARNING" in line.upper():
                    color = "warning"
                else:
                    color = "light"
                
                log_items.append(
                    dbc.Alert(
                        line, 
                        color=color, 
                        className="p-2 mb-1 small",
                        style={"fontSize": "12px", "lineHeight": "1.2"}
                    )
                )
            
            status_content.append(
                html.Div([
                    html.H6(f"Email Listener Output ({lines_to_show}/{len(self.simulation_lines)} lines):", className="mb-2"),
                    html.Div(
                        log_items, 
                        style={
                            "maxHeight": "400px", 
                            "overflowY": "auto", 
                            "overflowX": "hidden",
                            "border": "2px solid #dee2e6", 
                            "borderRadius": "8px", 
                            "padding": "10px",
                            "backgroundColor": "#f8f9fa",
                            "scrollBehavior": "smooth"
                        },
                        id="log-container"
                    )
                ])
            )
        
        # Display traditional processing logs if available
        elif self.processing_logs:
            log_items = []
            for i, log in enumerate(self.processing_logs):
                # Color coding for different log types
                if "ERROR" in log.upper():
                    color = "danger"
                elif any(tag in log.upper() for tag in ["[EMAIL]", "[ATTACH]", "[FOLDER]", "[DRIVE_LINK]", "[UPLOAD]"]):
                    color = "success"
                elif any(tag in log.upper() for tag in ["[INFO]", "[CONNECT]", "[SUCCESS]"]):
                    color = "info"
                elif "WARNING" in log.upper():
                    color = "warning"
                else:
                    color = "light"
                
                log_items.append(
                    dbc.Alert(
                        log, 
                        color=color, 
                        className="p-2 mb-1 small",
                        style={"fontSize": "12px", "lineHeight": "1.2"}
                    )
                )
            
            status_content.append(
                html.Div([
                    html.H6("Processing Log:", className="mb-2"),
                    html.Div(
                        log_items, 
                        style={
                            "maxHeight": "300px", 
                            "overflowY": "auto", 
                            "overflowX": "hidden",
                            "border": "2px solid #dee2e6", 
                            "borderRadius": "8px", 
                            "padding": "10px",
                            "backgroundColor": "#f8f9fa",
                            "scrollBehavior": "smooth"
                        },
                        id="log-container"
                    )
                ])
            )
        else:
            status_content.append(
                dbc.Alert([
                    html.I(className="bi bi-info-circle me-2"),
                    "No activity yet. Click 'Start Processing' to begin monitoring for insurance emails."
                ], color="info")
            )
        
        return html.Div(status_content)
    
    def _build_results_content(self):
        """Build the results display with progress tracking for each email"""
        results = []
        
        # Show drive link prominently if found
        if hasattr(self, 'drive_link_found') and self.drive_link_found:
            results.append(
                dbc.Alert([
                    html.H4([
                        html.I(className="bi bi-google me-2"),
                        "Google Drive Link Found!"
                    ], className="mb-3"),
                    html.P("The email processing is complete. Click the link below to access the Google Drive folder:", className="mb-3"),
                    html.A([
                        html.I(className="bi bi-box-arrow-up-right me-2"),
                        "Open Google Drive Folder"
                    ], href=self.drive_link_found, target="_blank", className="btn btn-success btn-lg")
                ], color="success", className="mb-4")
            )
        
        # Show processing status
        if self.processed_emails:
            for email in self.processed_emails:
                drive_link = email.get("drive_link")
                folder_name = email.get("folder_name", "Processing...")
                progress = email.get("progress", 0)
                status = email.get("status", "Processing")
                
                # Progress bar for this email
                progress_color = "success" if progress == 100 else "info"
                progress_bar = dbc.Progress(
                    value=progress,
                    color=progress_color,
                    striped=progress < 100,
                    animated=progress < 100,
                    className="mb-2",
                    style={"height": "20px"}
                )
                
                # Get uploaded files info
                uploaded_files = email.get("uploaded_files", [])
                attachment_name = email.get("attachment_name", "Unknown attachment")
                
                # Create uploaded files display
                uploaded_files_display = []
                if uploaded_files:
                    for file_info in uploaded_files:
                        file_badge = dbc.Badge([
                            html.I(className="bi bi-file-earmark me-1"),
                            file_info["name"]
                        ], color="light", className="me-1 mb-1")
                        uploaded_files_display.append(file_badge)
                
                # Email processing card
                results.append(
                    dbc.Card([
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    html.H6(f"📧 {folder_name}", className="mb-1"),
                                    html.Small(f"Started: {email['timestamp']}", className="text-muted"),
                                    html.Br(),
                                    html.Small(f"Status: {status}", className=f"text-{'success' if progress == 100 else 'info'}"),
                                    progress_bar,
                                    html.Div(f"{progress}% Complete", className="small text-muted mb-2"),
                                    # Show uploaded files if available
                                    html.Div([
                                        html.Small("Files uploaded:", className="text-muted") if uploaded_files else "",
                                        html.Div(uploaded_files_display) if uploaded_files else ""
                                    ]) if uploaded_files else html.Div([
                                        html.Small(f"Attachment: {attachment_name}", className="text-muted") if attachment_name != "Unknown attachment" else ""
                                    ])
                                ], md=12)
                            ])
                        ])
                    ], className="mb-3", style={"border": f"2px solid {'#28a745' if progress == 100 else '#17a2b8'}"})
                )
        elif not hasattr(self, 'simulation_active') or not self.simulation_active:
            results.append(
                dbc.Alert([
                    html.I(className="bi bi-inbox me-2"),
                    "Click 'Start Processing' to read and display the log file step by step."
                ], color="info")
            )
        
        return html.Div(results)
    
    def run(self, debug=True, host='0.0.0.0', port=8050):
        """Run the dashboard"""
        def signal_handler(sig, frame):
            print("\nStopping email listener...")
            if hasattr(self, 'email_listener_process') and self.email_listener_process:
                self.email_listener_process.terminate()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        print(f"🚀 Starting Insurance Document Processor at http://{host}:{port}")
        print("✨ Features: Email Processing, Google Drive Integration, Real-time Status")
        print("🛑 Use Ctrl+C to stop")
        
        self.app.run(debug=debug, host=host, port=port)

if __name__ == "__main__":
    dashboard = ModernInsuranceAIDashboard()
    dashboard.run()
