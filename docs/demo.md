# ADAS Diagnostics Co-pilot Demo

This document provides sample questions and use cases to demonstrate the capabilities of the ADAS Diagnostics Co-pilot.

## Getting Started

Once you have the application running at http://localhost:8501, you can try these sample questions to explore the system's capabilities.

## Sample Questions by Category

### 1. Mercedes E-Class ADAS Camera System

**Camera System Specifications:**
- "What are the specifications of the Continental MFC431 camera in the E-Class?"
- "What is the field of view and detection range of the ADAS camera?"
- "What processor is used in the Image Processing Unit?"

**Camera Calibration:**
- "What are the requirements for static calibration of the ADAS camera?"
- "How long does dynamic calibration take and what conditions are needed?"
- "What distance should the calibration target be placed at?"

**Lane Detection:**
- "What types of lane markings can the system detect?"
- "What is the minimum width for lane marking detection?"
- "At what speed does Lane Keeping Assist activate?"

### 2. Diagnostic Trouble Codes (Real DTCs from Sample Data)

**Camera System DTCs:**
- "What does DTC B1A00 mean and how do I diagnose it?"
- "I'm getting B1A01 - what should I check for camera lens obstruction?"
- "How do I resolve B1A02 camera calibration required error?"

**Engine System DTCs:**
- "What causes P0300 random misfire in the M264 engine?"
- "How do I diagnose P0171 system too lean on Bank 1?"
- "What are the symptoms of P0234 turbocharger overboost condition?"

**Brake System DTCs:**
- "What does P0571 brake switch circuit malfunction indicate?"
- "How do I diagnose C1201 ABS control module internal fault?"
- "What causes P0572 brake switch circuit low?"

**Transmission DTCs:**
- "What does P0700 transmission control system malfunction mean?"
- "How do I test the input speed sensor for P0715?"
- "What causes P0730 incorrect gear ratio in the 9G-TRONIC?"

### 3. OTA Updates and Software (Based on Sample Data)

**ADAS Camera Updates:**
- "What improvements were made in camera software version V2.1.0?"
- "How long does an ADAS camera module update take?"
- "What are the prerequisites for updating the camera software?"

**OTA System Troubleshooting:**
- "What does U3000 OTA update communication error mean?"
- "How do I resolve U3001 update installation failed?"
- "What causes U3002 update authentication failed?"

**Update Categories:**
- "What are critical safety updates and can they be deferred?"
- "How long can I postpone feature enhancement updates?"
- "What happens during a recall campaign update?"

### 4. Component and Part Analysis (Actual Part Numbers)

**Mercedes E-Class Specific Parts:**
- "What are the specifications for part number A213-905-01-00?"
- "Tell me about the Bosch ESP 9.3 brake control module A213-545-00-32"
- "What is the capacity and type of brake fluid for the E-Class?"

**Engine Components:**
- "What are the specifications of the M264 2.0L turbocharged engine?"
- "What is the part number for the Mass Airflow Sensor?"
- "What type of spark plugs does the E-Class use and what's the gap?"

**Transmission Components:**
- "What are the gear ratios for the 9G-TRONIC transmission?"
- "What type of transmission fluid does the 9G-TRONIC use?"
- "What is the torque specification for the transmission case bolts?"

### 5. Mercedes E-Class Specific Systems (VIN Pattern: WDD213*)

**DISTRONIC PLUS & Active Lane Keeping:**
- "How does DISTRONIC PLUS adaptive cruise control work in the E-Class?"
- "What is the steering torque range for Lane Keeping Assist?"
- "At what speeds does the Forward Collision Warning activate?"

**Automatic Emergency Braking:**
- "What is the maximum deceleration for AEB in the E-Class?"
- "What types of objects can the AEB system detect?"
- "What are the warning stages before automatic braking?"

**9G-TRONIC Transmission:**
- "How does the 9G-TRONIC transmission integrate with ADAS systems?"
- "What is the difference between Eco Mode and Sport Mode shifting?"
- "How does the predictive shifting feature work?"

### 6. Real-World Diagnostic Scenarios

**Camera System Issues:**
- "The ADAS camera shows 'lens obstruction detected' but the windshield is clean. What should I check?"
- "After windshield replacement, the camera needs calibration. What's the complete procedure?"
- "The Lane Keeping Assist isn't activating above 65 km/h. What could be wrong?"

**Brake System Problems:**
- "The brake lights aren't working and cruise control is disabled. What DTC should I expect?"
- "I have a spongy brake pedal on an E-Class. What are the diagnostic steps?"
- "The ABS warning light is on and there's no traction control. What should I check first?"

**Engine Performance Issues:**
- "The E350 has rough idle and reduced power. What are the most likely causes?"
- "I'm getting a lean condition code P0171. What's the diagnostic procedure?"
- "The turbocharger is making unusual noise and there's black smoke. What should I check?"

**Transmission Problems:**
- "The 9G-TRONIC is showing harsh shifts. What pressure tests should I perform?"
- "There's no torque converter lockup. How do I diagnose the input speed sensor?"
- "The transmission is overheating. What should I check in the cooling system?"

### 7. OTA Update Scenarios

**Update Failures:**
- "An OTA update failed during installation. How do I recover the system?"
- "The vehicle shows 'update authentication failed'. What does this mean?"
- "After an OTA update, multiple ECUs are showing communication errors. What's the procedure?"

**Update Planning:**
- "What network requirements are needed for large infotainment updates?"
- "How do I schedule OTA updates for optimal conditions?"
- "What happens if the vehicle loses power during an update?"

