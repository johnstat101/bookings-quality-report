# Bookings Quality Report

## Overview
Bookings Quality Report is a project designed to monitor and improve the quality of airline bookings. The goal is to ensure that all Passenger Name Records (PNRs) contain the necessary booking elements for better customer service across all touchpoints.

## Data Source
- Retrieves booking data from the SBR file in the airline data warehouse.

## Objectives
- Ensure all bookings meet the desired quality standards.
- Enable better servicing of customers by monitoring booking completeness and accuracy.

## Key Features

### PNR Quality Monitoring
Checks each PNR for the following essential elements:
- Phone number
- Email address
- Frequent Flyer Number (FF#)
- Meal selection
- Seat assignment

### Performance Analysis
- By booking channel (own office, web, mobile app, travel agency, NDC)
- By booking office ID
- By Travel Agency IATA code (and agency name, if available)
- By Staff ID (and staff name, if available)

### Quality Metrics
- Percentage of PNRs missing required elements
- Percentage of PNRs with incorrect formats
- Booking quality score by PNR, office ID, channel, and staff ID

### Dashboard & Reporting
- Interactive dashboard in the portal to display statistics
- Highlights agents, offices, and channels with poor data collection or incorrect details
- Identifies issues that hinder automated communication with passengers

## Benefits
- Improves booking data quality for enhanced customer communication.
- Identifies training needs and process gaps for booking agents and offices.
- Supports data-driven decision-making for operational improvements.

## Getting Started
1. Connect to the airline data warehouse and retrieve the SBR file.
2. Run the quality checks and generate performance metrics.
3. View results and insights on the dashboard.

---