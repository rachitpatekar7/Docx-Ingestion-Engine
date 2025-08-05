# report_builder.py

class ReportBuilder:
    def __init__(self, data):
        self.data = data

    def generate_summary(self):
        # Logic to generate a summary report from the data
        summary = {
            "total_records": len(self.data),
            "fields": list(self.data[0].keys()) if self.data else [],
        }
        return summary

    def generate_detailed_report(self):
        # Logic to generate a detailed report from the data
        detailed_report = []
        for record in self.data:
            detailed_report.append(record)
        return detailed_report

    def save_report(self, report, file_path):
        # Logic to save the report to a file
        with open(file_path, 'w') as file:
            for line in report:
                file.write(f"{line}\n")

    def build_report(self, report_type='summary', file_path='report.txt'):
        if report_type == 'summary':
            report = self.generate_summary()
        else:
            report = self.generate_detailed_report()

        self.save_report(report, file_path)