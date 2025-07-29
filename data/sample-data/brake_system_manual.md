# Mercedes-Benz E-Class Brake System Service Manual
## Model Year: 2023-2024 | VIN Pattern: WDD213*

### System Overview
The Mercedes-Benz E-Class Advanced Driver Assistance System (ADAS) integrated brake system combines traditional hydraulic braking with electronic brake-by-wire technology. This system provides enhanced safety through automatic emergency braking (AEB), DISTRONIC PLUS adaptive cruise control, and Active Brake Assist integration.

### Component Specifications

#### Mercedes-Benz E-Class Brake Control Module (BCM)
- **Part Number**: A213-545-00-32 (ESP/ABS Control Unit)
- **Supplier**: Bosch ESP 9.3
- **Software Version**: ME9.7.1
- **CAN Bus Address**: 0x7E0
- **Mercedes Star Diagnosis Code**: N47/5

#### Master Cylinder Assembly
- **Bore Diameter**: 25.4mm (E350), 27.0mm (E63 AMG)
- **Reservoir Capacity**: 1.2L
- **Operating Pressure**: 180 bar max
- **Brake Fluid Type**: MB 331.0 (DOT 4+)

#### Mercedes-Benz E-Class Brake Pads (Front)
- **Material**: Ceramic composite (AMG Performance pads available)
- **Thickness (New)**: 15mm (E350), 17mm (E63 AMG)
- **Minimum Thickness**: 3mm
- **Part Number**: A213-420-12-20 (Standard), A213-420-15-20 (AMG)
- **Replacement Interval**: 40,000-60,000 miles

#### Mercedes-Benz E-Class Brake Rotors (Front)
- **Diameter**: 330mm (E350), 360mm (E63 AMG)
- **Thickness (New)**: 32mm (E350), 36mm (E63 AMG)
- **Minimum Thickness**: 30mm (E350), 34mm (E63 AMG)
- **Part Number**: A213-421-01-12 (Standard), A213-421-05-12 (AMG)
- **Runout Tolerance**: 0.05mm

### Diagnostic Trouble Codes (DTCs)

#### P0571 - Brake Switch Circuit Malfunction
**Symptoms**: 
- Brake lights not functioning
- Cruise control disabled
- AEB system fault

**Diagnosis**:
1. Check brake switch continuity
2. Verify 12V supply to switch
3. Inspect wiring harness for damage

**Repair**: Replace brake switch assembly (Part: SW-BRK-2024-001)

#### P0572 - Brake Switch Circuit Low
**Symptoms**:
- Intermittent brake light operation
- ADAS warning messages

**Diagnosis**:
1. Measure voltage at BCM connector pin 15
2. Check ground circuit integrity
3. Perform brake switch calibration

#### C1201 - ABS Control Module Internal Fault
**Symptoms**:
- ABS warning light illuminated
- Loss of traction control
- Reduced braking assistance

**Diagnosis**:
1. Scan for additional codes
2. Check wheel speed sensor signals
3. Verify hydraulic pump operation

**Repair**: Replace ABS control module and perform system relearn

### Maintenance Procedures

#### Brake Fluid Replacement
**Interval**: 24 months or 30,000 miles
**Procedure**:
1. Connect scan tool and enter brake service mode
2. Bleed system starting from RR, LR, RF, LF
3. Monitor fluid level and color
4. Perform brake pedal feel test
5. Clear service indicators

#### Brake Pad Inspection
**Interval**: Every 12,000 miles
**Procedure**:
1. Remove wheels and inspect pad thickness
2. Check for uneven wear patterns
3. Measure rotor thickness and runout
4. Inspect caliper operation
5. Document findings in service record

### ADAS Integration Points

#### Emergency Brake Assist (EBA)
- Activates when collision imminent (< 1.5 seconds)
- Maximum deceleration: 8 m/s²
- Requires functional radar and camera systems

#### Adaptive Cruise Control (ACC)
- Maintains following distance 1.5-3.0 seconds
- Speed range: 30-180 km/h
- Integrates with brake and throttle systems

### Troubleshooting Guide

#### Symptom: Spongy Brake Pedal
**Possible Causes**:
- Air in brake lines
- Brake fluid contamination
- Master cylinder internal leak
- Brake booster malfunction

**Diagnostic Steps**:
1. Check brake fluid level and condition
2. Perform brake system pressure test
3. Inspect for external leaks
4. Test brake booster vacuum

#### Symptom: Brake Noise
**Possible Causes**:
- Worn brake pads
- Glazed rotors
- Contaminated friction surfaces
- Loose caliper hardware

**Diagnostic Steps**:
1. Visual inspection of brake components
2. Measure pad and rotor thickness
3. Check for proper lubrication
4. Verify torque specifications

### Safety Warnings
⚠️ **CRITICAL**: Always use proper jack stands when working under vehicle
⚠️ **CRITICAL**: Brake fluid is corrosive - avoid contact with painted surfaces
⚠️ **CRITICAL**: System must be bled after any hydraulic component replacement

### Technical Specifications
- **System Pressure**: 180 bar maximum
- **Fluid Capacity**: 1.2L total system
- **Operating Temperature**: -40°C to +120°C
- **Response Time**: < 150ms for emergency braking
