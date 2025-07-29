# ADAS Diagnostics Co-pilot Demo

This document provides sample questions and use cases to demonstrate the capabilities of the ADAS Diagnostics Co-pilot.

## Getting Started

Once you have the application running at http://localhost:8501, you can try these sample questions to explore the system's capabilities.

## Sample Questions by Category

### 1. General ADAS System Queries

**Basic System Information:**
- "What are the main components of an ADAS camera system?"
- "Explain how the brake system works in modern vehicles"
- "What is the role of the transmission control module?"

**System Integration:**
- "How do ADAS cameras interact with the brake system?"
- "What are the dependencies between the engine control unit and transmission?"
- "Describe the communication protocols used in ADAS systems"

### 2. Diagnostic Trouble Codes (DTC)

**DTC Analysis:**
- "What does DTC code B1234 mean?"
- "How do I diagnose a P0171 error code?"
- "What are the common causes of transmission-related DTCs?"

**DTC Troubleshooting:**
- "I'm seeing multiple DTCs related to the camera system. What should I check first?"
- "The vehicle has intermittent brake system warnings. What diagnostic steps should I follow?"

### 3. OTA Updates and Software Issues

**Update Correlation:**
- "Are there any known issues with OTA update version 2.1.0?"
- "What changes were made in the latest software release?"
- "How can I check if a recent update caused system failures?"

**Version Management:**
- "What's the difference between software versions 1.5.2 and 1.6.0?"
- "Which vehicles are affected by the camera calibration update?"

### 4. Component and Part Analysis

**Part Identification:**
- "What are the specifications for Mercedes part number A213-123-45-67?"
- "Which supplier provides the radar sensors for E-Class vehicles?"
- "What's the replacement procedure for a faulty camera module?"

**Compatibility:**
- "Are brake components from 2020 E-Class compatible with 2022 models?"
- "What parts need to be replaced when upgrading the ADAS system?"

### 5. Vehicle-Specific Queries (Mercedes E-Class)

**VIN-Based Analysis:**
- "Show me the service history for VIN WDD213..."
- "What ADAS features are available on this specific E-Class model?"
- "Has this vehicle received all required software updates?"

**Model-Specific Issues:**
- "What are common ADAS issues in 2021 Mercedes E-Class vehicles?"
- "Are there any recalls affecting E-Class brake systems?"

### 6. Timeline and Historical Analysis

**Event Correlation:**
- "Show me all events related to camera system failures in the last 6 months"
- "What happened before the brake system started showing warnings?"
- "Timeline of software updates for this vehicle model"

**Pattern Recognition:**
- "Are there patterns in ADAS failures after specific updates?"
- "Which components fail most frequently after 50,000 miles?"

### 7. Complex Diagnostic Scenarios

**Multi-System Issues:**
- "The vehicle has intermittent ADAS warnings, reduced braking performance, and transmission hesitation. What could be the root cause?"
- "After the latest OTA update, multiple systems are showing errors. How should I approach this diagnosis?"

**Intermittent Problems:**
- "How do I diagnose an intermittent camera calibration issue?"
- "The brake assist randomly deactivates. What diagnostic procedure should I follow?"

**Environmental Factors:**
- "Could weather conditions affect ADAS camera performance?"
- "What impact does temperature have on brake system operation?"

### 8. Maintenance and Procedures

**Calibration:**
- "What's the procedure for calibrating ADAS cameras after windshield replacement?"
- "How do I perform a brake system calibration?"

**Preventive Maintenance:**
- "What are the recommended maintenance intervals for ADAS components?"
- "How often should brake fluid be replaced in vehicles with advanced brake assist?"

## Advanced Usage Tips

### 1. Follow-up Questions
The system maintains conversation context, so you can ask follow-up questions:
- Initial: "What causes brake system warnings?"
- Follow-up: "How do I test the brake pressure sensor?"
- Follow-up: "What tools do I need for this test?"

### 2. Specific Context
Provide specific details for more targeted responses:
- "2022 Mercedes E-Class with VIN WDD213... showing DTC B1234 after OTA update 2.1.0"

### 3. Multi-Step Diagnostics
Ask for step-by-step procedures:
- "Give me a step-by-step diagnostic procedure for intermittent ADAS camera failures"

### 4. Component Relationships
Explore system interconnections:
- "Show me how the radar sensor connects to the brake system"
- "What other components are affected when the camera module fails?"

## Expected Responses

The system will provide:
- **Detailed explanations** of automotive systems and components
- **Diagnostic procedures** with step-by-step instructions
- **Component relationships** and system dependencies
- **Historical context** when databases are configured
- **Tool usage transparency** showing which search methods were used
- **Source references** when available

## Limitations

In basic mode (without databases):
- No access to historical data or specific vehicle records
- Limited to general automotive knowledge
- Cannot perform timeline analysis or pattern recognition

With full database setup:
- Access to ingested documents and knowledge graphs
- Vehicle-specific analysis capabilities
- Timeline and relationship analysis

## Getting Help

If you encounter issues or need assistance:
1. Check the system status indicators in the Streamlit interface
2. Review the tool usage section to understand how queries were processed
3. Try rephrasing questions for better results
4. Refer to the README.md for setup and configuration help

## Contributing

To improve the system's knowledge base:
1. Add relevant automotive documents to the `data/sample-data/` directory
2. Run the ingestion pipeline to process new documents
3. Test queries related to the new content
4. Share feedback on system performance and accuracy
