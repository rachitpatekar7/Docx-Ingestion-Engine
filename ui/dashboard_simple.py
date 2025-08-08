#!/usr/bin/env python3
"""
Simplified Insurance Document Processor Dashboard
Captures real-time output from email listener and displays it step by step on the UI
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import subprocess
import sys
import os
import tempfile
import threading
import time
from datetime import datetime

class EmailProcessorDashboard:
    def __init__(self):
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP])
        self.app.title = "Insurance Document Processor"
        
        # Initialize state
        self.reset_state()
        
        # Setup layout and callbacks
        self.setup_layout()
        self.setup_callbacks()
    
    def reset_state(self):
        """Reset all processing state"""
        self.simulation_active = False
        self.simulation_complete = False
        self.simulation_lines = []
        self.simulation_index = 0
        self.current_progress = 0
        self.current_status = "Ready to start"
        self.processing_step = "Idle"
        self.drive_link_found = None
        self.email_process = None
        self.temp_output_file = None
        self.output_reader_thread = None
    
    def setup_layout(self):
        """Setup the main dashboard layout"""
        self.app.layout = dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H1([
                            html.I(className="bi bi-envelope-check me-3", style={"color": "#0d6efd"}),
                            "Insurance Document Processor"
                        ], className="text-center mb-2", style={"color": "#2c3e50"}),
                        html.P("Automated Email-Based Document Processing & Google Drive Storage", 
                               className="text-center text-muted mb-4")
                    ])
                ])
            ], className="mb-4"),
            
            # Auto-refresh component
            dcc.Interval(
                id='interval-component',
                interval=1000,  # Update every 1 second
                n_intervals=0
            ),
            
            # Main processing card
            dbc.Card([
                dbc.CardHeader([
                    html.H4([
                        html.I(className="bi bi-gear-fill me-2"),
                        "Email Document Processor"
                    ], className="mb-0", style={"color": "#2c3e50"})
                ]),
                dbc.CardBody([
                    # Credentials section
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
                            
                            # Control buttons
                            dbc.ButtonGroup([
                                dbc.Button([
                                    html.I(className="bi bi-play-fill me-2"),
                                    "Start Processing"
                                ], id="start-btn", color="success", size="lg"),
                                dbc.Button([
                                    html.I(className="bi bi-stop-fill me-2"),
                                    "Stop Processing"
                                ], id="stop-btn", color="danger", size="lg", disabled=True)
                            ], className="w-100 mb-3"),
                            
                            # Status badge
                            html.Div([
                                dbc.Badge("Ready", id="status-badge", color="secondary", className="fs-6 px-3 py-2")
                            ], className="text-center")
                        ], md=6),
                        
                        # Processing status section
                        dbc.Col([
                            html.H5([
                                html.I(className="bi bi-2-circle-fill me-2", style={"color": "#198754"}),
                                "Processing Status"
                            ], className="mb-3"),
                            html.Div(id="status-content")
                        ], md=6)
                    ])
                ])
            ], className="mb-4"),
            
            # Results section
            dbc.Card([
                dbc.CardHeader([
                    html.H4([
                        html.I(className="bi bi-3-circle-fill me-2", style={"color": "#fd7e14"}),
                        "Processing Results"
                    ], className="mb-0", style={"color": "#2c3e50"})
                ]),
                dbc.CardBody([
                    html.Div(id="results-content")
                ])
            ]),
            
            # Footer
            html.Hr(className="mt-5"),
            html.P("Insurance Document Processor v2.0 | Documentation | Support", 
                   className="text-center text-muted small")
        ], fluid=True, className="py-4")
    
    def setup_callbacks(self):
        """Setup dashboard callbacks"""
        @self.app.callback(
            [Output('start-btn', 'disabled'),
             Output('stop-btn', 'disabled'),
             Output('status-badge', 'children'),
             Output('status-badge', 'color'),
             Output('status-content', 'children'),
             Output('results-content', 'children')],
            [Input('start-btn', 'n_clicks'),
             Input('stop-btn', 'n_clicks'),
             Input('interval-component', 'n_intervals')],
            [State('email-input', 'value'),
             State('password-input', 'value')]
        )
        def update_dashboard(start_clicks, stop_clicks, n_intervals, email, password):
            ctx = callback_context
            
            # Handle button clicks
            if ctx.triggered:
                trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
                
                if trigger_id == 'start-btn' and start_clicks:
                    self.start_processing()
                elif trigger_id == 'stop-btn' and stop_clicks:
                    self.stop_processing()
            
            # Update display based on current state
            if self.simulation_active:
                self.update_from_output()
                
                start_disabled = True
                stop_disabled = False
                status_text = "Processing Active"
                status_color = "success"
            else:
                start_disabled = False
                stop_disabled = True
                status_text = "Ready" if not self.simulation_complete else "Complete"
                status_color = "secondary" if not self.simulation_complete else "success"
            
            # Build content
            status_content = self.build_status_content()
            results_content = self.build_results_content()
            
            return start_disabled, stop_disabled, status_text, status_color, status_content, results_content
    
    def start_processing(self):
        """Start the email listener process"""
        self.reset_state()
        self.simulation_active = True
        self.current_status = "Starting email listener..."
        
        # Create temporary file for output capture
        self.temp_output_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.log')
        self.temp_output_file.close()
        
        try:
            # Start email listener process with output redirection
            self.email_process = subprocess.Popen([
                sys.executable, "engines/run_email_listener.py"
            ], stdout=open(self.temp_output_file.name, 'w'), 
               stderr=subprocess.STDOUT,
               shell=True, cwd=os.path.dirname(os.path.dirname(__file__)))
            
            self.current_status = "Email listener started! Monitoring for output..."
            
        except Exception as e:
            self.current_status = f"Error starting email listener: {str(e)}"
            self.simulation_active = False
    
    def stop_processing(self):
        """Stop the email listener process"""
        self.simulation_active = False
        self.current_status = "Stopping..."
        
        if self.email_process:
            try:
                self.email_process.terminate()
                self.email_process.wait(timeout=5)
            except:
                try:
                    self.email_process.kill()
                except:
                    pass
            self.email_process = None
        
        self.current_status = "Stopped by user"
    
    def update_from_output(self):
        """Read output from temp file and update display"""
        if not self.temp_output_file:
            return
        
        try:
            # Read current content from temp file
            with open(self.temp_output_file.name, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if content:
                # Split into lines
                all_lines = [line.strip() for line in content.split('\n') if line.strip()]
                
                # Update simulation lines if we have new content
                if len(all_lines) > len(self.simulation_lines):
                    self.simulation_lines = all_lines
                    self.current_status = f"Captured {len(all_lines)} lines of output..."
                
                # Update progress and status based on current line
                if self.simulation_lines and self.simulation_index < len(self.simulation_lines):
                    # Advance one line at a time for step-by-step display
                    self.simulation_index = min(self.simulation_index + 1, len(self.simulation_lines))
                    
                    # Calculate progress
                    self.current_progress = int((self.simulation_index / len(self.simulation_lines)) * 100)
                    
                    # Update status based on latest line
                    if self.simulation_index > 0:
                        current_line = self.simulation_lines[self.simulation_index - 1]
                        self.update_status_from_line(current_line)
        
        except Exception as e:
            self.current_status = f"Error reading output: {str(e)}"
    
    def update_status_from_line(self, line):
        """Update status based on current log line"""
        if "[CONNECT]" in line:
            self.current_status = "Connecting to Gmail..."
        elif "[SUCCESS]" in line and "Connected" in line:
            self.current_status = "Successfully connected to Gmail!"
        elif "[EMAIL]" in line:
            self.current_status = "Insurance email received! Processing..."
        elif "[ATTACH]" in line:
            self.current_status = "Saving PDF attachment..."
        elif "[FOLDER]" in line:
            self.current_status = "Creating Google Drive folder..."
        elif "[DRIVE_LINK]" in line:
            # Extract drive link
            if "https://" in line:
                link_part = line.split("https://", 1)[1].strip()
                self.drive_link_found = "https://" + link_part
            self.current_status = "Google Drive folder created!"
            self.simulation_complete = True
            self.current_progress = 100
        elif "[UPLOAD]" in line:
            self.current_status = "Uploading files to Google Drive..."
    
    def build_status_content(self):
        """Build the status display section"""
        content = []
        
        # Show current status
        content.append(
            html.Div([
                html.H6("Current Status:", className="mb-2"),
                html.P(self.current_status, className="text-muted mb-3")
            ])
        )
        
        # Show progress bar
        if self.current_progress > 0:
            progress_color = "success" if self.current_progress == 100 else "info"
            content.append(
                html.Div([
                    html.H6("Progress:", className="mb-2"),
                    dbc.Progress(
                        value=self.current_progress,
                        color=progress_color,
                        striped=self.current_progress < 100,
                        animated=self.current_progress < 100,
                        className="mb-3",
                        style={"height": "25px"}
                    ),
                    html.P(f"{self.current_progress}% Complete", className="text-center small text-muted")
                ])
            )
        
        # Show log output step by step
        if self.simulation_lines:
            log_items = []
            lines_to_show = self.simulation_index
            
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
            
            content.append(
                html.Div([
                    html.H6(f"Live Output ({lines_to_show}/{len(self.simulation_lines)} lines):", className="mb-2"),
                    html.Div(
                        log_items, 
                        style={
                            "maxHeight": "400px", 
                            "overflowY": "auto", 
                            "border": "2px solid #dee2e6", 
                            "borderRadius": "8px", 
                            "padding": "10px",
                            "backgroundColor": "#f8f9fa"
                        }
                    )
                ])
            )
        
        return content
    
    def build_results_content(self):
        """Build the results display section"""
        if self.drive_link_found:
            return dbc.Alert([
                html.H4([
                    html.I(className="bi bi-google me-2"),
                    "Google Drive Link Ready!"
                ], className="mb-3"),
                html.P("Email processing complete! Access your files:", className="mb-3"),
                html.A([
                    html.I(className="bi bi-box-arrow-up-right me-2"),
                    "Open Google Drive Folder"
                ], href=self.drive_link_found, target="_blank", className="btn btn-success btn-lg")
            ], color="success")
        elif self.simulation_active:
            return dbc.Alert([
                html.I(className="bi bi-hourglass-split me-2"),
                "Processing in progress... Results will appear here when complete."
            ], color="info")
        else:
            return dbc.Alert([
                html.I(className="bi bi-inbox me-2"),
                "Click 'Start Processing' to begin monitoring for insurance emails."
            ], color="light")
    
    def run(self, debug=True, host='0.0.0.0', port=8050):
        """Run the dashboard"""
        print("🚀 Starting Insurance Document Processor at http://{}:{}".format(host, port))
        print("✨ Features: Email Processing, Google Drive Integration, Real-time Status")
        print("🛑 Use Ctrl+C to stop")
        
        self.app.run(debug=debug, host=host, port=port)

if __name__ == '__main__':
    dashboard = EmailProcessorDashboard()
    dashboard.run()
