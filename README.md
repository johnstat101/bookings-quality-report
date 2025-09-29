# Bookings Quality Report

## Overview
The Bookings Quality Report is a comprehensive web application designed to monitor, analyze, and improve the quality of airline bookings. By processing Passenger Name Record (PNR) data from SBR files, it provides an interactive dashboard with deep insights into data completeness and accuracy. The ultimate goal is to ensure all PNRs contain the necessary elements for enhanced customer service, automated communication, and operational efficiency.

## Data Source
- **SBR (Standard Booking Record) File**: The application ingests booking data from CSV or Excel files, typically extracted from the airline's data warehouse.
- **Manual Upload**: Users can upload SBR files directly through the web interface for immediate analysis.

## Objectives
- Ensure all bookings meet the desired quality standards.
- Enable better servicing of customers by monitoring booking completeness and accuracy.
- Identify and highlight agents, offices, and delivery systems with poor data collection practices.
- Provide actionable data to support training initiatives and process improvements.
- Reduce issues that hinder automated passenger communication (e.g., pre-flight notifications, disruption handling).

## Key Features

### Interactive Dashboard & Reporting
- **Centralized Overview**: Key metrics at a glance, including total PNRs, average quality score, and the number of reachable vs. unreachable bookings.
- **Tabbed Navigation**: Easy access to different analysis sections: Overview, Delivery Systems, Elements, Offices, Quality, and Export.
- **Dynamic Filtering**:
    - **Booking Date Range**: Filter PNRs by their creation date.
    - **Delivery System**: Multi-select filter for booking systems (e.g., Amadeus, Galileo, KQ Website).
    - **Office ID**: Multi-select filter for specific booking offices, with a search functionality.
- **Theme Customization**: Multiple UI themes (including a dark mode) for personalized user experience.

### Data Validation & Quality Scoring
A sophisticated quality score (0-100%) is calculated for each PNR based on the presence and validity of key elements:
- **Contact Details (40%)**: Validates the presence of a correctly formatted phone number or email address in the appropriate fields.
- **Frequent Flyer Number (20%)**: Checks for the presence of an FF#.
- **Meal Selection (20%)**: Checks for a meal code.
- **Seat Assignment (20%)**: Checks for a seat assignment.

The system also identifies specific data quality issues:
- **Missing Contacts**: PNRs with no phone or email.
- **Wrongly Placed Contacts**: Detects when an email address is placed in a phone-only field (`CTCM`) or a phone number is in an email-only field (`CTCE`). Generic fields (`AP`, `APE`, `APM`) are excluded from misplacement detection.
- **Incorrect Format**: Flags contacts that do not match standard email or phone number patterns.
- **Advanced Email Support**: Recognizes '//' as alternative to '@' and './' as replacement for '-' in email addresses (e.g., `SG./OFFICE//AFRAA.ORG` equals `SG-OFFICE@AFRAA.ORG`).

### In-Depth Performance Analysis
- **Delivery System Performance**: Compares the average quality score and booking volume across different delivery systems (e.g., GDS, Web).
- **Office Performance**: A sortable heatmap table ranks booking offices by average quality score and volume, highlighting top performers and those needing improvement.
- **Missing Elements Analysis**: Doughnut charts visualize the completion rate for each key data element (Email, Phone, FF#, Meal, Seat).
- **Quality Score Distribution**: A histogram shows the distribution of PNRs across different quality score ranges (e.g., Critical, Poor, Good, Excellent).
- **Quality Score Trend**: A line chart displays the evolution of the average quality score over time (last 7, 30, or 90 days), reflecting the impact of improvement efforts.

### Data Management
- **File Upload**: A user-friendly drag-and-drop interface for uploading SBR data in `.csv`, `.xlsx`, or `.xls` format. The system clears old data upon a new upload to ensure a fresh analysis.
- **Interactive Data Export**: Click on any dashboard metric card to open a detailed modal view with:
    - Filterable data table with search functionality
    - Real-time filtering by office ID and delivery system
    - Export to Excel button for currently visible/filtered data
    - Duplicate removal based on PNR and contact detail combinations
- **Bulk Export Options**: Traditional export functionality for complete datasets including all data, no contacts, low-quality, and high-quality PNRs.

### Intelligent Data Parsing
- **Flexible Date Formats**: Automatically parses booking creation dates from common SBR formats like `ddmmyy` and `dmmyy`.
- **Advanced Contact Validation**: Sophisticated regex patterns identify emails and phones with airline industry-specific formats:
    - Supports prefixes like `KQ/M+`, `KQ/E+` and suffixes like `/EN`, `/FR`
    - Recognizes `//` as email separator (alternative to `@`)
    - Handles `./ ` as replacement for `-` in both username and domain parts
    - Validates contact placement in appropriate fields (CTCE for emails, CTCM for phones)
- **Robust Data Processing**: Bulk database operations with deduplication logic for passengers and contacts, ensuring efficient processing of large SBR files.
- **Multiple Passenger Support**: Handles PNRs with multiple passengers, tracking individual passenger details and quality metrics separately.

## Benefits
- Improves booking data quality for enhanced customer communication.
- Identifies training needs and process gaps for booking agents and offices.
- Supports data-driven decision-making for operational improvements.
- Provides a single source of truth for booking quality metrics across the organization.

## User Stories

*   **As a Revenue Management Analyst,** I want to see the overall booking quality score and how it trends over time, so I can report on our data-driven initiatives to senior management.
*   **As a Contact Center Manager,** I want to filter PNRs by my office ID and identify agents who frequently create bookings with missing or incorrect contact details, so I can provide targeted training.
*   **As a Digital Channels Manager,** I want to compare the data quality from our Website and Mobile App channels against GDS channels, so I can ensure our direct channels are performing optimally.
*   **As a Data Analyst,** I want to export a list of all low-quality PNRs from a specific delivery system, so I can perform a root-cause analysis on the data entry errors.
*   **As an Operations Manager,** I want to quickly upload the latest weekly SBR file and see an immediate breakdown of data quality, so I can monitor our network's performance without delay.

## Getting Started
1.  **Retrieve Data**: Obtain the SBR data file (CSV/Excel) from the airline data warehouse.
2.  **Upload Data**: Navigate to the "Upload" section of the application and upload the file.
3.  **Analyze**: Once processing is complete, navigate back to the dashboard.
4.  **Filter & Explore**: Use the filters and tabs to drill down into the data and gain insights.
5.  **Detailed Analysis**: Click on any metric card to open a modal with detailed PNR data, filterable by office and delivery system.
6.  **Export**: Use the modal export button for filtered data or bulk export options for complete datasets.

---