### 8. Maintenance Procedures (Based on Sample Data)

**ADAS Camera Maintenance:**
- "What are the monthly inspection requirements for the ADAS camera?"
- "How do I clean the camera lens properly?"
- "What environmental conditions affect camera performance?"

**Brake System Maintenance:**
- "What is the brake fluid replacement interval for E-Class with ADAS?"
- "How do I perform the brake bleeding procedure with scan tool?"
- "What are the minimum brake pad thicknesses for standard and AMG models?"

**Engine Maintenance:**
- "What type of oil does the M264 engine require and what's the capacity?"
- "What is the spark plug replacement interval and torque specification?"
- "How often should the air filter be replaced in severe duty conditions?"

**Transmission Maintenance:**
- "What is the fluid capacity for the 9G-TRONIC transmission?"
- "How do I check transmission fluid level properly?"
- "What's the procedure for resetting transmission adaptations?"

## Advanced Usage Tips

### 1. Follow-up Questions
The system maintains conversation context, so you can ask follow-up questions:
- Initial: "What does DTC B1A00 mean?"
- Follow-up: "How do I check CAN bus communication for this error?"
- Follow-up: "What tools do I need to test the camera module connections?"

### 2. Specific Context (Use Real Data)
Provide specific details for more targeted responses:
- "2023 Mercedes E-Class with VIN WDD213 showing DTC B1A02 after windshield replacement"
- "M264 engine with P0300 misfire after 60,000 miles"
- "9G-TRONIC transmission with P0715 input speed sensor error"

### 3. Multi-Step Diagnostics
Ask for step-by-step procedures using actual procedures from the data:
- "Give me the complete static calibration procedure for the Continental MFC431 camera"
- "Walk me through diagnosing P0171 system too lean on the M264 engine"
- "What's the step-by-step brake fluid replacement procedure for E-Class?"

### 4. Component Relationships
Explore system interconnections using real part numbers and systems:
- "How does the A213-905-01-00 camera module communicate with the brake system?"
- "What other systems are affected when the Bosch ESP 9.3 control module fails?"
- "How does the 9G-TRONIC transmission coordinate with the M264 engine management?"

### 5. Technical Specifications
Ask for detailed technical information:
- "What are the torque specifications for the ADAS camera mounting bracket?"
- "What is the operating pressure range for the 9G-TRONIC hydraulic system?"
- "What are the environmental specifications for the camera module storage?"

## Expected Responses

The system will provide:
- **Detailed explanations** based on Mercedes E-Class technical manuals
- **Diagnostic procedures** with actual DTC codes and step-by-step instructions
- **Component specifications** with real part numbers and suppliers
- **Technical parameters** like torque specs, pressures, and tolerances
- **Tool usage transparency** showing which documents were searched
- **Source references** from the ingested technical manuals

### Sample Response Examples

**For DTC Questions:**
- Specific symptoms, diagnostic steps, and repair procedures
- Related component information and part numbers
- Prerequisites and safety warnings

**For Component Questions:**
- Technical specifications, operating parameters
- Installation procedures and torque specifications
- Supplier information and compatibility details

**For Maintenance Questions:**
- Service intervals, fluid specifications
- Step-by-step procedures with tool requirements
- Safety precautions and environmental conditions

## System Capabilities

With the current sample data, the system can answer questions about:
- ✅ Mercedes E-Class ADAS camera system (Continental MFC431)
- ✅ Brake system with ESP 9.3 and AEB integration
- ✅ M264 2.0L turbocharged engine diagnostics
- ✅ 9G-TRONIC transmission control and maintenance
- ✅ OTA update procedures and troubleshooting
- ✅ Specific DTCs: B1A00, B1A01, B1A02, P0300, P0171, P0234, P0571, P0572, C1201, P0700, P0715, P0730, U3000, U3001, U3002
- ✅ Real part numbers and specifications
- ✅ Maintenance procedures and intervals

## Quick Test Questions

Try these questions to verify the system is working with the sample data:

### Basic Functionality Test
1. "What is the part number for the ADAS camera in the Mercedes E-Class?"
   - Expected: A213-905-01-00 (Stereo Camera Unit)

2. "What does DTC B1A00 mean?"
   - Expected: Camera Module Communication Error with diagnostic steps

3. "What type of transmission fluid does the 9G-TRONIC use?"
   - Expected: ZF LifeGuard Fluid 8

### Advanced Functionality Test
4. "What are the gear ratios for the 9G-TRONIC transmission?"
   - Expected: Complete list from 1st gear (5.250:1) to 9th gear (0.600:1)

5. "How do I diagnose P0300 random misfire in the M264 engine?"
   - Expected: Step-by-step diagnostic procedure with specific checks

6. "What are the prerequisites for OTA updates to the ADAS camera module?"
   - Expected: Vehicle stationary, clear weather, specific time requirements

## Getting Help

If you encounter issues or need assistance:
1. Check the system status indicators in the Streamlit interface
2. Review the tool usage section to understand how queries were processed
3. Try the quick test questions above to verify system functionality
4. Refer to the README.md for setup and configuration help
5. Ensure the sample data has been ingested using `task ingest:sample`

## Contributing

To improve the system's knowledge base:
1. Add relevant automotive documents to the `data/sample-data/` directory
2. Run `task ingest:sample` to process new documents
3. Test queries related to the new content using specific questions
4. Share feedback on system performance and accuracy

### Adding New Documents
When adding new documents, include:
- Technical specifications with part numbers
- Diagnostic procedures with actual DTC codes
- Maintenance intervals and procedures
- Component relationships and dependencies
- Safety warnings and precautions
