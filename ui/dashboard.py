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
from datetime import datetime
import signal
import sys
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
        self.setup_layout()
        self.setup_callbacks()
        
    def extract_text_from_pdf(self, contents):
        """Extract text from PDF file"""
        try:
            # Decode base64 content
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            
            # Try PyPDF2 first (faster)
            try:
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(decoded))
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                if text.strip():
                    return text
            except:
                pass
            
            # Fallback to OCR with pdf2image
            try:
                images = convert_from_bytes(decoded)
                text = ""
                for image in images:
                    # Convert PIL image to text using OCR
                    import pytesseract
                    text += pytesseract.image_to_string(image) + "\n"
                return text
            except:
                return "Error: Could not extract text from PDF"
                
        except Exception as e:
            return f"Error processing PDF: {str(e)}"
    
    def get_engine_status(self):
        """Check which engines are currently running"""
        status = {}
        for engine in ['file_listener', 'ocr_engine', 'classifier_engine', 'data_extraction_engine', 'matching_rule_engine']:
            status[engine] = engine in self.running_processes and self.running_processes[engine].poll() is None
        return status
    
    def get_database_stats(self):
        """Get statistics from all databases"""
        stats = {}
        
        # OCR Stats
        try:
            conn = sqlite3.connect('db/ocr_store.db')
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM ocr_results")
            stats['ocr_processed'] = cursor.fetchone()[0]
            conn.close()
        except:
            stats['ocr_processed'] = 0
            
        # Classification Stats
        try:
            conn = sqlite3.connect('db/classifier_store.db')
            cursor = conn.cursor()
            cursor.execute("SELECT document_type, COUNT(*) FROM classification_results GROUP BY document_type")
            results = cursor.fetchall()
            stats['classifications'] = {doc_type: count for doc_type, count in results}
            conn.close()
        except:
            stats['classifications'] = {}
            
        # Submission Stats
        try:
            conn = sqlite3.connect('db/submission_store.db')
            cursor = conn.cursor()
            cursor.execute("SELECT status, COUNT(*) FROM submission_data GROUP BY status")
            results = cursor.fetchall()
            stats['submissions'] = {status: count for status, count in results}
            
            # Risk scores and appetite decisions
            cursor.execute("SELECT risk_score, appetite_data FROM submission_data WHERE risk_score IS NOT NULL")
            risk_data = cursor.fetchall()
            stats['risk_scores'] = [row[0] for row in risk_data if row[0] is not None]
            
            appetite_decisions = []
            for row in risk_data:
                if row[1]:
                    try:
                        appetite = json.loads(row[1])
                        appetite_decisions.append(appetite.get('decision', 'unknown'))
                    except:
                        pass
            stats['appetite_decisions'] = appetite_decisions
            conn.close()
        except:
            stats['submissions'] = {}
            stats['risk_scores'] = []
            stats['appetite_decisions'] = []
            
        return stats
    
    def get_recent_submissions(self):
        """Get recent submission data for the table"""
        try:
            conn = sqlite3.connect('db/submission_store.db')
            df = pd.read_sql_query("""
                SELECT submission_id, document_type, confidence_score, risk_score, 
                       timestamp, status, appetite_data
                FROM submission_data 
                ORDER BY timestamp DESC 
                LIMIT 20
            """, conn)
            
            # Parse appetite decisions
            df['appetite_decision'] = df['appetite_data'].apply(
                lambda x: json.loads(x).get('decision', 'N/A') if x else 'N/A'
            )
            
            # Format timestamp
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
            
            conn.close()
            return df[['submission_id', 'document_type', 'confidence_score', 'risk_score', 
                      'appetite_decision', 'status', 'timestamp']]
        except:
            return pd.DataFrame()
    
    def start_engine(self, engine_name):
        """Start an engine process"""
        if engine_name not in self.running_processes or self.running_processes[engine_name].poll() is not None:
            try:
                process = subprocess.Popen(['python', f'engines/{engine_name}.py'])
                self.running_processes[engine_name] = process
                return True
            except Exception as e:
                print(f"Error starting {engine_name}: {e}")
                return False
        return False
    
    def stop_engine(self, engine_name):
        """Stop an engine process"""
        if engine_name in self.running_processes:
            try:
                self.running_processes[engine_name].terminate()
                self.running_processes[engine_name].wait(timeout=5)
                return True
            except:
                try:
                    self.running_processes[engine_name].kill()
                    return True
                except:
                    return False
        return False
    
    def setup_layout(self):
        """Setup the modern dashboard layout"""
        self.app.layout = dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H1([
                            html.I(className="bi bi-shield-check me-3", style={"color": "#0d6efd"}),
                            "Insurance AI Processing Platform"
                        ], className="text-center mb-0", style={"color": "#2c3e50", "font-weight": "600"}),
                        html.P("Intelligent Document Processing & Risk Assessment", 
                               className="text-center text-muted mb-4", style={"font-size": "1.1rem"})
                    ])
                ])
            ], className="mb-4"),
            
            # Auto-refresh interval
            dcc.Interval(
                id='interval-component',
                interval=3*1000,  # Update every 3 seconds
                n_intervals=0
            ),
            
            # Engine Control Panel
            dbc.Card([
                dbc.CardHeader([
                    html.H4([
                        html.I(className="bi bi-gear-fill me-2"),
                        "Engine Control Center"
                    ], className="mb-0")
                ]),
                dbc.CardBody([
                    html.Div(id="engine-controls", className="mb-3"),
                    dbc.ButtonGroup([
                        dbc.Button([
                            html.I(className="bi bi-play-fill me-2"),
                            "Start All Engines"
                        ], id="start-all-btn", color="success", size="lg"),
                        dbc.Button([
                            html.I(className="bi bi-stop-fill me-2"),
                            "Stop All Engines"
                        ], id="stop-all-btn", color="danger", size="lg", className="ms-2"),
                    ])
                ])
            ], className="mb-4", style={"border": "none", "box-shadow": "0 4px 6px rgba(0, 0, 0, 0.1)"}),
            
            # Statistics Cards
            html.Div(id="stats-cards", className="mb-4"),
            
            # File Upload Section
            dbc.Card([
                dbc.CardHeader([
                    html.H4([
                        html.I(className="bi bi-cloud-upload-fill me-2"),
                        "Document Upload Center"
                    ], className="mb-0")
                ]),
                dbc.CardBody([
                    dcc.Upload(
                        id='upload-data',
                        children=html.Div([
                            html.I(className="bi bi-file-earmark-pdf", style={"font-size": "3rem", "color": "#6c757d"}),
                            html.Br(),
                            html.H5("Drag & Drop or Click to Upload", className="mt-3 mb-2"),
                            html.P("Supports PDF, TXT, and Image files", className="text-muted"),
                            dbc.Badge("PDF Support Enabled", color="info", className="mt-2")
                        ], className="text-center"),
                        style={
                            'width': '100%',
                            'height': '200px',
                            'lineHeight': '200px',
                            'borderWidth': '2px',
                            'borderStyle': 'dashed',
                            'borderRadius': '15px',
                            'borderColor': '#dee2e6',
                            'textAlign': 'center',
                            'background': '#f8f9fa',
                            'transition': 'all 0.3s ease'
                        },
                        multiple=True
                    ),
                    html.Div(id='upload-status', className="mt-3")
                ])
            ], className="mb-4", style={"border": "none", "box-shadow": "0 4px 6px rgba(0, 0, 0, 0.1)"}),
            
            # Charts Row
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("Document Types", className="mb-0")),
                        dbc.CardBody([
                            dcc.Graph(id="document-types-chart", style={"height": "300px"})
                        ])
                    ], style={"border": "none", "box-shadow": "0 4px 6px rgba(0, 0, 0, 0.1)"})
                ], md=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("Risk Score Distribution", className="mb-0")),
                        dbc.CardBody([
                            dcc.Graph(id="risk-scores-chart", style={"height": "300px"})
                        ])
                    ], style={"border": "none", "box-shadow": "0 4px 6px rgba(0, 0, 0, 0.1)"})
                ], md=6),
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("Appetite Decisions", className="mb-0")),
                        dbc.CardBody([
                            dcc.Graph(id="appetite-decisions-chart", style={"height": "300px"})
                        ])
                    ], style={"border": "none", "box-shadow": "0 4px 6px rgba(0, 0, 0, 0.1)"})
                ], md=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("Processing Timeline", className="mb-0")),
                        dbc.CardBody([
                            dcc.Graph(id="processing-timeline-chart", style={"height": "300px"})
                        ])
                    ], style={"border": "none", "box-shadow": "0 4px 6px rgba(0, 0, 0, 0.1)"})
                ], md=6),
            ], className="mb-4"),
            
            # Recent Submissions Table
            dbc.Card([
                dbc.CardHeader([
                    html.H4([
                        html.I(className="bi bi-table me-2"),
                        "Recent Submissions"
                    ], className="mb-0")
                ]),
                dbc.CardBody([
                    html.Div(id="submissions-table")
                ])
            ], style={"border": "none", "box-shadow": "0 4px 6px rgba(0, 0, 0, 0.1)"})
            
        ], fluid=True, style={"background": "#f5f7fa", "min-height": "100vh", "padding": "20px"})
    
    def setup_callbacks(self):
        """Setup dashboard callbacks"""
        
        @self.app.callback(
            [Output('engine-controls', 'children'),
             Output('stats-cards', 'children'),
             Output('document-types-chart', 'figure'),
             Output('risk-scores-chart', 'figure'),
             Output('appetite-decisions-chart', 'figure'),
             Output('processing-timeline-chart', 'figure'),
             Output('submissions-table', 'children')],
            [Input('interval-component', 'n_intervals'),
             Input('start-all-btn', 'n_clicks'),
             Input('stop-all-btn', 'n_clicks')]
        )
        def update_dashboard(n_intervals, start_clicks, stop_clicks):
            ctx = callback_context
            
            # Handle engine control buttons
            if ctx.triggered:
                button_id = ctx.triggered[0]['prop_id'].split('.')[0]
                if button_id == 'start-all-btn' and start_clicks:
                    engines = ['file_listener', 'ocr_engine', 'classifier_engine', 
                              'data_extraction_engine', 'matching_rule_engine']
                    for engine in engines:
                        self.start_engine(engine)
                elif button_id == 'stop-all-btn' and stop_clicks:
                    for engine in list(self.running_processes.keys()):
                        self.stop_engine(engine)
            
            # Get current data
            engine_status = self.get_engine_status()
            stats = self.get_database_stats()
            recent_submissions = self.get_recent_submissions()
            
            # Engine Controls with modern design
            engine_controls = []
            for engine, is_running in engine_status.items():
                color = "success" if is_running else "secondary"
                icon = "bi-check-circle-fill" if is_running else "bi-x-circle-fill"
                
                engine_controls.append(
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    html.I(className=f"bi {icon} me-2", style={"font-size": "1.2rem"}),
                                    html.Span(engine.replace('_', ' ').title(), className="fw-bold")
                                ], className="d-flex align-items-center"),
                                dbc.Badge("Running" if is_running else "Stopped", 
                                         color=color, className="mt-2")
                            ], className="text-center")
                        ], color=color, outline=True, style={"height": "100px"})
                    ], md=2, className="mb-2")
                )
            
            engine_controls_layout = dbc.Row(engine_controls)
            
            # Stats Cards with modern design
            stats_cards = dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.I(className="bi bi-file-text-fill", 
                                      style={"font-size": "2.5rem", "color": "#0d6efd"}),
                                html.H2(stats.get('ocr_processed', 0), className="mt-2 mb-0"),
                                html.P("Documents Processed", className="text-muted mb-0")
                            ], className="text-center")
                        ])
                    ], style={"background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)", 
                             "color": "white", "border": "none"})
                ], md=2),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.I(className="bi bi-tags-fill", 
                                      style={"font-size": "2.5rem", "color": "#17a2b8"}),
                                html.H2(sum(stats.get('classifications', {}).values()), className="mt-2 mb-0"),
                                html.P("Documents Classified", className="text-muted mb-0")
                            ], className="text-center")
                        ])
                    ], style={"background": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)", 
                             "color": "white", "border": "none"})
                ], md=2),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.I(className="bi bi-check-circle-fill", 
                                      style={"font-size": "2.5rem", "color": "#28a745"}),
                                html.H2(len([d for d in stats.get('appetite_decisions', []) if d == 'accept']), 
                                       className="mt-2 mb-0"),
                                html.P("Accepted", className="text-muted mb-0")
                            ], className="text-center")
                        ])
                    ], style={"background": "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)", 
                             "color": "white", "border": "none"})
                ], md=2),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.I(className="bi bi-clock-fill", 
                                      style={"font-size": "2.5rem", "color": "#ffc107"}),
                                html.H2(len([d for d in stats.get('appetite_decisions', []) if d == 'review']), 
                                       className="mt-2 mb-0"),
                                html.P("Under Review", className="text-muted mb-0")
                            ], className="text-center")
                        ])
                    ], style={"background": "linear-gradient(135deg, #fa709a 0%, #fee140 100%)", 
                             "color": "white", "border": "none"})
                ], md=2),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.I(className="bi bi-x-circle-fill", 
                                      style={"font-size": "2.5rem", "color": "#dc3545"}),
                                html.H2(len([d for d in stats.get('appetite_decisions', []) if d == 'decline']), 
                                       className="mt-2 mb-0"),
                                html.P("Declined", className="text-muted mb-0")
                            ], className="text-center")
                        ])
                    ], style={"background": "linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)", 
                             "color": "white", "border": "none"})
                ], md=2),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.I(className="bi bi-graph-up", 
                                      style={"font-size": "2.5rem", "color": "#6f42c1"}),
                                html.H2(sum(stats.get('submissions', {}).values()), className="mt-2 mb-0"),
                                html.P("Total Submissions", className="text-muted mb-0")
                            ], className="text-center")
                        ])
                    ], style={"background": "linear-gradient(135deg, #d299c2 0%, #fef9d7 100%)", 
                             "color": "white", "border": "none"})
                ], md=2),
            ])
            
            # Charts with modern styling
            # Document Types Chart
            doc_types_data = stats.get('classifications', {})
            if doc_types_data:
                doc_types_fig = px.pie(
                    values=list(doc_types_data.values()),
                    names=list(doc_types_data.keys()),
                    title="Document Types Distribution",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                doc_types_fig.update_layout(
                    font=dict(size=12),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
            else:
                doc_types_fig = go.Figure().add_annotation(
                    text="No data available", 
                    showarrow=False,
                    font=dict(size=16, color="gray")
                )
            
            # Risk Scores Chart
            risk_scores = stats.get('risk_scores', [])
            if risk_scores:
                risk_scores_fig = px.histogram(
                    x=risk_scores,
                    title="Risk Scores Distribution",
                    nbins=10,
                    color_discrete_sequence=['#667eea']
                )
                risk_scores_fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
            else:
                risk_scores_fig = go.Figure().add_annotation(
                    text="No data available", 
                    showarrow=False,
                    font=dict(size=16, color="gray")
                )
            
            # Appetite Decisions Chart
            appetite_decisions = stats.get('appetite_decisions', [])
            if appetite_decisions:
                appetite_counts = pd.Series(appetite_decisions).value_counts()
                appetite_fig = px.bar(
                    x=appetite_counts.index,
                    y=appetite_counts.values,
                    title="Appetite Decisions",
                    color=appetite_counts.index,
                    color_discrete_map={'accept': '#28a745', 'review': '#ffc107', 'decline': '#dc3545'}
                )
                appetite_fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
            else:
                appetite_fig = go.Figure().add_annotation(
                    text="No data available", 
                    showarrow=False,
                    font=dict(size=16, color="gray")
                )
            
            # Processing Timeline Chart
            if not recent_submissions.empty:
                timeline_data = recent_submissions.groupby('timestamp').size().reset_index(name='count')
                timeline_fig = px.line(
                    timeline_data,
                    x='timestamp',
                    y='count',
                    title="Processing Timeline",
                    color_discrete_sequence=['#4facfe']
                )
                timeline_fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
            else:
                timeline_fig = go.Figure().add_annotation(
                    text="No data available", 
                    showarrow=False,
                    font=dict(size=16, color="gray")
                )
            
            # Submissions Table with modern styling
            if not recent_submissions.empty:
                submissions_table = dash_table.DataTable(
                    data=recent_submissions.to_dict('records'),
                    columns=[{'name': col.replace('_', ' ').title(), 'id': col} for col in recent_submissions.columns],
                    style_cell={
                        'textAlign': 'left',
                        'padding': '12px',
                        'fontFamily': 'Arial, sans-serif',
                        'fontSize': '14px'
                    },
                    style_header={
                        'backgroundColor': '#f8f9fa',
                        'fontWeight': 'bold',
                        'border': '1px solid #dee2e6'
                    },
                    style_data_conditional=[
                        {
                            'if': {'filter_query': '{appetite_decision} = accept'},
                            'backgroundColor': '#d1ecf1',
                            'color': 'black',
                        },
                        {
                            'if': {'filter_query': '{appetite_decision} = decline'},
                            'backgroundColor': '#f8d7da',
                            'color': 'black',
                        },
                        {
                            'if': {'filter_query': '{appetite_decision} = review'},
                            'backgroundColor': '#fff3cd',
                            'color': 'black',
                        }
                    ],
                    style_table={'overflowX': 'auto'},
                    page_size=10,
                    sort_action="native"
                )
            else:
                submissions_table = dbc.Alert(
                    "No submissions found. Upload a document to get started!",
                    color="info",
                    className="text-center"
                )
            
            return (engine_controls_layout, stats_cards, doc_types_fig, risk_scores_fig, 
                   appetite_fig, timeline_fig, submissions_table)
        
        @self.app.callback(
            Output('upload-status', 'children'),
            Input('upload-data', 'contents'),
            State('upload-data', 'filename'),
            prevent_initial_call=True
        )
        def handle_file_upload(list_of_contents, list_of_names):
            if list_of_contents is not None:
                upload_results = []
                
                # Handle single file or multiple files
                if not isinstance(list_of_contents, list):
                    list_of_contents = [list_of_contents]
                    list_of_names = [list_of_names]
                
                for contents, filename in zip(list_of_contents, list_of_names):
                    try:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                        
                        # Handle PDF files
                        if filename.lower().endswith('.pdf'):
                            text_content = self.extract_text_from_pdf(contents)
                            stored_filename = f"uploaded_pdf_{timestamp}.txt"
                            
                            with open(f"data/incoming/{stored_filename}", "w", encoding='utf-8') as f:
                                f.write(text_content)
                            
                            upload_results.append(
                                dbc.Alert([
                                    html.I(className="bi bi-check-circle-fill me-2"),
                                    f"PDF processed successfully: {filename} → {stored_filename}"
                                ], color="success", className="d-flex align-items-center")
                            )
                        
                        # Handle text and other files
                        else:
                            content_type, content_string = contents.split(',')
                            decoded = base64.b64decode(content_string)
                            
                            # Determine file extension
                            file_ext = filename.split('.')[-1] if '.' in filename else 'txt'
                            stored_filename = f"uploaded_{timestamp}.{file_ext}"
                            
                            with open(f"data/incoming/{stored_filename}", "wb") as f:
                                f.write(decoded)
                            
                            upload_results.append(
                                dbc.Alert([
                                    html.I(className="bi bi-check-circle-fill me-2"),
                                    f"File uploaded successfully: {filename} → {stored_filename}"
                                ], color="success", className="d-flex align-items-center")
                            )
                    
                    except Exception as e:
                        upload_results.append(
                            dbc.Alert([
                                html.I(className="bi bi-exclamation-triangle-fill me-2"),
                                f"Error uploading {filename}: {str(e)}"
                            ], color="danger", className="d-flex align-items-center")
                        )
                
                # Add processing info
                upload_results.append(
                    dbc.Alert([
                        html.I(className="bi bi-info-circle-fill me-2"),
                        "Files will be automatically processed by the AI engines. Check the dashboard for real-time updates!"
                    ], color="info", className="d-flex align-items-center mt-2")
                )
                
                return html.Div(upload_results)
            
            return ""
    
    def run(self, debug=True, host='0.0.0.0', port=8050):
        """Run the dashboard"""
        def signal_handler(sig, frame):
            print("\nStopping all engines...")
            for engine in list(self.running_processes.keys()):
                self.stop_engine(engine)
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        print(f"🚀 Starting Modern Insurance AI Dashboard at http://{host}:{port}")
        print("✨ Features: PDF Support, Modern UI, Real-time Processing")
        print("🛑 Use Ctrl+C to stop all engines and exit")
        
        self.app.run_server(debug=debug, host=host, port=port)

if __name__ == '__main__':
    dashboard = ModernInsuranceAIDashboard()
    dashboard.run()